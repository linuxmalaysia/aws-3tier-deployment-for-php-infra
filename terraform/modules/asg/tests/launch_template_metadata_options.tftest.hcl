# Unit tests for the ASG module's launch template `metadata_options` block,
# which is the behavior introduced by this PR (enforcing IMDSv2 by requiring
# a session token and capping the hop limit to 1, instead of relying on the
# provider/API default of IMDSv1-and-v2-both-allowed with a hop limit of 2).
#
# These tests use a mocked "aws" provider so they run entirely locally (no
# AWS credentials or network access required) and only exercise the `plan`
# phase, since we only care about the configuration that would be submitted
# to AWS, not real provider behavior.

mock_provider "aws" {}

variables {
  environment            = "test"
  private_app_subnet_ids = ["subnet-0123456789abcdef0", "subnet-0fedcba9876543210"]
  asg_sg_id              = "sg-0123456789abcdef0"
  target_group_arn       = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/test-tg/0123456789abcdef"
}

# Baseline: with only the required variables set (all defaults for
# optional inputs), the launch template must enforce IMDSv2 with a hop
# limit of 1. This is the core hardening behavior added by this PR.
run "launch_template_enforces_imdsv2_by_default" {
  command = plan

  assert {
    condition     = length(aws_launch_template.main.metadata_options) == 1
    error_message = "Launch template must define exactly one metadata_options block"
  }

  assert {
    condition     = aws_launch_template.main.metadata_options[0].http_endpoint == "enabled"
    error_message = "Instance metadata service (IMDS) must remain enabled (http_endpoint = \"enabled\")"
  }

  assert {
    condition     = aws_launch_template.main.metadata_options[0].http_tokens == "required"
    error_message = "IMDSv2 must be enforced: http_tokens must be \"required\", not \"optional\""
  }

  assert {
    condition     = aws_launch_template.main.metadata_options[0].http_put_response_hop_limit == 1
    error_message = "Metadata hop limit must be capped at 1 to prevent metadata access from containers/proxies on the instance"
  }
}

# Regression/negative case: the hop limit must be exactly 1, not the AWS
# default of 2 or any higher value that would allow metadata requests to
# traverse additional network hops (e.g. from a container).
run "launch_template_hop_limit_is_not_default_of_two" {
  command = plan

  assert {
    condition     = aws_launch_template.main.metadata_options[0].http_put_response_hop_limit != 2
    error_message = "Metadata hop limit must not be left at the AWS default of 2; it must be hardened to 1"
  }
}

# The IMDSv2 hardening must not be conditional on instance type: Graviton
# (arm64) instance types must get the same metadata_options as x86_64.
run "launch_template_enforces_imdsv2_for_arm64_instance_types" {
  command = plan

  variables {
    instance_type = "m6g.large"
  }

  assert {
    condition     = aws_launch_template.main.metadata_options[0].http_tokens == "required"
    error_message = "IMDSv2 enforcement must apply regardless of instance type (including Graviton/arm64 families)"
  }

  assert {
    condition     = aws_launch_template.main.metadata_options[0].http_put_response_hop_limit == 1
    error_message = "Hop limit must be capped at 1 regardless of instance type (including Graviton/arm64 families)"
  }
}

# The IMDSv2 hardening must not be conditional on an explicitly supplied
# AMI ID (as opposed to the default SSM-resolved AMI).
run "launch_template_enforces_imdsv2_with_custom_ami" {
  command = plan

  variables {
    ami_id = "ami-0123456789abcdef0"
  }

  assert {
    condition     = aws_launch_template.main.metadata_options[0].http_endpoint == "enabled"
    error_message = "IMDS endpoint must remain enabled when a custom AMI ID is supplied"
  }

  assert {
    condition     = aws_launch_template.main.metadata_options[0].http_tokens == "required"
    error_message = "IMDSv2 must be enforced even when a custom AMI ID is supplied"
  }
}

# The IMDSv2 hardening must not be conditional on ASG sizing inputs.
run "launch_template_enforces_imdsv2_regardless_of_asg_sizing" {
  command = plan

  variables {
    min_size         = 1
    max_size         = 10
    desired_capacity = 3
  }

  assert {
    condition = (
      aws_launch_template.main.metadata_options[0].http_endpoint == "enabled" &&
      aws_launch_template.main.metadata_options[0].http_tokens == "required" &&
      aws_launch_template.main.metadata_options[0].http_put_response_hop_limit == 1
    )
    error_message = "Metadata hardening must be applied identically regardless of ASG min/max/desired capacity settings"
  }
}