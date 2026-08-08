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

# IAM Role for EC2 Instance to integrate with systems or read configurations if needed
resource "aws_iam_role" "instance_role" {
  name = "${var.environment}-asg-instance-role"

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

# Attach AWS SSM Policy for remote management/troubleshooting
resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "instance_profile" {
  name = "${var.environment}-asg-instance-profile"
  role = aws_iam_role.instance_role.name
}

# Launch Template
resource "aws_launch_template" "main" {
  name_prefix   = "${var.environment}-launch-template-"
  image_id      = local.selected_ami_id
  instance_type = var.instance_type

  iam_instance_profile {
    arn = aws_iam_instance_profile.instance_profile.arn
  }

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [var.asg_sg_id]
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  user_data = base64encode(<<-EOF
              #!/bin/bash
              set -euo pipefail
              dnf update -y
              dnf install -y nginx php-fpm php-mysqli php-pdo php-mbstring php-xml php-curl php-intl php-zip php-opcache

              systemctl restart php-fpm
              systemctl enable php-fpm
              systemctl restart nginx
              systemctl enable nginx

              # Create Document Root for CodeIgniter
              mkdir -p /var/www/html/codeigniter/public

              # Configure Nginx for CodeIgniter and PHP-FPM Integration
              cat <<'EON' > /etc/nginx/conf.d/codeigniter.conf
              server {
                  listen 80 default_server;
                  server_name _;
                  root /var/www/html/codeigniter/public;
                  index index.php index.html index.htm;

                  location / {
                      try_files $uri $uri/ /index.php?$query_string;
                  }

                  location ~ \.php$ {
                      try_files $uri =404;
                      include fastcgi_params;
                      fastcgi_split_path_info ^(.+\.php)(/.+)$;
                      fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
                      fastcgi_param PATH_INFO $fastcgi_path_info;
                      fastcgi_pass unix:/run/php-fpm/www.sock;
                  }
              }
              EON

              # Remove default server block if it exists
              sed -i '/default_server/d' /etc/nginx/nginx.conf || true
              systemctl restart nginx

              # Simple metadata service call to retrieve EC2 instance metadata with bounded timeouts
              TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" --max-time 2 --connect-timeout 2 || echo "")
              if [ -n "$TOKEN" ]; then
                  INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id --max-time 2 --connect-timeout 2 || echo "unknown-instance-id")
                  AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone --max-time 2 --connect-timeout 2 || echo "unknown-az")
              else
                  INSTANCE_ID="unknown-instance-id"
                  AZ="unknown-az"
              fi

              # Create starter mock CodeIgniter front controller
              cat <<EOP > /var/www/html/codeigniter/public/index.php
              <?php
              define('CI_VERSION', '4.5.1');
              echo "<html>
              <head>
                  <title>AWS 3-Tier CodeIgniter Application</title>
                  <style>
                      body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; color: #333; }
                      .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 700px; margin: auto; }
                      h1 { color: #0066cc; margin-top: 0; }
                      .badge { background-color: #4caf50; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
                      .footer { margin-top: 30px; font-size: 0.8em; color: #777; border-top: 1px solid #ddd; padding-top: 15px; }
                      ul { padding-left: 20px; }
                      li { margin-bottom: 8px; }
                  </style>
              </head>
              <body>
                  <div class='card'>
                      <h1>AWS 3-Tier CodeIgniter Web Application <span class='badge'>Active</span></h1>
                      <p>This is the application compute tier, running inside a secure, private subnet auto-scaled with an ASG and load balanced by an ALB protected by AWS WAFv2.</p>
                      <hr/>
                      <p><strong>Instance Metadata:</strong></p>
                      <ul>
                          <li><strong>Instance ID:</strong> $INSTANCE_ID</li>
                          <li><strong>Availability Zone:</strong> $AZ</li>
                          <li><strong>PHP Engine:</strong> PHP " . phpversion() . "</li>
                          <li><strong>Framework:</strong> CodeIgniter " . CI_VERSION . "</li>
                      </ul>
                      <div class='footer'>Deploy managed with OpenTofu. Hardened & Secure.</div>
                  </div>
              </body>
              </html>";
              EOP
              EOF
  )

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "${var.environment}-asg-instance"
      Environment = var.environment
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "main" {
  name_prefix         = "${var.environment}-asg-"
  vpc_zone_identifier = var.private_app_subnet_ids

  target_group_arns         = [var.target_group_arn]
  health_check_type         = "ELB"
  health_check_grace_period = 300

  min_size         = var.min_size
  max_size         = var.max_size
  desired_capacity = var.desired_capacity

  launch_template {
    id      = aws_launch_template.main.id
    version = "$Latest"
  }

  force_delete = true

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

# Scale Out (Up) Policy based on CPU
resource "aws_autoscaling_policy" "scale_out" {
  name                   = "${var.environment}-asg-scale-out"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.main.name
}

# Scale In (Down) Policy based on CPU
resource "aws_autoscaling_policy" "scale_in" {
  name                   = "${var.environment}-asg-scale-in"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = aws_autoscaling_group.main.name
}

# CPU Metric Alarm for Scale Out (High CPU > 70%)
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.environment}-asg-high-cpu"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 120
  statistic           = "Average"
  threshold           = 70

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.main.name
  }

  alarm_actions = [aws_autoscaling_policy.scale_out.arn]
}

# CPU Metric Alarm for Scale In (Low CPU < 30%)
resource "aws_cloudwatch_metric_alarm" "cpu_low" {
  alarm_name          = "${var.environment}-asg-low-cpu"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 120
  statistic           = "Average"
  threshold           = 30

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.main.name
  }

  alarm_actions = [aws_autoscaling_policy.scale_in.arn]
}
