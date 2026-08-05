#!/bin/bash
# Enable safety flags
set -euo pipefail

echo "=== Bootstrapping Nginx & PHP-FPM for CodeIgniter Web Application ==="

# Simple metadata service call to retrieve EC2 instance metadata with bounded timeouts
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" --max-time 2 --connect-timeout 2 || echo "")

if [ -n "$TOKEN" ]; then
    INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id --max-time 2 --connect-timeout 2 || echo "unknown-instance-id")
    AZ=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone --max-time 2 --connect-timeout 2 || echo "unknown-az")
else
    INSTANCE_ID="unknown-instance-id"
    AZ="unknown-az"
fi

# Detect OS
if [ -f /etc/debian_version ]; then
    echo "Detected Debian/Ubuntu OS"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get upgrade -y
    apt-get install -y nginx php-fpm php-mysql php-pgsql php-mbstring php-xml php-curl php-intl php-zip php-opcache

    # Find local PHP version (e.g., 8.2, 8.3)
    PHP_VER=$(php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')
    FPM_SERVICE="php${PHP_VER}-fpm"
    FPM_SOCKET="/run/php/php${PHP_VER}-fpm.sock"

    # Configure PHP-FPM socket path and ownership for Nginx on Ubuntu
    systemctl restart "$FPM_SERVICE"
    systemctl enable "$FPM_SERVICE"

elif [ -f /etc/os-release ] && grep -q "Amazon Linux" /etc/os-release; then
    echo "Detected Amazon Linux OS"
    dnf update -y
    dnf install -y nginx php-fpm php-mysqli php-pdo php-mbstring php-xml php-curl php-intl php-zip php-opcache

    FPM_SERVICE="php-fpm"
    FPM_SOCKET="/run/php-fpm/www.sock"

    systemctl restart "$FPM_SERVICE"
    systemctl enable "$FPM_SERVICE"
else
    echo "Fallback OS configuration"
    exit 1
fi

# Ensure Nginx is started and enabled
systemctl restart nginx
systemctl enable nginx

# Create Document Root for CodeIgniter
mkdir -p /var/www/html/codeigniter/public

# Generate custom Nginx configuration to point to PHP-FPM
NGINX_CONF_PATH="/etc/nginx/sites-available/default"
if [ ! -d "/etc/nginx/sites-available" ]; then
    # On Amazon Linux, use /etc/nginx/conf.d/codeigniter.conf
    NGINX_CONF_PATH="/etc/nginx/conf.d/codeigniter.conf"
    # Remove default server block if it exists
    sed -i '/default_server/d' /etc/nginx/nginx.conf || true
fi

cat <<EOF > "$NGINX_CONF_PATH"
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
EOF

# Restart Nginx to load the configuration
systemctl restart nginx

# Create index.php mapping the standard CodeIgniter entrypoint with 3-tier system information
cat <<EOF > /var/www/html/codeigniter/public/index.php
<?php
// Mock CodeIgniter 4 Front Controller showing 3-tier stats
define('CI_VERSION', '4.5.1');
define('ENVIRONMENT', 'production');

\$db_status = 'Disconnected (Pending Configuration)';
\$valkey_status = 'Disconnected (Pending Configuration)';

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
        <p><strong>System Integrations:</strong></p>
        <ul>
            <li><strong>Database:</strong> " . \$db_status . "</li>
            <li><strong>Valkey Session Cache:</strong> " . \$valkey_status . "</li>
        </ul>
        <div class='footer'>Deploy managed with OpenTofu. Hardened & Secure.</div>
    </div>
</body>
</html>";
EOF

echo "=== Bootstrapping Complete ==="
