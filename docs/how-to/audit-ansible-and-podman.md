---
layout: default
okf_version: "0.1"
type: "How-To Guide"
title: "Auditing Ansible and Podman Configurations"
timestamp: "2026-08-05T22:30:00+08:00"
topics: ["how-to", "audit", "ansible", "podman", "security", "linter"]
---

# Auditing Ansible and Podman Configurations


This how-to guide explains how to audit and lint your Ansible playbooks and Podman Quadlet systemd configurations using our built-in dependency-free Python static analysis engines.

---


## How to Audit Ansible Playbooks for Security


Our custom playbook scanner validates that your automation tasks conform to security hardening policies—namely protecting passwords and preventing overly permissive file permission modifications.


### Step 1: Run the standard static analysis suite


To verify all current configurations, run the test runner from the repository root:

```bash
python3 -m unittest tests/test_ansible_playbooks.py
```


### Step 2: Remediate Ansible playbook violations


If the scanner flags a playbook task, here is how you fix it:


#### Problem 1: Plaintext Hardcoded Password

```yaml
# VIOLATION: Exposed plaintext password string
vars:
  db_password: "my_insecure_database_password_123"
```

**Remediation:** Always reference secrets using safe Jinja template structures:

```yaml
# SECURE: Secure reference to dynamic/vaulted variables
vars:
  db_password: "{{ vaulted_db_password }}"
```


#### Problem 2: World-Writable File Permissions

```yaml
# VIOLATION: Group and other write bits are active
- name: Configure app permissions
  ansible.builtin.file:
    path: /etc/app_config.ini
    mode: '0666'
```

**Remediation:** Lockdown file permissions to restricted values:

```yaml
# SECURE: Restricted octal permission setting
- name: Configure app permissions
  ansible.builtin.file:
    path: /etc/app_config.ini
    mode: '0600'
```

---


## How to Audit Podman Container and Quadlet Configurations


For self-hosted container instances on on-premises comparisons (using Podman 5+), our systemd Quadlet linter audits container files (`.container`) to enforce unprivileged execution and isolate container environments.


### Step 1: Run the Podman configuration audits


To perform a full static check of your container configurations:

```bash
python3 -m unittest tests/test_podman_containers.py
```


### Step 2: Remediate Podman container violations


If the linter reports a container configuration failure, apply these fixes:


#### Problem 1: Disabling Security Label Separation

```ini
# VIOLATION: Disables SELinux label separation
[Container]
SecurityLabelDisable=true
```

**Remediation:** Remove this key or set it to false so standard SELinux security context rules are active:

```ini
# SECURE: Security separation is active
[Container]
ReadOnly=true
NoNewPrivileges=true
```


#### Problem 2: Running Containers as Root

```ini
# VIOLATION: Container running as root
[Container]
User=root
```

**Remediation:** Explicitly declare a non-root User ID:

```ini
# SECURE: Running as a non-privileged user
[Container]
User=1000:1000
```


#### Problem 3: Mounting the Host Socket

```ini
# VIOLATION: Exposing the daemon socket to the container
[Container]
Volume=/var/run/docker.sock:/var/run/docker.sock
```

**Remediation:** Never mount daemon sockets inside your application tier containers. Remove the volume directive.
