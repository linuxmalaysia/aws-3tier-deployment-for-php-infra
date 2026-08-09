---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "OpenTofu Migration & AWS Support Research Guide"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier", "opentofu", "migration"]
---

**[DEVOPS EXECUTION]**

# OpenTofu Migration & AWS Support Research Guide

This document presents a comprehensive feasibility study, architectural research, and practical migration path for transitioning our AWS 3-Tier Infrastructure configuration from **HashiCorp Terraform** to **OpenTofu**.

OpenTofu is a production-ready, open-source infrastructure-as-code (IaC) tool under the governance of the Linux Foundation (part of the Cloud Native Computing Foundation - CNCF). It was spawned as a community-driven fork of Terraform following its transition to the Business Source License (BSL).

---

## 1. Executive Summary

- **High Compatibility:** OpenTofu serves as a drop-in replacement for Terraform configurations (especially those compatible with Terraform 1.5.x, which this project uses with its `>= 1.5.0` requirement).
- **Zero AWS Resource Impact:** Migrating the deployment engine from `terraform` to `tofu` does not affect currently running AWS resources (such as VPCs, ALBs, ASGs, WAFv2, or RDS).
- **Same AWS API Calls:** Both engines utilize the standard AWS Provider which translates declarative configuration into AWS API calls using the AWS SDK for Go.
- **Enhanced Open Source Features:** OpenTofu offers advanced features like client-side state encryption, improved variable handling, and native resource exclusion (`tofu plan -exclude="..."`).

---

## 2. AWS Support and Compatibility Matrix

AWS natively supports OpenTofu indirectly and directly across its entire ecosystem, since OpenTofu acts as a client orchestrator of AWS APIs via the AWS Provider.

| AWS Feature / Service | Support Level | Technical Integration Mechanism |
| :--- | :--- | :--- |
| **AWS APIs & Resources** | **Native & Complete** | Handled seamlessly via the `hashicorp/aws` provider, which is mirrored directly in the OpenTofu Registry. All resources (VPC, WAFv2, ALB, ASG, RDS) behave identically. |
| **IAM Authentication** | **Native & Complete** | Uses standard AWS SDK Go credential resolution chain (profiles, env vars, instance profiles). |
| **OIDC / Web Identity** | **Native & Complete** | Fully supports AWS OpenID Connect (OIDC) authentication, enabling passwordless GitHub Actions runs. |
| **S3 Backend (State Storage)** | **Native & Complete** | The `s3` state backend in OpenTofu matches the Terraform S3 backend exactly, utilizing SSE, S3 Versioning, and IAM-based access. |
| **DynamoDB (State Locking)** | **Native & Complete** | Fully supports DynamoDB table state locking to prevent concurrent runs. |
| **AWS CodeBuild** | **Complete (via scripts)** | Since CodeBuild executes raw container environments, OpenTofu is fully supported. Tofu can be installed via package manager (APT/YUM) or official binary installation. |
| **AWS CodePipeline** | **Complete (via CodeBuild)** | CodePipeline orchestrates steps. Running OpenTofu within a CodePipeline pipeline is done via CodeBuild actions. |
| **AWS Proton** | **Complete (via custom runner)** | AWS Proton allows specifying custom IaC engines through custom container-based provisioning, allowing seamless execution of OpenTofu. |
| **AWS Systems Manager (SSM)** | **Supported** | Parameter Store and Secrets Manager are accessed natively via data sources or backend credential configurations. |

---

## 3. AWS Authentication Integration

OpenTofu inherits the exact same credential chain precedence as the AWS SDK and AWS CLI:

1. **Static Credentials:** Environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN`.
2. **Shared Config & Credentials Files:** Located at `$HOME/.aws/config` and `$HOME/.aws/credentials` (leveraging `AWS_PROFILE`).
3. **Web Identity / OIDC Tokens:** Loaded via `AWS_WEB_IDENTITY_TOKEN_FILE` and `AWS_ROLE_ARN`. This is crucial for secure, keyless execution in **GitHub Actions** and **AWS EKS / ECS**.
4. **ECS Task Roles / Container Credentials:** Loaded using `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI`.
5. **EC2 Instance Profile Metadata:** Evaluated when running directly on an EC2 instance (e.g., inside an administrative workstation or bastion host).

---

## 4. State Management and S3 Backend

OpenTofu's S3 state backend is completely compatible with Terraform's backend. The configuration remains virtually identical:

```hcl
terraform {
  backend "s3" {
    bucket         = "my-opentofu-state-bucket"
    key            = "state/terraform.tfstate"
    region         = "ap-southeast-5"
    dynamodb_table = "my-opentofu-lock-table"
    encrypt        = true
  }
}
```

> **Note:** OpenTofu accepts the `terraform` configuration block for backward compatibility. There is no need to rename this block to `tofu` in your `.tf` files.

### State Migration Safeties:
- Before running OpenTofu on an existing Terraform-managed deployment, create a backup of your S3 state file:
  ```bash
  aws s3 cp s3://my-opentofu-state-bucket/state/terraform.tfstate ./terraform.tfstate.backup
  ```
- Running `tofu init` will recognize the existing state file and integrate with it natively.

---

## 5. Command Mapping

OpenTofu is designed with direct CLI command parity to make the transition trivial for developers:

| Terraform Command | OpenTofu Equivalent | Purpose |
| :--- | :--- | :--- |
| `terraform init` | `tofu init` | Initializes directories, downloads providers/modules |
| `terraform fmt` | `tofu fmt` | Automatically formats configuration files |
| `terraform validate` | `tofu validate` | Checks configuration semantics and syntax |
| `terraform plan` | `tofu plan` | Outputs execution plan of pending AWS updates |
| `terraform apply` | `tofu apply` | Executes updates against active AWS APIs |
| `terraform destroy` | `tofu destroy` | Destroys all provisioned resources securely |
| `terraform state <subcmd>`| `tofu state <subcmd>` | Inspects or alters local/remote state records |
| `terraform import` | `tofu import` | Imports existing AWS resources into the state |

### Advanced OpenTofu Commands:
- **Excluding Resources Dynamically:**
  ```bash
  tofu plan -exclude="module.rds"
  tofu apply -exclude="module.rds"
  ```
  *(Terraform only supports targeting specific resources via `-target`, whereas OpenTofu supports negative targeting with `-exclude`).*

---

## 6. How to Run OpenTofu in AWS Environments

### A. AWS CodeBuild Integration
To run OpenTofu in an AWS CodeBuild environment, include the following in your `buildspec.yml`:

```yaml
version: 0.2

phases:
  install:
    commands:
      # Install OpenTofu repository and binary
      - curl -s https://get.opentofu.org/install/opentofu-install.sh -o opentofu-install.sh
      - chmod +x opentofu-install.sh
      - ./opentofu-install.sh --install-method standalone
      - tofu --version
  pre_build:
    commands:
      - cd terraform
      - tofu init -backend-config="bucket=${STATE_BUCKET}"
  build:
    commands:
      - tofu plan -out=tfplan
  post_build:
    commands:
      - echo "Build completed on `date`"
```

### B. AWS CodePipeline Integration
AWS CodePipeline does not have a dedicated action type for OpenTofu or Terraform out of the box. However, the standard best practice is to use **AWS CodeBuild** as a pipeline stage:
1. **Source Stage:** Code is retrieved from AWS CodeCommit, GitHub, or Amazon S3.
2. **Build Stage (CodeBuild):** CodeBuild installs and runs OpenTofu to generate an execution plan (`tofu plan`).
3. **Approval Stage (Optional):** Manual approval step inside CodePipeline to verify the plan.
4. **Deploy Stage (CodeBuild):** CodeBuild applies the plan (`tofu apply tfplan`).

### C. AWS Proton Integration
AWS Proton coordinates infrastructure provisioning. For teams wanting to use OpenTofu:
1. Register a **Custom Provisioning** template.
2. Configure Proton to run an AWS CodeBuild project.
3. In the CodeBuild project, fetch the OpenTofu CLI and execute standard plan and apply commands mapped to the Proton service input schema.

---

## 7. Execution and Migration Plan for this Repository

To fully execute this replacement in this codebase, we perform the following steps:
1. **Report & Documentation:** Write this comprehensive guide (`docs/opentofu-migration.md`) and register it in the main Jekyll configuration and index (`docs/index.md`).
2. **Scripts Migration:** Modify CLI helpers `scripts/deploy.sh` and `scripts/destroy.sh` to transition to `tofu` while maintaining safety structures.
3. **GitHub Actions CI/CD Migration:** Update `.github/workflows/terraform.yml` to rename it to `opentofu.yml`, using the official `opentofu/setup-opentofu@v1` runner to ensure native, secure plan/apply on pushes.
4. **General References Refactoring:** Replace Terraform terminology and setup notes in `README.md`, `docs/engineering/scripts.md`, and `docs/engineering/cicd.md` with OpenTofu standards.
