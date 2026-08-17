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
                  # Create secure temporary directory and register cleanup trap
                  SECURE_TMP_DIR=$(mktemp -d -t metadata-XXXXXX 2>/dev/null || mktemp -d)
                  trap 'rm -rf "$SECURE_TMP_DIR"' EXIT

                  # Parallelize synchronous HTTP requests for metadata retrieval
                  curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id --max-time 2 --connect-timeout 2 > "$SECURE_TMP_DIR/instance_id" 2>/dev/null &
                  PID_ID=$!
                  curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone --max-time 2 --connect-timeout 2 > "$SECURE_TMP_DIR/az" 2>/dev/null &
                  PID_AZ=$!

                  # Wait for both background jobs to complete
                  wait $PID_ID $PID_AZ || true

                  INSTANCE_ID=$(cat "$SECURE_TMP_DIR/instance_id" 2>/dev/null || echo "unknown-instance-id")
                  AZ=$(cat "$SECURE_TMP_DIR/az" 2>/dev/null || echo "unknown-az")

                  # Fallback if the files are empty or missing
                  [ -z "$INSTANCE_ID" ] && INSTANCE_ID="unknown-instance-id"
                  [ -z "$AZ" ] && AZ="unknown-az"
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
