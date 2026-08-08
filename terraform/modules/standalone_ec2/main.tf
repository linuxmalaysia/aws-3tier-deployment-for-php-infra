locals {
  is_arm64        = length(regexall("^[a-z]+[0-9]g[a-z]*\\.", var.instance_type)) > 0
  selected_ami_id = var.ami_id != "" ? var.ami_id : one(data.aws_ami.ubuntu_canonical[*].id)
}

# Fetch Canonical Ubuntu Server AMI based on the architecture
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

# Standalone Instance Custom Security Group
resource "aws_security_group" "standalone_sg" {
  name        = "${var.environment}-standalone-ec2-sg"
  description = "Security group for standalone application/developer instances"
  vpc_id      = var.vpc_id

  # Inbound HTTP from the ALB SG for web-facing test applications
  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [var.alb_sg_id]
  }

  # Inbound HTTPS from the ALB SG for secure test applications
  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [var.alb_sg_id]
  }

  # Allow all outbound to NAT Gateway for package updates and auditing
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-standalone-ec2-sg"
    Environment = var.environment
  }
}

# IAM Role for Standalone EC2 Instance to integrate with Systems Manager (SSM)
resource "aws_iam_role" "standalone_role" {
  name = "${var.environment}-standalone-ec2-role"

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

# Attach SSM Policy for secure shell administration and remote patches
resource "aws_iam_role_policy_attachment" "ssm_policy" {
  role       = aws_iam_role.standalone_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "standalone_profile" {
  name = "${var.environment}-standalone-ec2-profile"
  role = aws_iam_role.standalone_role.name
}

# Standalone EC2 Instances
resource "aws_instance" "standalone" {
  count         = var.instance_count
  ami           = local.selected_ami_id
  instance_type = var.instance_type

  subnet_id = var.private_app_subnet_ids[count.index % length(var.private_app_subnet_ids)]

  vpc_security_group_ids = [aws_security_group.standalone_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.standalone_profile.name

  # Enable detailed monitoring for staging audit compatibility
  monitoring = true

  # Tag specifications for proper compliance
  tags = {
    Name        = "${var.environment}-standalone-instance-${count.index + 1}"
    Environment = var.environment
    OS          = "Ubuntu-26.04-LTS"
    Hardened    = "ASIMP-Compliant"
  }

  # Bootstrapping user data for testing
  user_data = <<-EOF
              #!/bin/bash
              set -euo pipefail
              export DEBIAN_FRONTEND=noninteractive
              apt-get update -y
              apt-get upgrade -y
              apt-get install -y nginx php-fpm php-mysql php-pgsql php-mbstring php-xml php-curl php-intl php-zip php-opcache

              # Find local PHP version dynamically
              PHP_VER=$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')
              FPM_SERVICE="php$${PHP_VER}-fpm"
              FPM_SOCKET="/run/php/php$${PHP_VER}-fpm.sock"

              systemctl restart "$FPM_SERVICE"
              systemctl enable "$FPM_SERVICE"
              systemctl restart nginx
              systemctl enable nginx

              # Create Document Root for CodeIgniter
              mkdir -p /var/www/html/codeigniter/public

              # Configure Nginx for CodeIgniter and PHP-FPM Integration
              cat <<EON > /etc/nginx/sites-available/default
              server {
                  listen 80 default_server;
                  server_name _;
                  root /var/www/html/codeigniter/public;
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
                  <title>AWS 3-Tier CodeIgniter Standalone Application</title>
                  <style>
                      body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; color: #333; }
                      .card { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 700px; margin: auto; }
                      h1 { color: #0066cc; margin-top: 0; }
                      .badge { background-color: #ff9800; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
                      .footer { margin-top: 30px; font-size: 0.8em; color: #777; border-top: 1px solid #ddd; padding-top: 15px; }
                      ul { padding-left: 20px; }
                      li { margin-bottom: 8px; }
                  </style>
              </head>
              <body>
                  <div class='card'>
                      <h1>AWS 3-Tier CodeIgniter Standalone Developer Server ${count.index + 1} <span class='badge'>Active (Staging)</span></h1>
                      <p>This is a standalone staging/development instance running Nginx & PHP-FPM, connected to staging infrastructure.</p>
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

  lifecycle {
    ignore_changes = [ami]
  }
}
