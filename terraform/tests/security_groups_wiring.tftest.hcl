# Root-level regression test for the wiring introduced in this PR between
# the root module and the security_groups module: `main.tf` now passes
# `http_ingress_cidr_blocks = [var.vpc_cidr]` into `module.security_groups`.
#
# Every sibling module is overridden with mock outputs so that only
# `module.security_groups` actually plans real resources (the other
# modules have pre-existing validation on computed attributes, like ARN
# formats, that are unrelated to this change and would otherwise require
# unrelated mocking work to satisfy). This keeps the test focused on the
# `security_groups` module wiring while still exercising it through the
# real root `main.tf` module-call arguments (as opposed to the module's
# own isolated tests in terraform/modules/security_groups/tests/).
#
# We cannot assert on the security_groups module's internal resources
# from here (module internals are only exposed through their declared
# outputs), so this test acts as a regression guard for the wiring
# itself: it ensures the whole configuration still type-checks and plans
# successfully with `http_ingress_cidr_blocks = [var.vpc_cidr]` in place.
# If the wiring were changed to pass a bare string instead of a
# one-element list (e.g. `http_ingress_cidr_blocks = var.vpc_cidr`), the
# module's `list(string)` variable type would reject it and this test
# would fail with a type-conversion error during plan.

mock_provider "aws" {}

variables {
  db_password = "test-password-not-a-real-secret"
}

override_module {
  target = module.vpc
  outputs = {
    vpc_id                 = "vpc-mock0000000000000"
    public_subnet_ids      = ["subnet-mock0001", "subnet-mock0002"]
    private_app_subnet_ids = ["subnet-mock0003", "subnet-mock0004"]
    private_db_subnet_ids  = ["subnet-mock0005", "subnet-mock0006"]
  }
}

override_module {
  target = module.alb
  outputs = {
    alb_arn          = "arn:aws:elasticloadbalancing:ap-southeast-5:123456789012:loadbalancer/app/mock/0000000000000000"
    alb_dns_name     = "mock-alb-1234567890.ap-southeast-5.elb.amazonaws.com"
    alb_zone_id      = "Z2MOCKZONEID"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-5:123456789012:targetgroup/mock/0000000000000000"
  }
}

override_module {
  target = module.waf
  outputs = {
    web_acl_arn = "arn:aws:wafv2:ap-southeast-5:123456789012:regional/webacl/mock/00000000-0000-0000-0000-000000000000"
  }
}

override_module {
  target = module.asg
  outputs = {
    asg_name = "mock-asg"
  }
}

override_module {
  target = module.rds
  outputs = {
    db_instance_endpoint = "mock-db.abcdefghijkl.ap-southeast-5.rds.amazonaws.com:5432"
  }
}

override_module {
  target = module.standalone_ec2
  outputs = {
    instance_ids      = ["i-mock00000000000"]
    private_ips       = ["10.0.10.10"]
    security_group_id = "sg-mock000000000000000"
  }
}

override_module {
  target = module.jumphost
  outputs = {
    jumphost_public_ip  = "203.0.113.10"
    jumphost_private_ip = "10.0.1.10"
    security_group_id   = "sg-mock000000000000001"
  }
}

override_module {
  target = module.elasticache_valkey
  outputs = {
    primary_endpoint_address = "mock-valkey.abcdefghijkl.ap-southeast-5.cache.amazonaws.com"
    security_group_id        = "sg-mock000000000000002"
  }
}

override_module {
  target = module.route53
  outputs = {
    hosted_zone_id = "Z3MOCKHOSTEDZONE"
    name_servers   = ["ns-1.mock.awsdns.com"]
    fqdn           = "app.linuxmalaysia.com"
  }
}

run "root_plan_succeeds_with_default_vpc_cidr" {
  command = plan

  assert {
    condition     = var.vpc_cidr == "10.0.0.0/16"
    error_message = "Default vpc_cidr must remain 10.0.0.0/16"
  }

  assert {
    condition     = output.vpc_id == "vpc-mock0000000000000"
    error_message = "Root plan should complete successfully with module.security_groups wired to the (mocked) VPC id"
  }
}

run "root_plan_succeeds_with_custom_vpc_cidr" {
  command = plan

  variables {
    vpc_cidr = "172.16.0.0/12"
  }

  assert {
    condition     = var.vpc_cidr == "172.16.0.0/12"
    error_message = "Custom vpc_cidr must be honored by the plan"
  }

  assert {
    condition     = output.vpc_id == "vpc-mock0000000000000"
    error_message = "Root plan should still complete successfully when a custom vpc_cidr is supplied to module.security_groups.http_ingress_cidr_blocks"
  }
}