# Fetch latest Amazon Linux 2023 AMI for x86_64
data "aws_ssm_parameter" "al2023_x86_64" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# Fetch latest Amazon Linux 2023 AMI for arm64
data "aws_ssm_parameter" "al2023_arm64" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64"
}

locals {
  # If instance type starts with t4g, m6g, c6g, r6g, etc. (typically Graviton), select arm64.
  is_arm64        = length(regexall("^(a1|[a-z]+[0-9]g[a-z]*)\\.", var.instance_type)) > 0
  default_ami_id  = local.is_arm64 ? data.aws_ssm_parameter.al2023_arm64.value : data.aws_ssm_parameter.al2023_x86_64.value
  selected_ami_id = var.ami_id != "" ? var.ami_id : local.default_ami_id
}
