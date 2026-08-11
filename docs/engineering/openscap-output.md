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

Within ASIMP, OpenSCAP evaluates the system against the **CIS Benchmarks Level 2 (Server) Profile** customized for the specific operating system, offering deep, standardized testing of kernel variables, package versions, and system permissions across both Debian and RHEL platform families.

---

## 1. OpenSCAP Scan Specifications

- **Scanning Tool**: OpenSCAP Scanner (command-line utility `oscap`)
- **Selected Profile**: `xccdf_org.ssgproject.content_profile_cis_level2_server` (revision: `0.1.72`, content version: `0.1.72`)
- **DataStream XML Source**: Dynamic SSG DataStream (`ssg-ubuntu2404-ds.xml` for Ubuntu 24.04/26.04 LTS, `ssg-debian12-ds.xml` for Debian 12, or the corresponding RHEL content datastreams).
- **Evaluation Baseline Target**: CIS Benchmarks Level 2 Compliance
- **Compliance Score Before Hardening**: `58.4%` (FAIL)
- **Compliance Score After Hardening**: `91.2%` (PASS - Target: `90.0%+`)
- **Scope Notice**: The results and report traces presented below represent illustrative, unverified, and simulated examples of host-level security audits. Any system configurations or results are strictly mock data designed for demonstration, test verification, and review purposes, and are not linked to live production execution provenance.

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

### Detailed Evaluation Calculations:

- **Denominator (Evaluated Rules)**: `314` applicable rules (excluding hardware modules, partition-level mount controls, or systemd-networkd rules skipped due to virtualized AWS EC2 constraints).
- **Numerator (Compliant Rules)**: `286` compliant rules (comprising `260` rules passed initially and `26` rules successfully remediated/fixed by ASIMP).
- **Rule Scoring formula**: Unweighted rule count compliance is `(Pass + Fixed) / Denominator = 286 / 314` yielding exactly `91.08%`.
- **Weighted Compliance Score**: Under the weighted OpenSCAP scoring algorithm (configured via content version `0.1.72` where high-severity rules are weighted higher), the weighted score calculates to exactly **91.2%**.

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

- **OVAL Database**: Dynamic OS-matched vulnerability definitions feed:
  - **Ubuntu 24.04 LTS**: Canonical USN OVAL feed (`com.ubuntu.noble.usn.oval.xml`)
  - **Debian 11 & Debian 12**: Debian Security Tracker OVAL feed (`oval-definitions-debian.xml`)
  - **RHEL 9 / AlmaLinux 9 / Rocky Linux 9 / Oracle Linux 9**: Red Hat Security Data API OVAL feed (`com.redhat.rhsa-RHEL9.xml`)
- **Tested Packages**: 180 (Nginx, PHP, OpenSSL, systemd, etc.)
- **Security Vulnerabilities Identified**: `0` (within the scope of known vulnerabilities covered by the respective OS-matched OVAL feed)
- **Status**: **Fully patched against OS-matched OVAL feed definitions**

---

## 5. Automated Remediation Shell Script

A key benefit of OpenSCAP in the ASIMP workflow is the dynamic generation of a standalone, target-specific shell script (such as the Ubuntu-only `remediate-noble-latest.sh` shown below, representing an Ubuntu 24.04/26.04 Noble target) containing exact fix guidelines. Remediations are dynamically compiled by ASIMP using target-matched package managers and service identifiers (e.g., restarting `ssh` for Ubuntu/Debian vs. `sshd` for RHEL-family or Amazon Linux 2023):

```bash
#!/bin/bash
# OpenSCAP generated bash remediation script for CIS Level 2 Profile
# Generated on: 2026-08-10

# Enable strict failure handling
set -euo pipefail

# Rule: Enable tcp_syncookies (idempotent sysctl update with optional indentation and value checks)
sysctl -q -n -w net.ipv4.tcp_syncookies=1
SYSCTL_CONF="/etc/sysctl.d/99-asimp-hardening.conf"
if grep -qE "^\s*net\.ipv4\.tcp_syncookies\s*=" "$SYSCTL_CONF" 2>/dev/null; then
    # If the active assignment exists but does not have value 1, replace it
    if ! grep -qE "^\s*net\.ipv4\.tcp_syncookies\s*=\s*1\s*$" "$SYSCTL_CONF" 2>/dev/null; then
        sed -i 's/^\s*net\.ipv4\.tcp_syncookies\s*=.*/net.ipv4.tcp_syncookies = 1/' "$SYSCTL_CONF"
    fi
else
    # Append if absent
    echo "net.ipv4.tcp_syncookies = 1" >> "$SYSCTL_CONF"
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

## 6. Enterprise Red Hat and Debian Family Support (RHEL, AlmaLinux, Rocky Linux, Oracle Linux, Debian, and Ubuntu)

ASIMP provides complete scanning portability across both major operating system families by dynamically loading the corresponding SCAP Security Guides (SSGs) from `/usr/share/xml/scap/ssg/content/`:

### Debian-derived Family
- **Ubuntu 24.04 & 26.04 LTS**: `ssg-ubuntu2404-ds.xml` / `ssg-ubuntu2404-ds.xml`
- **Debian 11 & Debian 12**: `ssg-debian11-ds.xml` / `ssg-debian12-ds.xml`

### RHEL-derived Family
- **RHEL 9 & RHEL 10**: `ssg-rhel9-ds.xml` / `ssg-rhel10-ds.xml`
- **AlmaLinux 9 & AlmaLinux 10**: `ssg-almalinux9-ds.xml` / `ssg-almalinux10-ds.xml`
- **Rocky Linux 9 & Rocky Linux 10**: `ssg-rocky9-ds.xml` / `ssg-rocky10-ds.xml`
- **Oracle Linux 9 & Oracle Linux 10**: `ssg-ol9-ds.xml` / `ssg-ol10-ds.xml`

- **Selected Profile**: `xccdf_org.ssgproject.content_profile_cis_level2_server` (for standard enterprise CIS compliance) or `xccdf_org.ssgproject.content_profile_ospp` for operating system protection.
- **Portability Layer**: ASIMP dynamically translates target operating system facts (`ansible_distribution` and `ansible_distribution_major_version`) to execute matching kernel-level sysctl hardened baselines, compiler permission lockdowns, and SSH server constraints across both Debian-derived and RHEL-derived platform families.

---
*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-10*
