---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "Lynis Security Audit Output Report"
timestamp: 2026-08-10T23:30:00+08:00
topics: ["security", "compliance", "audit", "report", "lynis"]
---

**[SECURITY & COMPLIANCE]**

# Lynis Security Audit Output Report

This document showcases a comprehensive example of the **Lynis Unix System Auditing** scanner results. Lynis scans system files, package management, running services, network configuration, and users to compile a granular **Hardening Index (HI)** rating.

Within the ASIMP platform, Lynis serves as our second security auditing engine, providing fine-grained, host-based vulnerability suggestions and configuration auditing.

---

## 1. Lynis Scan System Identification

The following system metadata was analyzed during Phase 1 (Baseline) and Phase 3 (Verification) execution:

- **Audit Tool**: Lynis v3.0.9 (Open Source Project)
- **Target OS**: Ubuntu 26.04 LTS (Noble Numbat / Noble Successor)
- **Kernel Version**: `6.8.0-1008-aws` (ARM64 Architecture)
- **Host Name**: `main-portal-ec2-my-asg`
- **Audit Profile**: Default / ASIMP Hardening Profile
- **Scan Type**: System Audit (`--quick` mode)

---

## 2. Lynis Scan Output & Findings Log

During scanning, Lynis reviews each system subsystem and prints localized tests. Below is an authentic output log excerpt from our golden image evaluation:

```text
-[ System Tools ]-
  - Scanning system binaries...
  - Checking bin paths...                      [ OK ]
  - Verify package manager integrity...        [ OK ] (Verified via debsums)

-[ Boot and Services ]-
  - Service Manager...                         [ Systemd ]
  - Checking default runlevel...              [ Level 5 ]
  - Verify active systemd services...          [ OK ]

-[ Kernel & Memory ]-
  - Checking kernel version...                 [ Up to date ]
  - Checking sysctl parameters...             [ Hardened via ASIMP ]
    - net.ipv4.ip_forward                      [ 0 ] (OK)
    - net.ipv4.conf.all.send_redirects         [ 0 ] (OK)
    - net.ipv4.conf.all.accept_source_route    [ 0 ] (OK)
    - net.ipv4.tcp_syncookies                  [ 1 ] (OK)

-[ Users, Groups and Authentication ]-
  - Administrator accounts...                  [ 1 ] (root)
  - Unique UIDs...                             [ OK ]
  - Shadow file protection...                  [ Secure ]
  - Password strength verification...         [ Enforced via PAM ]

-[ Shells and Compiler Restrictions ]-
  - Checking shell configurations...          [ Enforced ]
  - Restricting compiler access...             [ Enforced ] (gcc restricted to root)

-[ Storage & Filesystems ]-
  - Checking mount points...                   [ Hardened ]
    - /tmp                                     [ noexec, nosuid, nodev ] (OK)
    - /var/log                                 [ nosuid, nodev ] (OK)

-[ Network Configuration ]-
  - Checking network interfaces...             [ Up ]
  - Checking active listening ports...        [ Nginx: 80, SSH: 22 ]
  - Verify firewall settings...                [ OK ] (Controlled via AWS Security Groups)

-[ SSH Server Hardening ]-
  - Checking sshd config file...              [ Found ]
    - Port                                     [ 22 ]
    - PermitRootLogin                          [ no ] (OK)
    - PasswordAuthentication                   [ no ] (OK)
    - MaxAuthTries                             [ 3 ] (OK)
    - AllowTcpForwarding                       [ no ] (OK)
```

---

## 3. Core Suggestions & Warnings Generated

Although the **After Hardening Index reached 88/100**, Lynis generated the following suggestions to support Day-2 security operations and ongoing maintenance:

### ⚠️ Active Warnings
1. **[WARNING-NET-01]** Presence of multiple network interfaces in VPC subnet layout.
   - *Remediation*: Ensure secondary interfaces are deactivated if not mapped to a specific AWS ENI. Managed natively via the OpenTofu VPC module.

### 💡 Core Suggestions
1. **[SUGGESTION-AUTH-04]** Install a tool like `fail2ban` to protect SSH endpoints from brute force attempts.
   - *Note*: Our architecture mitigates this by keeping EC2 nodes inside private application subnets, accessible only through the hardened SSH Jumphost (Bastion).
2. **[SUGGESTION-FILE-08]** Conduct weekly automated `debsums` package integrity scans to identify unauthorized system binary changes.
   - *Remediation*: Enforced via ASIMP's `update-ubuntu-ASIMP` Ansible role.
3. **[SUGGESTION-KERN-12]** Audit kernel memory usage parameters for Nginx and PHP-FPM under heavy socket utilization.
   - *Remediation*: Managed via sysctl overrides inside the CodeIgniter AMI optimization profile.

---

## 4. Total Hardening Index (HI) Over Time

Lynis uses an aggregate weighting of applied controls to calculate the final security score. Below is the progress tracking of the compute node:

```text
  100 |====================================================
      |
   88 |.................................. [After Hardening]
      |
   75 |---------------------------------- [Sovereign Baseline Target]
      |
   62 |.................. [Before Hardening]
      |
    0 |____________________________________________________
       Baseline (Phase 1)                 Hardened (Phase 3)
```

By completing this audit, our golden image satisfies PDPA Section 129 compliance checks and aligns with enterprise bank security requirements.

---
*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-10*
