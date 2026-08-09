---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "Developer Design Mapping"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier"]
---

**[DEVOPS EXECUTION]**

# Developer Design Alignment Guide

This guide details how we transition the **Developer's First Design** (which specified three separate, standalone Ubuntu 26.04 LTS servers for a PHP web application) into our secure, highly-available, production-ready **AWS 3-Tier Architecture**, without changing any underlying AWS constraints or requirements.

---

## Rationale for the Architectural Transition

The developer's original design was logical but modeled around static, single-node virtual machines. Running critical production infrastructure on standalone VMs presents several operational risks:
1. **Single Points of Failure (SPOFs):** If any of the servers experiences hardware degradation or guest OS crashes, the entire application goes offline.
2. **Direct Public Exposure:** Placing database or application servers directly on public-facing networks increases the surface area for brute-force SSH, port-scanning, and SQL injection (SQLi) attacks.
3. **Manual Scalability & High Latency:** VM resources are fixed and cannot scale dynamically in response to user demand or computational peaks.
4. **Backup and Patches overhead:** Managing backups, OS updates, and package security patches manually across multiple VMs takes significant operational effort.

By aligning this layout with our secure AWS design, we retain **all functionality** of the developer's original services (Nginx, PHP, CodeIgniter, and database) while inheriting cloud-native security, performance, and automation.

---

## Detailed Component Transitions

### 1. Web/App Server (Nginx + PHP-FPM for CodeIgniter)
* **Developer's First Design:** A single Ubuntu server running Nginx & PHP-FPM (2 vCPU, 4GB RAM) exposed to the public internet via port 80/443.
* **AWS Alignment:**
  - **Layer 7 Firewall (AWS WAFv2):** Blocks common exploits (OWASP Top 10, SQLi, XSS) and manages brute-force or DDoS attempts via dynamic IP Rate Limiting.
  - **Application Load Balancer (ALB):** Terminates external SSL/TLS, manages routing rules, and automatically performs health checks to route traffic only to healthy instances.
  - **Private CodeIgniter Web Tier (ASG):** Sized as `t4g.medium` (2 vCPU, 4GB RAM) but deployed within **private subnets** under an Auto Scaling Group (ASG). This ensures the compute instances have *no public IP*, can scale out horizontally, and are protected from brute-force exposure.
  - **Dedicated Standalone Instance (AMI Baking):** Paired with a dedicated PHP Standalone instance inside the private subnets. Connected directly to identical database/S3 resources to test routing/static templates, run CodeIgniter migrations, and pre-bake certified `ami-php-*` images.

### 2. Database Data Tier (SQL Database)
* **Developer's First Design:** A single Ubuntu server (4 vCPU, 16GB RAM) running self-managed database.
* **AWS Alignment:**
  - **Fully Managed RDS (Multi-AZ):** Upgraded to **AWS RDS Database** (Multi-AZ deployment) sized at `db.m6g.xlarge` (4 vCPU, 16GB RAM) or standard Graviton classes.
  - **Multi-AZ Replication:** Synchronously replicates data across physically separate Availability Zones. In the event of an outage in AZ A, AWS automatically fails over to AZ B with zero manual intervention or data loss.
  - **Absolute Network Isolation:** Deployed inside isolated Private Database Subnets. The database security group restricts incoming traffic *exclusively* to the application security group (ASG), preventing any direct internet access.

---

## Operating System & Hardware Optimizations

To deliver maximum efficiency, we transition the underlying hardware platform from legacy x86 virtual machines to **AWS Graviton (ARM64)** processors:

1. **Price-Performance Efficiency:** AWS Graviton (`t4g` and `m6g` instances) delivers up to **40% better price-performance** compared to equivalent x86 instances, significantly lowering the monthly run costs.
2. **Ubuntu 26.04 LTS Base Operating System:** To leverage the latest performance improvements, security features, and modern PHP/container support, we standardize our base platform on **Ubuntu 26.04 LTS**.
3. **Amazon Linux 2023 Option:** For lightweight workloads that do not depend on Canonical specific packages, **Amazon Linux 2023 (AL2023)** remains available as a minimal, cloud-optimized option.

---

## Server Hardening & Security Compliance (ASIMP Integration)

In aligning the developer design with AWS enterprise standards, all Ubuntu 26.04 LTS compute resources (both ASG instances and Standalone instances) are hardened and tuned using **ASIMP (Ansible System Integrity Management Platform)** (available at [github.com/linuxmalaysia/ASIMP](https://github.com/linuxmalaysia/ASIMP)).

ASIMP is a host-based, automated security hardening, compliance, and auditing framework that implements a strict **"Measure, Harden, Re-Measure"** paradigm to verify and guarantee security posturing before the machine is allowed to process production traffic.

### The ASIMP Hardening & Auditing Pipeline

```
  [ PHASE 1: Baseline Auditing ]
               │
               ▼ Generates /var/log/asimp-baseline-scores.json
  [ PHASE 2: Hardening & Mitigations ]
               │  • OS updates, debsums packages verification
               │  • OpenStack ansible-hardening & SSH hardening
               │  • Lynis system level modifications
               ▼
  [ PHASE 3: Verification & Reporting ]
                  • Re-runs audits and outputs comparison scorecard
                  • HTML reports written to /var/log/openscap-after-report.html
```

### Key ASIMP Hardening Capabilities Applied:

1. **Dual-Engine Security Auditing:**
   - **OpenSCAP:** Conducts formal vulnerability and security compliance scanning mapped against the **CIS Security Ubuntu Linux Benchmark Level 2** profile.
   - **Lynis:** Performs comprehensive system configuration auditing, examining OS parameters, boot configurations, cryptography standards, and active network ports.
2. **Pre & Post Scorecard Comparison:**
   - Runs audits prior to hardening to capture initial baselines, then executes them afterwards, logging comparative metrics in `/var/log/asimp-baseline-scores.json`.
   - Generates visually comprehensive, standalone HTML inspection reports at `/var/log/openscap-before-report.html` and `/var/log/openscap-after-report.html`.
3. **Automated Package Updates & debsums Verification:**
   - Standardizes the Ubuntu system upgrade procedures and checks package-level code integrity via `debsums` to detect any unauthorized binary modifications.
4. **Standardized OS Hardening Benchmarks:**
   - Deploys rigorous security compliance controls utilizing OpenStack's `ansible-hardening` role.
   - Standardizes and restricts SSH configuration endpoints using Dev-Sec's certified `ssh-hardening` roles, enforcing secure cipher suites, disabling password-based root access, and specifying key exchange standards.
5. **Detailed System Tuning & Custom Fixes:**
   - Automatically tunes virtual memory configuration parameters, core kernel dumps, file system mounting options (e.g., nodev, nosuid, noexec where appropriate), and limits access to PHP compiler scripts.

---

## Summary of the AWS Security & HA Multipliers

Through this alignment, the developer gets their exact applications deployed with unmatched production capabilities:

```
┌─────────────────────────┬─────────────────────────────────────────────────┐
│ Feature                 │ How AWS Improves Developer's First Design       │
├─────────────────────────┼─────────────────────────────────────────────────┤
│ High Availability       │ Multi-AZ redundancy for Compute and RDS DB.     │
├─────────────────────────┼─────────────────────────────────────────────────┤
│ DDoS & Web Protection   │ AWS WAFv2 blocking bad traffic before compute.  │
├─────────────────────────┼─────────────────────────────────────────────────┤
│ Elastic Scaling         │ ASG automatically adds instances based on load. │
├─────────────────────────┼─────────────────────────────────────────────────┤
│ Data Protection         │ Automatic, daily snapshots + Multi-AZ backups.  │
└─────────────────────────┴─────────────────────────────────────────────────┘
```
