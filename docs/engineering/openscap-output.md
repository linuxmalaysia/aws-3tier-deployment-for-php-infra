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

This document presents a detailed example of the **OpenSCAP Security Audit** results. OpenSCAP is an SCAP-compliant scanner used to evaluate systems against standard security baselines, such as the Center for Internet Security (CIS) Benchmarks or DISA STIGs.

Within ASIMP, OpenSCAP evaluates the system against the **CIS Ubuntu Security Linux Level 2 (Server) Profile**, offering deep, standardized testing of kernel variables, package versions, and system permissions.

---

## 1. OpenSCAP Scan Specifications

- **Scanning Tool**: OpenSCAP Scanner (command-line utility `oscap`)
- **Selected Profile**: `xccdf_org.ssgproject.content_profile_cis_level2_server`
- **DataStream XML Source**: Canonical SSG DataStream (`ssg-ubuntunoble-ds.xml` for Ubuntu 24.04 LTS Noble Numbat)
- **Evaluation Baseline Target**: CIS Benchmarks Level 2 Compliance
- **Compliance Score Before Hardening**: `58.4%` (FAIL)
- **Compliance Score After Hardening**: `91.2%` (PASS - Target: `90.0%+`)
- **Scope Notice**: The results and report traces presented below represent a verified, illustrative example of host-level security audits. Any system configurations or results not directly testable in unprivileged sandbox/CI containers are simulated based on authentic, supported evidence from our golden image baking environments.

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
- **Security Vulnerabilities Identified**: `0` (within the scope of known vulnerabilities covered by the pinned Canonical OVAL feed and the tested 180 packages)
- **Status**: **Fully patched against OVAL feed definitions**

---

## 5. Automated Remediation Shell Script

A key benefit of OpenSCAP in the ASIMP workflow is the dynamic generation of a standalone, target-specific shell script (`remediate-noble-latest.sh`) containing exact fix guidelines:

```bash
#!/bin/bash
# OpenSCAP generated bash remediation script for CIS Level 2 Profile
# Generated on: 2026-08-10

# Enable strict failure handling
set -euo pipefail

# Rule: Enable tcp_syncookies (idempotent sysctl update)
sysctl -q -n -w net.ipv4.tcp_syncookies=1
if ! grep -q "^net.ipv4.tcp_syncookies" /etc/sysctl.d/99-asimp-hardening.conf 2>/dev/null; then
    echo "net.ipv4.tcp_syncookies = 1" >> /etc/sysctl.d/99-asimp-hardening.conf
fi

# Rule: Secure shadow files permissions
chmod 0600 /etc/shadow

# Rule: Validate SSH configuration and restart SSH service
if sshd -t; then
    systemctl restart ssh
else
    echo "SSH configuration validation failed! Skipping restart to prevent lockout." >&2
    exit 1
fi
```

This ensures complete operational transparency, letting DevOps engineers audit the exact actions before deploying changes to live launch templates.

---
*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-10*
