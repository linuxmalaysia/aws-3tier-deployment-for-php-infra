---
layout: default
okf_version: "0.1"
type: "Technical Reference"
title: "CLI & Scripts Reference Manual"
timestamp: "2026-08-05T22:30:00+08:00"
topics: ["reference", "cli", "scripts", "manual", "parameters"]
---

# CLI & Scripts Reference Manual

This document provides exhaustive, structured reference material detailing arguments, environments, dependencies, inputs, and outputs for every tool and automation script in this repository.

---

## 1. `scripts/deploy.sh`

A bash script coordinating pre-flight validations and deploying our AWS 3-Tier infrastructure.

* **Interpreter:** `/usr/bin/env bash`
* **Dependencies:** `tofu` CLI (OpenTofu >= 1.6.0), `bash` >= 4.0
* **Expected Inputs:**
  - File `terraform/terraform.tfvars` must exist. If missing, copies `terraform.tfvars.example` and terminates with exit code `0`.
* **Flow & Actions:**
  1. Verifies `tofu` installation.
  2. Formatting check via `tofu fmt -recursive`.
  3. Validation via `tofu validate`.
  4. Generates execution plan saved as binary file `terraform/tfplan`.
  5. Interactive approval prompt. If yes, runs `tofu apply tfplan`.
* **Exit Codes:**
  - `0`: Success (or copied example `.tfvars` file).
  - `1`: Validation failed, missing requirements, or execution failure.

---

## 2. `scripts/destroy.sh`

A bash helper script to safely teardown all AWS resources provisioned by the project.

* **Interpreter:** `/usr/bin/env bash`
* **Dependencies:** `tofu` CLI, `bash` >= 4.0
* **Expected Inputs:**
  - Initialized state database in `terraform/.terraform/`
* **Flow & Actions:**
  1. Confirms OpenTofu initialization.
  2. Prompts user for interactive confirmation.
  3. Runs `tofu destroy -auto-approve` to cleanly reclaim resources.
* **Exit Codes:**
  - `0`: Resources successfully destroyed or operation canceled by user.
  - `1`: OpenTofu not initialized, missing CLI, or deletion error.

---

## 3. `scripts/user_data.sh`

A standard cloud-init shell bootstrap script deployed inside AWS EC2 launch templates.

* **Interpreter:** `/bin/bash` with flags `set -euo pipefail`
* **Features:** Parallel background instance metadata (IMDSv2) retrieval.
* **System Support & Dependencies:**
  - **Debian/Ubuntu 24.04+ LTS:** Installs packages via `apt-get`.
  - **Amazon Linux:** Installs packages via `dnf`.
* **Created Assets:**
  - Mounts/Sockets: PHP-FPM socket path `/run/php/php<VER>-fpm.sock` or `/run/php-fpm/www.sock`.
  - Directory: Document Root `/var/www/html/codeigniter/public`.
  - Config: `/etc/nginx/sites-available/default` or `/etc/nginx/conf.d/codeigniter.conf`.
  - Application Script: `/var/www/html/codeigniter/public/index.php`.

---

## 4. `scripts/prepare_docs.py`

Python utility enforcing OKF (Open Knowledge Format) v0.1 frontmatter rules over repository Markdown documents.

* **Interpreter:** `/usr/bin/env python3`
* **Dependencies:** Standard library only (`os`, `re`, `subprocess`, `datetime`)
* **Behavior:**
  - If a file has no frontmatter, constructs a brand new block with fields: `layout`, `okf_version`, `type`, `title` (extracted from first H1), `timestamp` (Git commit metadata fallback), and `topics`.
  - If a file has existing frontmatter, merges values while preserving existing parameters and nested structures.
  - Generates array strings for `topics` wrapped with double quotes.
* **Exit Codes:**
  - `0`: All files successfully processed.
  - `1`: Structural parsing or file system validation failure.

---

## 5. `scripts/generate_sitemaps.py`

Python utility to construct sitemap and web visibility assets for Jekyll and GitBook configurations.

* **Interpreter:** `/usr/bin/env python3`
* **Dependencies:** Standard library only.
* **Configuration Target:** Base URL `https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/`.
* **Output Artifacts:**
  - `sitemap.txt`
  - `sitemap.xml`
  - `robots.txt`
  - `.well-known/security.txt`

---

## 6. `scripts/generate_llms_assets.py`

Python utility providing an API and a CLI utility (`llms_txt2ctx`) to compile LLM context files.

* **Interpreter:** `/usr/bin/env python3`
* **Dependencies:** Standard library only.
* **CLI Arguments:**
  ```text
  python3 scripts/generate_llms_assets.py [input_file] [--optional True/False]
  ```
  - `input_file`: Path to source file (usually `llms.txt`).
  - `--optional`: Include "optional" sections of `llms.txt` (Default: `False`).
* **Python API signatures:**
  - `parse_llms_file(txt)`: Parses a markdown text block and returns structured data.
  - `create_ctx(txt, optional=False, base_dir=None)`: Constructs and returns XML context.
  - `compile_llms_full(txt, base_dir=None)`: Compiles plain Markdown contents.
