---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "Automation Scripts"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier"]
---

**[DEVOPS EXECUTION]**

# Automation Scripts

The project includes CLI helper scripts and bootstrapping scripts under the `scripts/` directory to automate common tasks, local testing, and instance provisioning.

---

## 1. Local Deployment Script (`scripts/deploy.sh`)

This script automates the full lifecycle of a local OpenTofu deployment. It performs validation and planning checks before prompting the user for confirmation to apply.

### Steps Executed:
1. **OpenTofu Installation Check:** Verifies that the `tofu` CLI is installed and available in the execution path.
2. **Directory Context:** Changes the working directory to `terraform/`.
3. **Environment Configuration Check:** Checks if `terraform.tfvars` exists. If not, it copies it from `terraform.tfvars.example` and prompts the user to review.
4. **Initialization (`tofu init`):** Downloads required providers and module configurations.
5. **Format Verification (`tofu fmt`):** Formats all configuration files recursively to match canonical HCL syntax.
6. **Validation (`tofu validate`):** Verifies syntax correctness and internal variable consistency.
7. **Execution Planning (`tofu plan`):** Generates a secure plan file `tfplan`.
8. **User Confirmation Prompt:** Asks `Do you want to apply this deployment? (y/n)`. If `y`, it runs `tofu apply tfplan`.

---

## 2. Infrastructure Teardown Script (`scripts/destroy.sh`)

This script provides a clean and automated way to destroy all resources managed by OpenTofu, preventing accidental dangling resources or billing charges.

### Steps Executed:
1. **OpenTofu Installation Check:** Verifies that the `tofu` CLI is installed and available.
2. **Initialization:** Confirms that OpenTofu has been initialized and that `.terraform` config exists.
3. **Resource Destruction (`tofu destroy`):** Prompts the user to confirm the termination of all resources. Once confirmed, it cleanly removes all VPC components, load balancers, database clusters, auto-scaling groups, and WAF rules.

---

## 3. Instance Bootstrapping Script (`scripts/user_data.sh`)

This is a standalone bootstrapping script for EC2 instances. It can be used for custom instance images or standalone EC2 deployment tests.

### Features:
- Updates the operating system packages.
- Installs and configures an Apache HTTP web server.
- Fetches Instance Metadata Service v2 (IMDSv2) security tokens dynamically.
- Retrieves instance metadata, including the Instance ID and host Availability Zone, displaying this dynamic diagnostic information on a beautifully styled HTML index page.