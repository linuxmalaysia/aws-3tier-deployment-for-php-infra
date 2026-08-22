# Unit tests for the ASG module's Auto Scaling Group, IAM, AMI-selection,
# and scaling-policy resources after `terraform/modules/asg/main.tf` was
# split into single-responsibility files (`asg.tf`, `data.tf`, `iam.tf`,
# `launch_template.tf`, `scaling_policies.tf`). This is a pure refactor
# (no resource arguments changed), so these tests exist to guard against
# regressions introduced by the split itself: that every resource still
# plans with the same configuration and that the cross-file references
# between the new files (e.g. the ASG referencing the launch template,
# the scaling policies/alarms referencing the ASG, the launch template
# referencing the IAM instance profile and the AMI-selection locals) are
# still wired correctly.
#
# These tests use a mocked "aws" provider so they run entirely locally (no
# AWS credentials or network access required) and only exercise the `plan`
# phase, since we only care about the configuration that would be
# submitted to AWS, not real provider behavior.

mock_provider "aws" {}

variables {
  environment            = "test"
  private_app_subnet_ids = ["subnet-0123456789abcdef0", "subnet-0fedcba9876543210"]
  asg_sg_id              = "sg-0123456789abcdef0"
  target_group_arn       = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/test-tg/0123456789abcdef"
}

# Baseline: with only the required variables set, the Auto Scaling Group
# (now defined in asg.tf) must be wired to the launch template (now in
# launch_template.tf) and use the documented defaults for sizing, health
# checks, and rollout behavior.
run "asg_wires_to_launch_template_with_documented_defaults" {
  command = plan

  assert {
    condition     = aws_autoscaling_group.main.min_size == 2
    error_message = "Default min_size must remain 2"
  }

  assert {
    condition     = aws_autoscaling_group.main.max_size == 5
    error_message = "Default max_size must remain 5"
  }

  assert {
    condition     = aws_autoscaling_group.main.desired_capacity == 2
    error_message = "Default desired_capacity must remain 2"
  }

  assert {
    condition     = aws_autoscaling_group.main.health_check_type == "ELB"
    error_message = "ASG must use ELB health checks"
  }

  assert {
    condition     = aws_autoscaling_group.main.health_check_grace_period == 300
    error_message = "ASG health check grace period must remain 300 seconds"
  }

  assert {
    condition     = jsonencode(aws_autoscaling_group.main.target_group_arns) == jsonencode([var.target_group_arn])
    error_message = "ASG must attach to the target group ARN passed in via variables"
  }

  assert {
    condition     = length(aws_autoscaling_group.main.launch_template) == 1
    error_message = "ASG must define exactly one launch_template block"
  }

  assert {
    condition     = aws_autoscaling_group.main.launch_template[0].id == aws_launch_template.main.id
    error_message = "ASG (asg.tf) must still reference the launch template resource now defined in launch_template.tf"
  }

  assert {
    condition     = aws_autoscaling_group.main.launch_template[0].version == "$Latest"
    error_message = "ASG must always roll out the latest launch template version"
  }

  assert {
    condition     = aws_autoscaling_group.main.force_delete == true
    error_message = "ASG must have force_delete enabled"
  }
}

# The rolling instance refresh configuration must survive the split intact.
run "asg_uses_rolling_instance_refresh_with_fifty_percent_min_healthy" {
  command = plan

  assert {
    condition     = length(aws_autoscaling_group.main.instance_refresh) == 1
    error_message = "ASG must define exactly one instance_refresh block"
  }

  assert {
    condition     = aws_autoscaling_group.main.instance_refresh[0].strategy == "Rolling"
    error_message = "ASG instance refresh strategy must remain 'Rolling'"
  }

  assert {
    condition     = aws_autoscaling_group.main.instance_refresh[0].preferences[0].min_healthy_percentage == 50
    error_message = "ASG instance refresh must keep at least 50%% of instances healthy during rollout"
  }

  assert {
    condition     = jsonencode(aws_autoscaling_group.main.instance_refresh[0].triggers) == jsonencode(["tag"])
    error_message = "ASG instance refresh must remain triggered by tag changes"
  }
}

# Environment tagging and propagation to launched instances must survive
# the split.
run "asg_propagates_environment_tag_to_instances" {
  command = plan

  assert {
    condition = anytrue([
      for t in aws_autoscaling_group.main.tag :
      t.key == "Environment" && t.value == var.environment && t.propagate_at_launch == true
    ])
    error_message = "ASG must tag instances with the Environment tag and propagate it at launch"
  }
}

# Custom sizing inputs must still flow through asg.tf's variable
# references after the split (regression against the fields being
# hardcoded or misrouted during the refactor).
run "asg_honors_custom_sizing_variables" {
  command = plan

  variables {
    min_size         = 1
    max_size         = 10
    desired_capacity = 3
  }

  assert {
    condition = (
      aws_autoscaling_group.main.min_size == 1 &&
      aws_autoscaling_group.main.max_size == 10 &&
      aws_autoscaling_group.main.desired_capacity == 3
    )
    error_message = "ASG must honor custom min_size/max_size/desired_capacity variables"
  }
}

# The IAM role/instance profile (now in iam.tf) must still be attached to
# the launch template (now in launch_template.tf).
run "iam_instance_profile_wired_to_launch_template" {
  command = plan

  assert {
    condition     = length(aws_launch_template.main.iam_instance_profile) == 1
    error_message = "Launch template must define exactly one iam_instance_profile block"
  }

  assert {
    condition     = aws_launch_template.main.iam_instance_profile[0].arn == aws_iam_instance_profile.instance_profile.arn
    error_message = "Launch template (launch_template.tf) must still reference the instance profile now defined in iam.tf"
  }

  assert {
    condition     = aws_iam_instance_profile.instance_profile.role == aws_iam_role.instance_role.name
    error_message = "IAM instance profile must still be linked to the IAM role within iam.tf"
  }

  assert {
    condition     = aws_iam_role_policy_attachment.ssm_policy.role == aws_iam_role.instance_role.name
    error_message = "SSM policy attachment must still target the IAM role within iam.tf"
  }

  assert {
    condition     = aws_iam_role_policy_attachment.ssm_policy.policy_arn == "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    error_message = "SSM policy attachment must still use the AmazonSSMManagedInstanceCore managed policy"
  }
}

# IAM role and instance profile names must remain scoped by environment.
run "iam_resource_names_are_environment_scoped" {
  command = plan

  assert {
    condition     = aws_iam_role.instance_role.name == "test-asg-instance-role"
    error_message = "IAM role name must be prefixed with the environment name"
  }

  assert {
    condition     = aws_iam_instance_profile.instance_profile.name == "test-asg-instance-profile"
    error_message = "IAM instance profile name must be prefixed with the environment name"
  }
}

# AMI selection (data.tf) must still flow into the launch template
# (launch_template.tf): an explicitly supplied ami_id must bypass the SSM
# data sources entirely.
run "launch_template_uses_explicit_ami_id_when_provided" {
  command = plan

  variables {
    ami_id = "ami-0123456789abcdef0"
  }

  assert {
    condition     = aws_launch_template.main.image_id == "ami-0123456789abcdef0"
    error_message = "Launch template must use the explicitly supplied ami_id, bypassing AMI auto-resolution"
  }
}

# When no ami_id is supplied, the x86_64 SSM-resolved AMI (data.tf) must be
# selected for a non-Graviton instance type.
run "launch_template_resolves_x86_64_ami_for_non_graviton_instance_type" {
  command = plan

  variables {
    instance_type = "t3.micro"
  }

  assert {
    condition     = aws_launch_template.main.image_id == data.aws_ssm_parameter.al2023_x86_64.value
    error_message = "Launch template must use the x86_64 AMI data source for non-Graviton instance types"
  }
}

# When no ami_id is supplied, the arm64 SSM-resolved AMI (data.tf) must be
# selected for a Graviton instance type.
run "launch_template_resolves_arm64_ami_for_graviton_instance_type" {
  command = plan

  variables {
    instance_type = "m6g.large"
  }

  assert {
    condition     = aws_launch_template.main.image_id == data.aws_ssm_parameter.al2023_arm64.value
    error_message = "Launch template must use the arm64 AMI data source for Graviton instance types"
  }
}

# The scaling policies and CloudWatch alarms (now in scaling_policies.tf)
# must still reference the Auto Scaling Group (now in asg.tf) by name.
run "scaling_policies_and_alarms_wired_to_asg" {
  command = plan

  assert {
    condition     = aws_autoscaling_policy.scale_out.scaling_adjustment == 1
    error_message = "Scale-out policy must increase capacity by 1"
  }

  assert {
    condition     = aws_autoscaling_policy.scale_out.adjustment_type == "ChangeInCapacity"
    error_message = "Scale-out policy must use ChangeInCapacity adjustment type"
  }

  assert {
    condition     = aws_autoscaling_policy.scale_out.autoscaling_group_name == aws_autoscaling_group.main.name
    error_message = "Scale-out policy (scaling_policies.tf) must still reference the ASG now defined in asg.tf"
  }

  assert {
    condition     = aws_autoscaling_policy.scale_in.scaling_adjustment == -1
    error_message = "Scale-in policy must decrease capacity by 1"
  }

  assert {
    condition     = aws_autoscaling_policy.scale_in.autoscaling_group_name == aws_autoscaling_group.main.name
    error_message = "Scale-in policy (scaling_policies.tf) must still reference the ASG now defined in asg.tf"
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.cpu_high.comparison_operator == "GreaterThanOrEqualToThreshold"
    error_message = "High-CPU alarm comparison operator must remain GreaterThanOrEqualToThreshold"
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.cpu_high.threshold == 70
    error_message = "High-CPU alarm threshold must remain 70"
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.cpu_high.dimensions["AutoScalingGroupName"] == aws_autoscaling_group.main.name
    error_message = "High-CPU alarm must be scoped to the ASG now defined in asg.tf"
  }

  assert {
    condition     = tolist(aws_cloudwatch_metric_alarm.cpu_high.alarm_actions)[0] == aws_autoscaling_policy.scale_out.arn
    error_message = "High-CPU alarm must trigger the scale-out policy"
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.cpu_low.comparison_operator == "LessThanOrEqualToThreshold"
    error_message = "Low-CPU alarm comparison operator must remain LessThanOrEqualToThreshold"
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.cpu_low.threshold == 30
    error_message = "Low-CPU alarm threshold must remain 30"
  }

  assert {
    condition     = aws_cloudwatch_metric_alarm.cpu_low.dimensions["AutoScalingGroupName"] == aws_autoscaling_group.main.name
    error_message = "Low-CPU alarm must be scoped to the ASG now defined in asg.tf"
  }

  assert {
    condition     = tolist(aws_cloudwatch_metric_alarm.cpu_low.alarm_actions)[0] == aws_autoscaling_policy.scale_in.arn
    error_message = "Low-CPU alarm must trigger the scale-in policy"
  }
}

# The module's outputs (outputs.tf, untouched by the split) must still
# resolve against the ASG now defined in asg.tf.
run "outputs_resolve_against_asg_defined_in_asg_tf" {
  command = plan

  assert {
    condition     = output.asg_id == aws_autoscaling_group.main.id
    error_message = "asg_id output must resolve to the Auto Scaling Group's id"
  }

  assert {
    condition     = output.asg_name == aws_autoscaling_group.main.name
    error_message = "asg_name output must resolve to the Auto Scaling Group's name"
  }

  assert {
    condition     = output.asg_arn == aws_autoscaling_group.main.arn
    error_message = "asg_arn output must resolve to the Auto Scaling Group's arn"
  }
}