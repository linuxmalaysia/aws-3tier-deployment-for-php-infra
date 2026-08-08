---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "CI/CD Pipeline Documentation"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier", "cicd", "automation"]
---

**[DEVOPS EXECUTION]**

# CI/CD Pipeline Documentation

This project includes a fully automated CI/CD pipeline configured via GitHub Actions in `.github/workflows/opentofu.yml`. It ensures that every code submission is vetted for quality, syntax correctness, and security boundaries.

---

## Pipeline Workflow Trigger Conditions

The pipeline is triggered automatically on:
- **Pull Requests** targeting the `main` branch.
- **Direct Pushes** or Merges to the `main` branch.

---

## Job Definitions

The workflow consists of three major jobs designed with security and safety gates:

### 1. OpenTofu Format and Validate (`opentofu-lint-and-validate`)
- **Environment:** `ubuntu-latest`
- **Steps:**
  - **Checkout Code:** Checks out the repository files.
  - **Setup OpenTofu:** Installs OpenTofu version `1.8.2` on the runner using `opentofu/setup-opentofu@v1`.
  - **Format Check:** Verifies formatting recursively via `tofu fmt -check -recursive`.
  - **Initialize:** Runs `tofu init -backend=false` to configure modules locally.
  - **Validate:** Evaluates configurations for semantic validity via `tofu validate`.

### 2. OpenTofu Planning (`opentofu-plan`)
- **Trigger:** Runs only on **Pull Request** events.
- **Dependency:** Requires the `opentofu-lint-and-validate` job to pass.
- **Steps:**
  - **Configure AWS OIDC Credentials:** Authenticates securely with AWS using OpenID Connect (OIDC) through `aws-actions/configure-aws-credentials@v4` with `secrets.AWS_ROLE_TO_ASSUME` and `secrets.AWS_REGION`.
  - **OpenTofu Init & Plan:** Performs complete backend initialization and generates an execution plan showing what changes will be applied.

### 3. OpenTofu Deployment (`opentofu-apply`)
- **Trigger:** Runs only on **Pushes** or Merges to the `main` branch.
- **Dependency:** Requires the `opentofu-lint-and-validate` job to pass.
- **Steps:**
  - **Configure AWS OIDC Credentials:** Authenticates securely with AWS using OIDC.
  - **OpenTofu Init & Apply:** Runs `tofu apply -auto-approve` to deploy the target infrastructure.

---

## Secret Management Best Practices

The pipeline utilizes modern security standards:
- **No Hardcoded Credentials:** Leverages short-lived, dynamically-exchanged AWS security tokens via OIDC instead of storing long-lived `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` secrets.
- **Configurable Region:** Adapts automatically based on `secrets.AWS_REGION` or defaults gracefully to `us-east-1` (or local regional default config).