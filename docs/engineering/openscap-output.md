---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "OpenSCAP Security Audit Output Report"
timestamp: 2026-08-10T23:30:00+08:00
topics: ["security", "compliance", "audit", "report", "openscap"]
---

**[SECURITY & COMPLIANCE]**

# OpenSCAP Security Audit Output Report

This document presents a detailed example of the **OpenSCAP Security Audit** results. OpenSCAP is a NIST-certified scanner used to evaluate systems against standard security baselines, such as the Center for Internet Security (CIS) Benchmarks or DISA STIGs.

Within ASIMP, OpenSCAP evaluates the system against the **CIS Ubuntu Security Linux Level 2 (Server) Profile** (or equivalent RedHat SSG profiles), offering deep, standardized testing of kernel variables, package versions, and system permissions.

---

## 1. OpenSCAP Scan Specifications

- **Scanning Tool**: OpenSCAP Scanner (command-line utility `oscap`)
- **Selected Profile**: `xccdf_org.ssgproject.content_profile_cis_level2_server`
- **DataStream XML Source**: Canonical SSG DataStream (`ssg-ubuntunoble-ds.xml` or Noble Successor)
- **Evaluation Baseline Target**: CIS Benchmarks Level 2 Compliance
- **Compliance Score Before Hardening**: `58.4%` (FAIL)
- **Compliance Score After Hardening**: `91.2%` (PASS - Target: `90.0%+`)

---

## 2. Rule Evaluation & Compliance Results

The scan checks over 300 rules on the target host. Below is a categorized summary representing the rule results under our hardened environment:

### Subsystem Compliance Summary Table

| Security Control Area | Tested Rules | Pass | Fail | Fixed (Remediated) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Filesystem Integrity** | 45 | 43 | 0 | 2 | ✅ Compliant |
| **System Account Restrictions** | 30 | 30 | 0 | 0 | ✅ Compliant |
| **PAM & Password Configuration** | 25 | 23 | 0 | 2 | ✅ Compliant |
| **SSH Server Security** | 20 | 18 | 0 | 2 | ✅ Compliant |
| **System Logging (Auditd)** | 35 | 32 | 0 | 3 | ✅ Compliant |
| **Network Parametric sysctl** | 15 | 13 | 0 | 2 | ✅ Compliant |

---

## 3. Selected Rule Verification Logs

Below is a detailed trace of critical rules evaluated during the scanning cycle:

### Rule 1: Ensure root login over SSH is disabled
- **Rule ID**: `xccdf_org.ssgproject.content_rule_sshd_disable_root_login`
- **Severity**: High
- **Baseline Evaluation**: `FAIL` (PermitRootLogin was set to yes)
- **Remediation Action**: ASIMP modified `/etc/ssh/sshd_config` to `PermitRootLogin no`.
- **Re-Measure Evaluation**: `PASS` (Status: **Fixed**)

### Rule 2: Enforce file permission boundaries on shadow files
- **Rule ID**: `xccdf_org.ssgproject.content_rule_file_permissions_etc_shadow`
- **Severity**: Medium
- **Baseline Evaluation**: `FAIL` (Shadow file had permissions of `0644`)
- **Remediation Action**: Enforced permission set `0600` on `/etc/shadow`.
- **Re-Measure Evaluation**: `PASS` (Status: **Fixed**)

### Rule 3: Enforce TCP SYN flood protection (sysctl)
- **Rule ID**: `xccdf_org.ssgproject.content_rule_sysctl_net_ipv4_tcp_syncookies`
- **Severity**: Medium
- **Baseline Evaluation**: `FAIL` (tcp_syncookies set to 0)
- **Remediation Action**: Added `net.ipv4.tcp_syncookies = 1` inside `/etc/sysctl.d/99-asimp-hardening.conf`.
- **Re-Measure Evaluation**: `PASS` (Status: **Fixed**)

---

## 4. OVAL Vulnerability Assessment

In addition to compliance profiles, ASIMP runs an OVAL (Open Vulnerability and Assessment Language) scan using Canonical's official Ubuntu Security Notices (USN) database definitions:

- **OVAL Database**: `com.ubuntu.noble.usn.oval.xml`
- **Tested Packages**: 180 (Nginx, PHP, OpenSSL, systemd, etc.)
- **Security Vulnerabilities Identified**: `0`
- **Status**: **Fully Patched & Non-Vulnerable**

---

## 5. Automated Remediation Shell Script

A key benefit of OpenSCAP in the ASIMP workflow is the dynamic generation of a standalone, target-specific shell script (`remediate-noble-latest.sh`) containing exact fix guidelines:

```bash
#!/bin/bash
# OpenSCAP generated bash remediation script for CIS Level 2 Profile
# Generated on: 2026-08-10

# Rule: Enable tcp_syncookies
sysctl -q -n -w net.ipv4.tcp_syncookies=1
echo "net.ipv4.tcp_syncookies = 1" >> /etc/sysctl.d/99-asimp-hardening.conf

# Rule: Secure shadow files permissions
chmod 0600 /etc/shadow

# Rule: Restart SSH service to apply configurations
systemctl restart ssh
```

This ensures complete operational transparency, letting DevOps engineers audit the exact actions before deploying changes to live launch templates.

---
*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-10*
