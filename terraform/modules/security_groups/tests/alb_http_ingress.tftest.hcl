# Unit tests for the security_groups module, focused on the ALB security
# group's HTTP ingress rule, which is the behavior introduced/changed in
# this PR (restricting port 80 to configurable CIDR blocks instead of
# allowing 0.0.0.0/0 and ::/0 unconditionally).
#
# These tests use a mocked "aws" provider so they run entirely locally
# (no AWS credentials or network access required) and only exercise the
# `plan` phase, since we only care about the configuration that would be
# submitted to AWS, not real provider behavior.
#
# NOTE: `ingress` on aws_security_group is a set of objects, and its
# nested `cidr_blocks`/`ipv6_cidr_blocks` attributes are lists. Comparing
# those values against HCL list literals with `==` can spuriously fail
# because a literal (`["a", "b"]`) is a *tuple*, not a *list*, and cty
# treats those as different types for equality purposes. `jsonencode()`
# is used on both sides of such comparisons to avoid that pitfall.

mock_provider "aws" {}

variables {
  vpc_id      = "vpc-0123456789abcdef0"
  environment = "test"
}

# Baseline: with no overrides, the module must fall back to its documented
# defaults (VPC CIDR for IPv4, no IPv6) and must not have regressed the
# untouched HTTPS ingress rule or the total ingress rule count.
run "http_ingress_defaults_to_vpc_cidr_only" {
  command = plan

  assert {
    condition     = jsonencode(var.http_ingress_cidr_blocks) == jsonencode(["10.0.0.0/16"])
    error_message = "Default http_ingress_cidr_blocks must remain the internal VPC CIDR (10.0.0.0/16)"
  }

  assert {
    condition     = length(var.http_ingress_ipv6_cidr_blocks) == 0
    error_message = "Default http_ingress_ipv6_cidr_blocks must remain empty"
  }

  assert {
    condition = anytrue([
      for rule in aws_security_group.alb_sg.ingress :
      rule.from_port == var.http_port &&
      rule.to_port == var.http_port &&
      rule.protocol == "tcp" &&
      jsonencode(rule.cidr_blocks) == jsonencode(["10.0.0.0/16"]) &&
      length(rule.ipv6_cidr_blocks) == 0
    ])
    error_message = "ALB HTTP ingress must be restricted to the VPC CIDR by default, with no IPv6 ranges"
  }

  assert {
    condition = anytrue([
      for rule in aws_security_group.alb_sg.ingress :
      rule.from_port == 443 &&
      rule.to_port == 443 &&
      rule.protocol == "tcp" &&
      jsonencode(rule.cidr_blocks) == jsonencode(["0.0.0.0/0"]) &&
      jsonencode(rule.ipv6_cidr_blocks) == jsonencode(["::/0"])
    ])
    error_message = "ALB HTTPS ingress on port 443 must remain open to the internet (unchanged by this PR)"
  }

  assert {
    condition     = length(aws_security_group.alb_sg.ingress) == 2
    error_message = "ALB security group must define exactly two ingress rules (HTTP + HTTPS)"
  }
}

# Custom IPv4/IPv6 CIDR blocks (e.g. office networks or a CloudFront
# managed prefix list resolved to CIDRs) must be applied verbatim to the
# HTTP ingress rule.
run "http_ingress_accepts_custom_cidr_blocks" {
  command = plan

  variables {
    http_ingress_cidr_blocks      = ["203.0.113.0/24", "198.51.100.0/24"]
    http_ingress_ipv6_cidr_blocks = ["2001:db8::/32"]
  }

  assert {
    condition = anytrue([
      for rule in aws_security_group.alb_sg.ingress :
      rule.from_port == var.http_port &&
      rule.to_port == var.http_port &&
      jsonencode(rule.cidr_blocks) == jsonencode(["203.0.113.0/24", "198.51.100.0/24"]) &&
      jsonencode(rule.ipv6_cidr_blocks) == jsonencode(["2001:db8::/32"])
    ])
    error_message = "ALB HTTP ingress must honor custom IPv4/IPv6 CIDR blocks passed via variables"
  }

  # The HTTPS rule must remain unaffected by HTTP-specific overrides.
  assert {
    condition = anytrue([
      for rule in aws_security_group.alb_sg.ingress :
      rule.from_port == 443 &&
      jsonencode(rule.cidr_blocks) == jsonencode(["0.0.0.0/0"]) &&
      jsonencode(rule.ipv6_cidr_blocks) == jsonencode(["::/0"])
    ])
    error_message = "ALB HTTPS ingress must remain open to the internet regardless of HTTP CIDR overrides"
  }
}

# Operators must still be able to explicitly reopen HTTP to the world by
# passing 0.0.0.0/0 and ::/0, preserving backward compatibility for anyone
# who deliberately wants the old, fully-open behavior.
run "http_ingress_can_be_reopened_to_the_internet" {
  command = plan

  variables {
    http_ingress_cidr_blocks      = ["0.0.0.0/0"]
    http_ingress_ipv6_cidr_blocks = ["::/0"]
  }

  assert {
    condition = anytrue([
      for rule in aws_security_group.alb_sg.ingress :
      rule.from_port == var.http_port &&
      jsonencode(rule.cidr_blocks) == jsonencode(["0.0.0.0/0"]) &&
      jsonencode(rule.ipv6_cidr_blocks) == jsonencode(["::/0"])
    ])
    error_message = "ALB HTTP ingress must still support fully open access when explicitly configured"
  }
}

# Edge case: an empty IPv4 list combined with an IPv6-only restriction
# must be accepted (e.g. an IPv6-only deployment).
run "http_ingress_supports_ipv6_only_restriction" {
  command = plan

  variables {
    http_ingress_cidr_blocks      = []
    http_ingress_ipv6_cidr_blocks = ["2001:db8::/32"]
  }

  assert {
    condition = anytrue([
      for rule in aws_security_group.alb_sg.ingress :
      rule.from_port == var.http_port &&
      length(rule.cidr_blocks) == 0 &&
      jsonencode(rule.ipv6_cidr_blocks) == jsonencode(["2001:db8::/32"])
    ])
    error_message = "ALB HTTP ingress must support an IPv6-only restriction when the IPv4 CIDR list is empty"
  }
}

# Edge case: both CIDR lists empty means no source can reach the HTTP
# port at all, which must plan successfully (an intentionally locked
# down configuration) rather than erroring out.
run "http_ingress_supports_fully_locked_down_configuration" {
  command = plan

  variables {
    http_ingress_cidr_blocks      = []
    http_ingress_ipv6_cidr_blocks = []
  }

  assert {
    condition = anytrue([
      for rule in aws_security_group.alb_sg.ingress :
      rule.from_port == var.http_port &&
      length(rule.cidr_blocks) == 0 &&
      length(rule.ipv6_cidr_blocks) == 0
    ])
    error_message = "ALB HTTP ingress must support being fully locked down (no IPv4 or IPv6 sources)"
  }
}

# The CIDR restriction must apply on whatever HTTP port is configured,
# not just the default port 80.
run "http_ingress_applies_cidr_restriction_on_custom_port" {
  command = plan

  variables {
    http_port                = 8080
    http_ingress_cidr_blocks = ["172.16.0.0/12"]
  }

  assert {
    condition = anytrue([
      for rule in aws_security_group.alb_sg.ingress :
      rule.from_port == 8080 &&
      rule.to_port == 8080 &&
      rule.protocol == "tcp" &&
      jsonencode(rule.cidr_blocks) == jsonencode(["172.16.0.0/12"])
    ])
    error_message = "ALB HTTP ingress must apply the CIDR restriction regardless of the configured http_port"
  }
}

# Multiple CIDR blocks (a common real-world case: several office/VPN
# networks) must all be preserved, not just the first entry.
run "http_ingress_preserves_multiple_cidr_blocks_in_order" {
  command = plan

  variables {
    http_ingress_cidr_blocks = ["10.0.0.0/16", "10.1.0.0/16", "10.2.0.0/16"]
  }

  assert {
    condition = anytrue([
      for rule in aws_security_group.alb_sg.ingress :
      rule.from_port == var.http_port &&
      length(rule.cidr_blocks) == 3 &&
      jsonencode(rule.cidr_blocks) == jsonencode(["10.0.0.0/16", "10.1.0.0/16", "10.2.0.0/16"])
    ])
    error_message = "ALB HTTP ingress must preserve every CIDR block supplied, in the order provided"
  }
}