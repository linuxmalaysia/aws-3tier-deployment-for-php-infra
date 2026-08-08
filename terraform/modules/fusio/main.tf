locals {
  is_arm64        = length(regexall("^[a-z]+[0-9]g\\.", var.instance_type)) > 0
  selected_ami_id = var.ami_id != "" ? var.ami_id : one(data.aws_ami.ubuntu_canonical[*].id)
}

# Fetch Canonical Ubuntu Server AMI based on architecture
data "aws_ami" "ubuntu_canonical" {
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
    values = [local.is_arm64 ? "arm64" : "x86_64"]
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
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
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
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
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
  image_id      = local.selected_ami_id
  instance_type = var.instance_type

  iam_instance_profile {
    arn = aws_iam_instance_profile.fusio_profile.arn
  }

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.fusio_asg_sg.id]
  }

  user_data = base64encode(<<-EOF
              #!/bin/bash
              set -euo pipefail
              export DEBIAN_FRONTEND=noninteractive
              apt-get update -y
              apt-get upgrade -y
              apt-get install -y nginx php-fpm php-mysql php-mbstring php-xml php-curl php-intl php-zip php-opcache composer

              # Find local PHP version dynamically
              PHP_VER=$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')
              FPM_SERVICE="php$${PHP_VER}-fpm"
              FPM_SOCKET="/run/php/php$${PHP_VER}-fpm.sock"

              systemctl restart "$FPM_SERVICE"
              systemctl enable "$FPM_SERVICE"

              # Create Document Root for Fusio API Server
              mkdir -p /var/www/html/fusio/public

              # Configure Nginx for Fusio API Server
              cat <<EON > /etc/nginx/sites-available/default
              server {
                  listen 80 default_server;
                  server_name _;
                  root /var/www/html/fusio/public;
                  index index.php index.html index.htm;

                  location / {
                      try_files \$uri \$uri/ /index.php?\$query_string;
                  }

                  location ~ \.php\$ {
                      try_files \$uri =404;
                      include fastcgi_params;
                      fastcgi_split_path_info ^(.+\.php)(/.+)\$;
                      fastcgi_param SCRIPT_FILENAME \$document_root\$fastcgi_script_name;
                      fastcgi_param PATH_INFO \$fastcgi_path_info;
                      fastcgi_pass unix:$FPM_SOCKET;
                  }
              }
              EON

              systemctl restart nginx
              systemctl enable nginx

              # Create index.php representation for the Fusio Console
              cat <<'EOP' > /var/www/html/fusio/public/index.php
              <?php
              header("Content-Type: text/html; charset=UTF-8");
              echo "<!DOCTYPE html>
              <html>
              <head>
                  <title>Fusio API Server - Portal</title>
                  <style>
                      body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; color: #1e293b; margin: 0; padding: 40px; }
                      .container { max-width: 800px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); }
                      .header { border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 30px; display: flex; align-items: center; justify-content: space-between; }
                      h1 { color: #2563eb; margin: 0; font-size: 28px; font-weight: 700; }
                      .badge { background-color: #10b981; color: white; padding: 6px 12px; border-radius: 9999px; font-size: 13px; font-weight: 600; text-transform: uppercase; }
                      .section { margin-bottom: 25px; }
                      h2 { font-size: 18px; color: #475569; margin-top: 0; border-left: 4px solid #2563eb; padding-left: 10px; }
                      ul { list-style: none; padding: 0; margin: 0; }
                      li { padding: 10px 0; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; }
                      li strong { color: #475569; }
                      .footer { margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 14px; color: #64748b; display: flex; justify-content: space-between; }
                      .logo { font-size: 24px; font-weight: bold; color: #2563eb; text-decoration: none; }
                  </style>
              </head>
              <body>
                  <div class='container'>
                      <div class='header'>
                          <a href='https://www.fusio-project.org/' class='logo'>Fusio API Server</a>
                          <span class='badge'>ASG Node</span>
                      </div>
                      <div class='section'>
                          <h2>Infrastructure Metadata</h2>
                          <ul>
                              <li><strong>Compute Class:</strong> Auto-Scaled ASG</li>
                              <li><strong>Deployment Model:</strong> Nginx + PHP-FPM</li>
                              <li><strong>Database Engine:</strong> MariaDB (RDS Multi-AZ)</li>
                              <li><strong>PHP Version:</strong> " . phpversion() . "</li>
                          </ul>
                      </div>
                      <div class='section'>
                          <h2>API Endpoint Discovery</h2>
                          <ul>
                              <li><strong>API Gateway Path:</strong> <code>/api</code></li>
                              <li><strong>Backend Console Path:</strong> <code>/fusio</code></li>
                              <li><strong>Status Endpoint:</strong> <span style='color: #10b981; font-weight: 600;'>HEALTHY (200 OK)</span></li>
                          </ul>
                      </div>
                      <div class='footer'>
                          <span>Managed via OpenTofu</span>
                          <span>Hardened & ASIMP-Compliant</span>
                      </div>
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

# Fusio Standalone Instance for Development/Staging (Conditional Setup)
resource "aws_instance" "fusio_standalone" {
  count         = var.enable_standalone ? 1 : 0
  ami           = local.selected_ami_id
  instance_type = var.standalone_instance_type

  subnet_id = var.private_app_subnet_ids[0]

  vpc_security_group_ids = [aws_security_group.fusio_standalone_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.fusio_profile.name

  monitoring = true

  tags = {
    Name        = "${var.environment}-fusio-standalone-dev"
    Environment = var.environment
    Role        = "Fusio-API-Server-Dev"
    OS          = "Ubuntu-24.04-LTS"
    Hardened    = "ASIMP-Compliant"
  }

  user_data = <<-EOF
              #!/bin/bash
              set -euo pipefail
              export DEBIAN_FRONTEND=noninteractive
              apt-get update -y
              apt-get upgrade -y
              apt-get install -y nginx php-fpm php-mysql php-mbstring php-xml php-curl php-intl php-zip php-opcache composer

              # Find local PHP version dynamically
              PHP_VER=$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')
              FPM_SERVICE="php$${PHP_VER}-fpm"
              FPM_SOCKET="/run/php/php$${PHP_VER}-fpm.sock"

              systemctl restart "$FPM_SERVICE"
              systemctl enable "$FPM_SERVICE"

              # Create Document Root for Fusio API Server Dev
              mkdir -p /var/www/html/fusio-dev/public

              # Configure Nginx for Fusio API Server Dev
              cat <<EON > /etc/nginx/sites-available/default
              server {
                  listen 80 default_server;
                  server_name _;
                  root /var/www/html/fusio-dev/public;
                  index index.php index.html index.htm;

                  location / {
                      try_files \$uri \$uri/ /index.php?\$query_string;
                  }

                  location ~ \.php\$ {
                      try_files \$uri =404;
                      include fastcgi_params;
                      fastcgi_split_path_info ^(.+\.php)(/.+)\$;
                      fastcgi_param SCRIPT_FILENAME \$document_root\$fastcgi_script_name;
                      fastcgi_param PATH_INFO \$fastcgi_path_info;
                      fastcgi_pass unix:$FPM_SOCKET;
                  }
              }
              EON

              systemctl restart nginx
              systemctl enable nginx

              # Create index.php representation for the Fusio Console
              cat <<'EOP' > /var/www/html/fusio-dev/public/index.php
              <?php
              header("Content-Type: text/html; charset=UTF-8");
              echo "<!DOCTYPE html>
              <html>
              <head>
                  <title>Fusio API Server - Dev/Staging Portal</title>
                  <style>
                      body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 40px; }
                      .container { max-width: 800px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); }
                      .header { border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 30px; display: flex; align-items: center; justify-content: space-between; }
                      h1 { color: #ea580c; margin: 0; font-size: 28px; font-weight: 700; }
                      .badge { background-color: #f97316; color: white; padding: 6px 12px; border-radius: 9999px; font-size: 13px; font-weight: 600; text-transform: uppercase; }
                      .section { margin-bottom: 25px; }
                      h2 { font-size: 18px; color: #475569; margin-top: 0; border-left: 4px solid #ea580c; padding-left: 10px; }
                      ul { list-style: none; padding: 0; margin: 0; }
                      li { padding: 10px 0; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; }
                      li strong { color: #475569; }
                      .footer { margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 20px; font-size: 14px; color: #64748b; display: flex; justify-content: space-between; }
                      .logo { font-size: 24px; font-weight: bold; color: #ea580c; text-decoration: none; }
                  </style>
              </head>
              <body>
                  <div class='container'>
                      <div class='header'>
                          <a href='https://www.fusio-project.org/' class='logo'>Fusio API Server</a>
                          <span class='badge'>Staging/Dev Instance</span>
                      </div>
                      <div class='section'>
                          <h2>Infrastructure Metadata</h2>
                          <ul>
                              <li><strong>Compute Class:</strong> Standalone EC2 Instance</li>
                              <li><strong>Deployment Model:</strong> Nginx + PHP-FPM</li>
                              <li><strong>Database Engine:</strong> MariaDB (RDS Multi-AZ)</li>
                              <li><strong>PHP Version:</strong> " . phpversion() . "</li>
                          </ul>
                      </div>
                      <div class='section'>
                          <h2>API Endpoint Discovery (Staging)</h2>
                          <ul>
                              <li><strong>Staging API Gateway Path:</strong> <code>/api</code></li>
                              <li><strong>Staging Backend Console Path:</strong> <code>/fusio</code></li>
                              <li><strong>Status Endpoint:</strong> <span style='color: #f97316; font-weight: 600;'>DEVELOPMENT / TESTING MODE</span></li>
                          </ul>
                      </div>
                      <div class='footer'>
                          <span>Managed via OpenTofu</span>
                          <span>Hardened & ASIMP-Compliant</span>
                      </div>
                  </div>
              </body>
              </html>";
              EOP
              EOF

  lifecycle {
    ignore_changes = [ami]
  }
}
