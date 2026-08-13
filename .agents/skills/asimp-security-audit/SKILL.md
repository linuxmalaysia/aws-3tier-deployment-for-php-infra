---
layout: default
okf_version: "0.1"
type: "Agent Skill"
title: "Ansible & Systems Hardening Audit (ASIMP) Skill"
timestamp: "2026-08-13T12:00:00+08:00"
topics: ["security", "asimp", "ansible", "audit", "compliance"]
name: asimp-security-audit
description: "Encapsulates guidelines and procedures for system integrity management, host-level security audits, compliance reporting, and static analysis verification."
---

# Ansible & Systems Hardening Audit (ASIMP) Skill

This custom agent skill incorporates all knowledge, standards, and static validation processes for server hardening, Ansible automation auditing, and system-level compliance.

## When to Use This Skill
- Use this when modifying, testing, or reviewing Ansible playbooks or Podman/systemd Quadlet configurations.
- Use this when verifying security reports (`asimp-output.md`, `lynis-output.md`, `openscap-output.md`) or performing SPA checklist updates.
- Use this when writing or modifying static analysis testing suites under `tests/`.

## How to Use It (Procedures and Conventions)

### 1. ASIMP Integration with AI Agents (DSOM)
- Integration is guided by `docs/engineering/asimp-for-ai-agents.md` under the visual tag **[SECURITY & COMPLIANCE]**.
- AI Agents must adhere to the 5-Step Local Knowledge-First Discovery Protocol before modifying systems or running exploratory shell actions.
- Avoid context window amnesia or token bloat by utilizing the "Artifact Pyramid" to reference synthesized scorecards first before drilling down to raw logs.

### 2. Static Analysis Rules & Hardening
- **Ansible Playbook Verification (`tests/test_ansible_playbooks.py`):** Uses a custom, dependency-free scanner to enforce secure configs. It flags hardcoded plaintext passwords missing Jinja expression brackets, and audits file permission modes (e.g., rejecting group- and other-write permissions like 0666 or 0766).
- **Podman Container Auditing (`tests/test_podman_containers.py`):** Validates rootless container executions, volume mounts, and systemd Quadlet container directives. Crucially, any configuration that disables container security label separation (e.g., `SecurityLabelDisable=true`) is flagged and rejected as insecure.

### 3. Dual-Engine Compliance Auditing
- Detailed reports for the ASIMP platform, Lynis host audits, and OpenSCAP compliance checks are maintained as `asimp-output.md`, `lynis-output.md`, and `openscap-output.md` under `docs/engineering/`.
- Ensure they are registered in `docs/index.md` inside a dedicated section titled `### Security Hardening & Compliance Reports (ASIMP)` and indexed inside `llms.txt`.

### 4. Cross-Family OS Support
- Systems support both Debian-derived (Ubuntu 24.04 LTS, Ubuntu 26.04 LTS, Debian 11, Debian 12) and RHEL-derived (RHEL 9, RHEL 10, AlmaLinux 9, AlmaLinux 10, Rocky/Oracle Linux 9 & 10) families.
- Always specify correct socket locations, config structures, and package managers for each family in system-level automation scripts.

---
*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-13*
