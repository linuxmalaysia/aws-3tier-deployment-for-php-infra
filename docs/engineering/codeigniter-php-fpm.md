---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "CodeIgniter PHP Application Deployment & Optimization Guide (with Nginx & PHP-FPM)"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier", "php", "codeigniter"]
---

**[DEVOPS EXECUTION]**

# CodeIgniter Deployment Guide (Nginx + PHP-FPM)

## 1. Executive Summary

This guide provides a comprehensive technical blueprint for deploying and optimizing high-performance **CodeIgniter PHP applications** within an enterprise AWS 3-tier architecture.

In this setup, we standardize on **Nginx** acting as the frontend web server and **PHP-FPM** (FastCGI Process Manager) serving the dynamic PHP application layer, hosted on hardened **Ubuntu 26.04 LTS** or **Amazon Linux 2023** instances. Standardizing on **AWS Graviton (ARM64)** compute delivers superior price-performance, while session state is securely managed off-instance using an **Amazon ElastiCache for Valkey** cluster to guarantee stateless horizontal scalability.

---

## 2. Nginx & PHP-FPM 3-Tier Architecture

To achieve absolute zero-trust security and seamless scalability, our architecture decouples web ingress from application execution:

```
                            [ Web Clients ]
                                  │
                                  ▼
                            [ AWS WAFv2 ]      <-- Ingress Security Filter
                                  │
                                  ▼
                    [ Application Load Balancer ] <-- Public Subnets
                                  │
                                  ├──────────────────────────────┐
                                  ▼ (Port 80)                    ▼ (Port 80)
                         [ Private Subnet AZ A ]        [ Private Subnet AZ B ]
                         ┌─────────────────────┐        ┌─────────────────────┐
                         │   Frontend Nginx    │        │   Frontend Nginx    │
                         │         │           │        │         │           │
                         │         ▼ (socket)  │        │         ▼ (socket)  │
                         │      PHP-FPM        │        │      PHP-FPM        │
                         │ (CodeIgniter App)   │        │ (CodeIgniter App)   │
                         └─────────┬───────────┘        └─────────┬───────────┘
                                   │                              │
                      ┌────────────┴───────────────┬──────────────┴────────────┐
                      ▼                            ▼                           ▼
            [ Amazon S3 Bucket ]         [ ElastiCache Valkey ]     [ Amazon RDS Database ]
            (Stateless Uploads)          (Shared Session Caching)   (MySQL / PostgreSQL)
```

1. **Presentation / Web Layer (Nginx):**
   - Nginx handles incoming connections from the ALB, serves static resources directly off high-speed local SSDs, and proxies all dynamic request payloads to the PHP-FPM socket.
2. **Application / Compute Layer (PHP-FPM):**
   - PHP-FPM processes dynamic application controllers. The CodeIgniter runtime is mounted locally. Direct inbound internet route is blocked; outgoing requests (e.g. external payment gateways) are masked by a NAT Gateway.
3. **Caching Layer (ElastiCache Valkey):**
   - All PHP sessions are directed to Valkey over secure TLS connections, enabling the application nodes to remain completely stateless and scale horizontally.
4. **Data Layer (RDS Database):**
   - CodeIgniter connects to a managed Multi-AZ MySQL/PostgreSQL instance via port-restricted private connections.

---

## 3. High-Performance Nginx Configuration

Apply this production-optimized configuration within `/etc/nginx/sites-available/default` (Ubuntu) or `/etc/nginx/conf.d/codeigniter.conf` (Amazon Linux 2023):

```nginx
server {
    listen 80;
    server_name _;

    # Document root points to CodeIgniter's public directory
    root /var/www/html/codeigniter/public;
    index index.php index.html index.htm;

    charset utf-8;

    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;

    # Dynamic Route Handling (Clean URLs in CodeIgniter)
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    # Deny access to hidden system files (.git, .env, etc.)
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Direct serving of high-speed static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|otf)$ {
        expires max;
        log_not_found off;
        access_log off;
        add_header Cache-Control "public, no-transform";
    }

    # Pass dynamic PHP scripts to PHP-FPM Unix Socket
    location ~ \.php$ {
        # Check that file exists before passing to PHP-FPM
        try_files $uri =404;

        # FastCGI Params setup
        include fastcgi_params;
        fastcgi_split_path_info ^(.+\.php)(/.+)$;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;

        # Route to local PHP-FPM socket (PHP 8.2 used as example)
        fastcgi_pass unix:/run/php/php8.2-fpm.sock;

        # Buffer and timeout optimizations
        fastcgi_buffers 16 16k;
        fastcgi_buffer_size 32k;
        fastcgi_read_timeout 600;
        fastcgi_send_timeout 600;
    }
}
```

---

## 4. PHP-FPM Optimization Blueprint

To optimize the execution speed of our CodeIgniter application, adjust the primary PHP-FPM configuration pool (typically found at `/etc/php/8.2/fpm/pool.d/www.conf` on Ubuntu):

### A. Dynamic vs. Static Process Manager (`pm`)
On production servers with dedicated resources, we use **pm = static** to eliminate process spawn latency:

```ini
; Use static PM for predictable production performance
pm = static

; Sized appropriately for instance RAM (assuming ~45MB per PHP-FPM process)
; For a t4g.medium (4GB RAM) with 3GB allocated to PHP: 3000 / 45 ≈ 60 processes
pm.max_children = 60

; The number of seconds after which an idle process will be killed
pm.process_idle_timeout = 10s

; Limit request execution count to prevent memory leaks from degrading performance
pm.max_requests = 1000
```

### B. Opcache & JIT Compilation Settings
Optimize bytecode execution within `/etc/php/8.2/fpm/php.ini`:

```ini
[opcache]
opcache.enable=1
opcache.enable_cli=1
opcache.memory_consumption=256
opcache.interned_strings_buffer=16
opcache.max_accelerated_files=20000
opcache.validate_timestamps=0 ; Set to 0 in production to eliminate file check overhead
opcache.save_comments=1

; JIT compiler configurations
opcache.jit=tracing
opcache.jit_buffer_size=64M
```

---

## 5. CodeIgniter 4 Configuration

### A. Environment Configuration (`.env`)
Generate and mount the following production `.env` file at the root of the CodeIgniter directory:

```ini
#--------------------------------------------------------------------
# ENVIRONMENT
#--------------------------------------------------------------------
CI_ENVIRONMENT = production

#--------------------------------------------------------------------
# APP SETTINGS
#--------------------------------------------------------------------
app.baseURL = 'https://app.linuxmalaysia.com/'
app.forceGlobalSecureRequests = true

#--------------------------------------------------------------------
# DATABASE
#--------------------------------------------------------------------
database.default.hostname = ${DB_HOST}
database.default.database = ${DB_NAME}
database.default.username = ${DB_USER}
database.default.password = ${DB_PASS}
database.default.DBDriver = 'MySQLi' # or 'Postgre' based on RDS Engine
database.default.DBPrefix = ''
database.default.port     = 3306      # or 5432 for Postgres

#--------------------------------------------------------------------
# SESSION (Valkey / Redis Cache Integration)
# NOTE: CodeIgniter 4.3.2 or later is strictly required for secure TLS session URLs.
#--------------------------------------------------------------------
app.sessionDriver = 'CodeIgniter\Session\Handlers\RedisHandler'
app.sessionSavePath = 'tls://${VALKEY_HOST}:6379?auth=${VALKEY_PASSWORD}&timeout=5'
app.sessionCookieName = 'ci_session'
app.sessionExpiration = 7200
app.sessionRegenerateDestroy = true
```

### B. Verifying Stateless Health Check Endpoint
To integrate seamlessly with the AWS Application Load Balancer (ALB), deploy a stateless status controller at `app/Controllers/Health.php`:

```php
<?php

namespace App\Controllers;

use CodeIgniter\Controller;

class Health extends Controller
{
    public function index()
    {
        $response = [
            'status' => 'UP'
        ];

        return $this->response->setJSON($response)->setStatusCode(200);
    }
}
```

This endpoint avoids hitting the database or session store, allowing the ALB to perform lightweight health checks (e.g., `/health`) every few seconds with minimal server load.
