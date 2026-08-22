---
layout: default
okf_version: "0.1"
type: "Technical Reference"
title: "Static Analysis Audit Rules"
timestamp: "2026-08-05T22:30:00+08:00"
topics: ["reference", "audit", "linter", "rules", "specifications"]
---

# Static Analysis Audit Rules


This document outlines the detailed specifications, parameters, and rejection criteria enforced by our built-in static analysis engines inside `tests/test_ansible_playbooks.py` and `tests/test_podman_containers.py`.

---


## 1. Ansible Playbook Auditing Rules


Our Ansible static analysis engine parses YAML playbooks structurally and scans task lists against secure host compliance policies.


### Password Plaintext Exposure Check


The auditor scans all declared host-level and play-level variables inside `vars` blocks.

* **Trigger Variable Names:** Any variable containing the substring `password` (case-insensitive).
* **Allowed Format:** Must be a secure Jinja template reference fully enclosed in braces:

  ```text
  {{ my_secure_password }}
  ```

* **Rejection Criteria:** Rejects and flags any string that:
  1. Contains a plaintext literal value (e.g., `"super_secret_password_123"`).
  2. Features an incomplete/unmatched brace expression (e.g., `"secret{{"`).


### File Permission Mode Check


The auditor inspects file and template creation tasks (like `ansible.builtin.file`, `ansible.builtin.template`, etc.) containing the `mode` parameter.

* **Rejection Criteria:** Flags any octal or symbolic modes that enable **group-write** or **other-write** bits.
* **Prohibited Octal Modes:**
  - `0666` (Read/Write for everyone)
  - `0766` (Read/Write/Execute for group and others)
  - `777` (Full control for everyone)
* **Prohibited Symbolic Rules:**
  - Symbolic rules with `+w`, `=w`, or `=rw` targeting groups (`g`), others (`o`), or all (`a`, or implicit).
  - Examples: `o+w`, `a+w`, `g+rw`, `o+rw`, `g=rw`, `a=rw`, `+w`.
* **Approved Standard Permissive Modes:**
  - `0600` / `600` (Owner Read/Write only)
  - `0640` / `640` (Owner Read/Write, Group Read only)
  - `0750` / `750` (Owner Read/Write/Execute, Group Read/Execute)

---


## 2. Podman Container & Quadlet Auditing Rules


Our Podman static analysis engine parses systemd Quadlet container files (`.container`) to enforce unprivileged container profiles and kernel namespace separation.


### Privileged Execution Rule


Ensures that no containers run with elevated host-level kernel permissions.

* **Prohibited Key:** `Privileged=true`
* **Secure Profile Expectation:** `Privileged` must be set to `false`, or omitted entirely.


### Root-Less Execution Rule


Enforces container user namespace isolation by blocking execution as the host root user.

* **Prohibited Key:** `User=root`
* **Secure Profile Expectation:** Must explicitly declare a non-root User ID (e.g. `User=1000:1000`).


### Dangerous Socket Mount Rule


To prevent container breakout exploits and daemon compromise, volume mounting of host container engine sockets is strictly blocked.

* **Prohibited Volume Bindings:** Any paths matching `docker.sock` or `podman.sock`.
* **Secure Profile Expectation:** Containers must handle tasks via HTTP APIs or internal networking, never by exposing local engine sockets.


### Security Label Separation Rule


Audits systemd Quadlet parameters to confirm that SELinux or AppArmor labels are active.

* **Prohibited Key:** `SecurityLabelDisable=true`
* **Secure Profile Expectation:** Key must be set to `false`, or omitted entirely. If duplicate `SecurityLabelDisable` keys are declared where a later declaration evaluates to `true`, the file is immediately rejected.
