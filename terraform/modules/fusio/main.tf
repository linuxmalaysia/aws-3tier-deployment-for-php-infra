locals {
  asg_is_arm64        = length(regexall("^(a1|[a-z]+[0-9]g[a-z]*)\\.", var.instance_type)) > 0
  asg_selected_ami_id = var.ami_id != "" ? var.ami_id : one(data.aws_ami.ubuntu_canonical_asg[*].id)

  standalone_is_arm64        = length(regexall("^(a1|[a-z]+[0-9]g[a-z]*)\\.", var.standalone_instance_type)) > 0
  standalone_selected_ami_id = var.ami_id != "" ? var.ami_id : one(data.aws_ami.ubuntu_canonical_standalone[*].id)
}

# Fetch Canonical Ubuntu Server AMI based on ASG architecture
data "aws_ami" "ubuntu_canonical_asg" {
  count       = var.ami_id == "" ? 1 : 0
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = [var.ubuntu_ami_filter_name]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = [local.asg_is_arm64 ? "arm64" : "x86_64"]
  }
}

# Fetch Canonical Ubuntu Server AMI based on Standalone architecture
data "aws_ami" "ubuntu_canonical_standalone" {
  count       = var.ami_id == "" ? 1 : 0
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = [var.ubuntu_ami_filter_name]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = [local.standalone_is_arm64 ? "arm64" : "x86_64"]
  }
}

# Fusio ASG Security Group
resource "aws_security_group" "fusio_asg_sg" {
  name        = "${var.environment}-fusio-asg-sg"
  description = "Security group for Fusio API Server ASG instances"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Inbound HTTP from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [var.alb_sg_id]
  }

  egress {
    description = "Allow HTTPS outbound for packages and SSM"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description     = "Allow outbound database traffic to RDS"
    from_port       = var.db_port
    to_port         = var.db_port
    protocol        = "tcp"
    security_groups = [var.db_sg_id]
  }

  tags = {
    Name        = "${var.environment}-fusio-asg-sg"
    Environment = var.environment
  }
}

# Fusio Standalone Security Group
resource "aws_security_group" "fusio_standalone_sg" {
  name        = "${var.environment}-fusio-standalone-sg"
  description = "Security group for Fusio Standalone development/staging server"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Inbound HTTP from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [var.alb_sg_id]
  }

  egress {
    description = "Allow HTTPS outbound for packages and SSM"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description     = "Allow outbound database traffic to RDS"
    from_port       = var.db_port
    to_port         = var.db_port
    protocol        = "tcp"
    security_groups = [var.db_sg_id]
  }

  tags = {
    Name        = "${var.environment}-fusio-standalone-sg"
    Environment = var.environment
  }
}

# Inbound rules to allow DB access from Fusio ASG and Standalone SG
resource "aws_security_group_rule" "db_from_fusio_asg" {
  type                     = "ingress"
  description              = "Allow inbound MariaDB connection from Fusio ASG"
  from_port                = var.db_port
  to_port                  = var.db_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.fusio_asg_sg.id
  security_group_id        = var.db_sg_id
}

resource "aws_security_group_rule" "db_from_fusio_standalone" {
  type                     = "ingress"
  description              = "Allow inbound MariaDB connection from Fusio Standalone"
  from_port                = var.db_port
  to_port                  = var.db_port
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.fusio_standalone_sg.id
  security_group_id        = var.db_sg_id
}

# Fusio ALB Target Group
resource "aws_lb_target_group" "fusio_tg" {
  name        = "${var.environment}-fusio-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    protocol            = "HTTP"
    port                = "traffic-port"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
    matcher             = "200-399"
  }

  tags = {
    Name        = "${var.environment}-fusio-tg"
    Environment = var.environment
  }
}

# Fusio ALB Listener Rule
resource "aws_lb_listener_rule" "fusio_rule" {
  listener_arn = var.https_listener_arn
  priority     = 90

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.fusio_tg.arn
  }

  condition {
    path_pattern {
      values = ["/api*", "/fusio*"]
    }
  }
}

# IAM Role & Instance Profile for Fusio instances (SSM enabled)
resource "aws_iam_role" "fusio_role" {
  name = "${var.environment}-fusio-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "fusio_ssm" {
  role       = aws_iam_role.fusio_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "fusio_profile" {
  name = "${var.environment}-fusio-profile"
  role = aws_iam_role.fusio_role.name
}

# Fusio ASG Launch Template
resource "aws_launch_template" "fusio_lt" {
  name_prefix   = "${var.environment}-fusio-lt-"
  image_id      = local.asg_selected_ami_id
  instance_type = var.instance_type

  iam_instance_profile {
    arn = aws_iam_instance_profile.fusio_profile.arn
  }

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.fusio_asg_sg.id]
  }

  user_data = base64encode(templatefile("${path.module}/templates/bootstrap.sh.tftpl", {
    doc_root   = "/var/www/html/fusio"
    node_label = "ASG Node (Static Placeholder)"
  }))

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  block_device_mappings {
    device_name = "/dev/sda1"

    ebs {
      volume_size           = 20
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "${var.environment}-fusio-asg-instance"
      Environment = var.environment
      Role        = "Fusio-API-Server"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Fusio Auto Scaling Group
resource "aws_autoscaling_group" "fusio_asg" {
  name_prefix         = "${var.environment}-fusio-asg-"
  vpc_zone_identifier = var.private_app_subnet_ids

  target_group_arns         = [aws_lb_target_group.fusio_tg.arn]
  health_check_type         = "ELB"
  health_check_grace_period = 300

  min_size         = var.min_size
  max_size         = var.max_size
  desired_capacity = var.desired_capacity

  launch_template {
    id      = aws_launch_template.fusio_lt.id
    version = "$Latest"
  }

  force_delete = var.force_delete

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 50
    }
    triggers = ["tag"]
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  lifecycle {
    create_before_destroy = true
    ignore_changes        = [desired_capacity]
  }
}

# Target-Tracking Autoscaling Policy
resource "aws_autoscaling_policy" "fusio_target_tracking" {
  name                   = "${var.environment}-fusio-asg-target-tracking"
  policy_type            = "TargetTrackingScaling"
  autoscaling_group_name = aws_autoscaling_group.fusio_asg.name

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# Fusio Standalone Instance for Development/Staging (Conditional Setup)
resource "aws_instance" "fusio_standalone" {
  count         = var.enable_standalone ? 1 : 0
  ami           = local.standalone_selected_ami_id
  instance_type = var.standalone_instance_type

  subnet_id = var.private_app_subnet_ids[0]

  vpc_security_group_ids = [aws_security_group.fusio_standalone_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.fusio_profile.name

  monitoring = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name        = "${var.environment}-fusio-standalone-dev"
    Environment = var.environment
    Role        = "Fusio-API-Server-Dev"
    OS          = "Ubuntu-26.04-LTS"
    Hardened    = "ASIMP-Compliant"
  }

  user_data = templatefile("${path.module}/templates/bootstrap.sh.tftpl", {
    doc_root   = "/var/www/html/fusio-dev"
    node_label = "Staging/Dev Instance (Static Placeholder)"
  })

  lifecycle {
    ignore_changes = [ami]
  }
}
