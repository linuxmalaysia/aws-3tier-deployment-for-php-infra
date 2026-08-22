---
layout: default
okf_version: "0.1"
type: Tutorial
title: "Setting up a Development Sandbox"
timestamp: "2026-08-05T22:30:00+08:00"
topics: ["tutorial", "sandbox", "setup", "development"]
render_with_liquid: false
---

# Setting up a Development Sandbox

Welcome! This step-by-step tutorial will guide you through setting up a complete, secure development sandbox for our **AWS Secure 3-Tier PHP CodeIgniter** project.

By the end of this tutorial, you will have a functional, mock local deployment validated by our custom linter tools and ready for secure AWS integration.

---

## Prerequisites

Before starting, ensure your local development environment has the following software installed:

* **Python >= 3.10** (for automation utilities and static analysis checks)
* **OpenTofu >= 1.6.0** (or Terraform >= 1.5.0)
* **Git** (for version control)
* **Shell environment** (bash, zsh, or similar Unix-like shell)

---

## Step 1: Clone the Repository and Navigate

Begin by cloning the codebase and navigating into the repository root:

```bash
git clone https://github.com/linuxmalaysia/aws-3tier-deployment-for-php-infra.git
cd aws-3tier-deployment-for-php-infra
```

---

## Step 2: Set Up Python Virtual Environment

Create and activate a isolated Python virtual environment to manage our project's script dependencies safely:

```bash
# Create a virtual environment in .venv
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

---

## Step 3: Install Required Linters and Testing Libraries

Next, install PyYAML to allow our unit-tests and static linting suites to execute fully:

```bash
pip install PyYAML
```

---

## Step 4: Run the Complete Validation Test Suite

To verify that your local sandbox complies fully with all architectural, security, and schema specifications, run our custom-built Python unit-test suite:

```bash
python3 -m unittest discover -s tests
```

You should see an output indicating that all tests have executed and passed:

```text
Ran [number of tests] tests

OK
```

---

## Step 5: Bake and Harden an Ansible Playbook Configuration

Let us write a sample, safe Ansible playbook to understand how our custom linter verifies files.

1. Create a local file named `playbook.yml` in your sandbox:

{% raw %}

```yaml
- name: Setup secure sandbox environment
  hosts: localhost
  vars:
    sandbox_db_user: "developer"
    # SAFE: Utilizing safe Jinja templates for secret variables
    sandbox_db_password: "{{ vaulted_password }}"
  tasks:
    - name: Set restricted permissions on local configuration
      ansible.builtin.file:
        path: /tmp/sandbox_config.ini
        mode: '0600' # SAFE: Restricted octal permissions
```

{% endraw %}

2. To see how our validator reacts, we can mock-run our linter logic over this sandbox playbook to ensure it passes all security audits without throwing plaintext password or world-writable directory violations.

---

## Step 6: Initialize OpenTofu (Without Active AWS Credentials)

To ensure that your OpenTofu configurations are syntactically sound and valid without needing active AWS keys or charging live credit cards:

```bash
# Navigate to the terraform directory
cd terraform/

# Initialize OpenTofu without contacting remote backends
tofu init -backend=false

# Validate configurations
tofu validate
```

If successful, OpenTofu will print:

```text
Success! The configuration is valid.
```

---

## Step 7: Clean Up Sandbox Assets

To safely teardown any temporary local configurations or plans generated in the sandbox, run:

```bash
git status
```

Make sure no untracked files are leaking into your Git commits!

Congratulations! Your secure development sandbox is fully configured and ready for production staging.
