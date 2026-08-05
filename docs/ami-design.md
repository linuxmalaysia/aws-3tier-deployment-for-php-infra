---
layout: default
title: "AMI Hardening & Baking Strategy"
---

# AMI Hardening & Baking Strategy (with ASIMP Integration)

This document describes the pre-baked Amazon Machine Image (AMI) strategy, automated software provisioning pipelines, and security compliance baselines utilized to deploy our **PHP CodeIgniter Web Application** within the **AWS Asia Pacific (Malaysia) Region (`ap-southeast-5`)**.

---

## 1. Pre-Baked vs. Just-In-Time Provisioning

When managing Auto Scaling Groups (ASGs) in high-throughput enterprise environments, the speed and reliability of spawning new compute nodes is critical. We adopt a **Pre-Baked AMI Strategy** to maximize operational efficiency:

- **Legacy "Just-In-Time" Bootstrapping (Slow & Fragile):** Spawning a generic OS image and downloading/installing Nginx, PHP-FPM, PHP extensions, and security updates on every instance start. This takes 5 to 10 minutes, relies heavily on third-party package repositories being online, and delays the autoscaling response time.
- **Pre-Baked Golden AMI Strategy (Fast & Resilient):** Standardizing all compute nodes on pre-packaged, fully configured, and pre-hardened custom AMIs (`ami-php-app-*`). Spawning a new instance takes under 45 seconds, requires zero package downloads during bootstrap, and guarantees 100% configuration consistency.

---

## 2. Standardized Compute Tiers & Base Images

Our CodeIgniter deployment runs on a hardened, optimized baseline:

### Golden PHP-FPM Web Application AMI (`ami-php-app-*`)
- **Base Operating System:** Ubuntu 26.04 LTS or Amazon Linux 2023.
- **Compute Architecture:** AWS Graviton ARM64 architecture (`t4g.*` or `m6g.*` instance classes).
- **Pre-Installed Stack:**
  - Nginx (optimized with HTTP/2 and custom buffer limits).
  - PHP 8.2 or 8.3 with standard FastCGI Process Manager (PHP-FPM).
  - Essential PHP extensions: `php-mysqli`/`php-pgsql`, `php-mbstring`, `php-xml`, `php-curl`, `php-intl`, `php-zip`, `php-opcache`.
  - AWS Systems Manager (SSM) Agent (for secure, passwordless instance management).
  - AWS CloudWatch Agent (pre-configured to stream Nginx access/error logs and PHP-FPM logs).

---

## 3. ASIMP Security Hardening and Compliance Integration

To meet enterprise compliance standards in Malaysia (e.g., PDPA and central bank audits), all custom AMIs are hardened using **ASIMP (Ansible System Integrity Management Platform)** before being deployed to the active ASG launch templates.

ASIMP executes an automated, host-based hardening and security verification pipeline:

```
                  [ Staging Standalone EC2 ]
                             │
                             ▼
                [ ASIMP Ansible Provisioning ]
                 - Install Nginx, PHP, and PHP-FPM
                 - Apply CIS Security Controls
                             │
                             ▼
                [ ASIMP Security Verification ]
                 - Run OpenSCAP Security Auditing
                 - Run Lynis Configuration Scan
                             │
                             ▼
                [ AMI Capture (Golden AMI) ]
```

### Key Security Controls Applied during AMI Baking:
1. **Disabled Direct Root SSH:** Enforces public-key authentication, disables password login, and limits connection access to whitelisted internal Bastion IPs.
2. **Package Integrity Scanning:** Runs `debsums` verification to confirm that no installed system binaries have been modified.
3. **CIS Benchmarks Level 2 Compliance:** Enforces file permissions, secures temporary storage mount options, and restricts access to system-level compilers.
4. **PHP Security Best Practices:** Enforces secure PHP settings within `php.ini` (disabling dangerous functions like `exec`, `shell_exec`, `system`, and hiding PHP version headers).
5. **Pre-Generated SCAP Scorecards:** Generates comprehensive HTML compliance scorecards at `/var/log/openscap-after-report.html` as cryptographic proof of audit compliance.
