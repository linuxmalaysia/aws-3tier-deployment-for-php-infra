---
layout: default
okf_version: "0.1"
type: Portal
title: "AWS 3-Tier Deployment for PHP CodeIgniter Web Application (with OpenTofu)"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier"]
---

# AWS 3-Tier Deployment for PHP CodeIgniter Web Application (with OpenTofu)

Welcome to the **AWS 3-Tier Deployment for PHP CodeIgniter Web Application** repository. This is an enterprise-grade, highly available, secure, and cost-optimized infrastructure project. It is natively deployed using **OpenTofu** and targeted at the **AWS Asia Pacific (Malaysia) region (`ap-southeast-5`)** with full support for Graviton (ARM64) compute, automated pre-baked AMIs, strict security architectures, Valkey-based session stores, and custom regional compliance solutions.

This project is tailored specifically to host a production-grade **PHP application utilizing the CodeIgniter framework**, served via **Nginx and PHP-FPM**.

---

## Technical Architecture Overview

Our design is built on the **Zero-Trust Network Principle**, dividing components into distinct physical and logical layers:

```
                                [ INTERNET ]
                                     │
                                     ▼
                               [ AWS WAFv2 ]   <-- (OWASP Top 10 + IP Rate Limiting)
                                     │
                                     ▼
                       [ Application Load Balancer ]  <-- (Public Subnets)
                                     │
                       ┌─────────────┴─────────────┐
                       ▼                           ▼
                [ Frontend Nginx ]          [ Frontend Nginx ]  <-- (ASG EC2 Private Subnets)
                [    + PHP-FPM   ]          [    + PHP-FPM   ]
                       │                           │
                       └─────────────┬─────────────┘
                                     ▼
                            [ ElasticCache Valkey ]     <-- (Session Caching Layer)
                                     │
                                     ▼
                             [ Multi-AZ RDS DB ]        <-- (Isolated Database Subnets)
```

1. **Presentation / Web Tier (Public Subnets):**
   - **Application Load Balancer (ALB):** Restricts incoming requests strictly to HTTP/HTTPS.
   - **AWS WAFv2:** Filters regional requests, blocking OWASP Top-10 vulnerabilities, SQL injection attempts, and implementing active IP rate limits.
2. **Application / Compute Tier (Private Subnets):**
   - **Auto Scaling Groups (ASG):** Secure, isolated EC2 instances running hardened **Ubuntu 26.04 LTS** (Graviton ARM64 architecture) or **Amazon Linux 2023**. Direct SSH is disabled; systems are managed passwordlessly using **AWS Systems Manager (SSM)**.
   - **Nginx + PHP-FPM:** Web server and PHP FastCGI processor configured for high-performance CodeIgniter operations.
   - **Amazon ElastiCache for Valkey:** High-performance, secure, and license-compliant key-value cache layer configured for CodeIgniter session persistence and caching.
3. **Database Tier (Isolated Subnets):**
   - **Multi-AZ RDS Database:** Isolate data across multiple availability zones. Ingress is restricted exclusively to port 3306 (MySQL) or 5432 (PostgreSQL) originating from the compute tier.

---

## Repository Structure

```
.
├── .github/
│   └── workflows/
│       ├── jekyll-gh-pages.yml   # Automates python document processing & Jekyll deploy
│       └── opentofu.yml          # Format, lint, OIDC-based validation & deploy
├── docs/                         # Jekyll Document System (Source of GitHub Pages Portal)
│   ├── _layouts/                 # Jekyll theme responsive layouts
│   ├── assets/                   # Centralized stylesheets (global.css)
│   ├── modules/                  # Technical sub-specifications for every component
│   └── *.md                      # Extensive engineering guide files
├── scripts/                      # Operation and deployment utility scripts
│   ├── deploy.sh                 # Coordinates OpenTofu linting, format, validate, and plans
│   ├── destroy.sh                # Graceful deletion coordinator for provisioning
│   ├── prepare_docs.py           # Pre-build Python processor prepending front-matter
│   └── user_data.sh              # Cloud-init bootstrapping script
├── terraform/                    # Modularized Infrastructure as Code (IaC) configuration
│   ├── modules/                  # Submodules encapsulating AWS resources
│   │   ├── alb/                  # Load balancer target definitions
│   │   ├── asg/                  # Launch templates & dynamic scaling rules
│   │   ├── elasticache/          # Valkey cluster configuration
│   │   ├── jumphost/             # Cyberjaya whitelisted SSH Bastion setup
│   │   ├── rds/                  # Highly available DB instance configuration
│   │   ├── route53/              # Dynamic records mapping DNS values
│   │   ├── security_groups/      # Strict port security definitions
│   │   ├── standalone_ec2/       # Pre-bake AMI dev / test environments
│   │   └── vpc/                  # Multi-AZ subnet allocation structures
│   ├── main.tf                   # Core OpenTofu file mapping variables and submodules
│   ├── outputs.tf                # Global stack endpoints outputs
│   ├── providers.tf              # Declarative block specifying AWS, TLS, Random, etc.
│   ├── variables.tf              # Fully typed input variables
│   └── terraform.tfvars.example  # Production template environment configurations
├── README.md                     # Central documentation index portal (this file)
├── AGENTS.md                     # Guide and context guidelines for AI Agents (including Google Jules)
├── llms.txt                      # AI-optimized plain text directory pointing to resources
├── HISTORY.md                    # Rich project narrative detailing the timeline from Day 0
└── CHANGELOG.md                  # Semantic version history detailing milestones to v1.0.0
```

---

## Documentation Portal Index

Our comprehensive documentation is compiled, auto-formatted, and deployed directly via **GitHub Pages**. Use the catalog below to navigate to specific sections:

### 1. Conceptual Alignment & Architecture (Engineering)

* **[Developer Design Alignment](docs/engineering/developer-design-mapping.md):** Architectural breakdown mapping fragile legacy single-VM developer architectures into enterprise-level highly available managed services.
* **[Separation of Concerns](docs/engineering/asg-separation-of-concern.md):** Guidelines for implementing stateless ASG layers, session persistence, and comparative analysis of S3 vs. Amazon EFS.
* **[System Architecture Details](docs/engineering/architecture.md):** Comprehensive breakdown of VPC subnetting, route tables, and Multi-AZ network architecture configurations.
* **[AI Agent Data Flow & Zero-Trust Handshake](docs/engineering/ragflow-langfuse.md):** Analysis of end-to-end request lifecycle and secure Zero-Trust handshakes for external AI Agents.
* **[OpenTofu Migration Guide](docs/engineering/opentofu-migration.md):** Migration patterns, state management comparisons, and CLI syntax transitions between legacy Terraform and OpenTofu.
* **[CodeIgniter Deployment Guide](docs/engineering/codeigniter-php-fpm.md):** Complete setup, proxy settings, and session/cache tuning configurations for CodeIgniter on Nginx & PHP-FPM.

### 2. Infrastructure Submodules (Engineering)

* **[VPC Networking](docs/engineering/modules/vpc.md):** Dynamic subnetting allocation, NAT Gateway patterns, and Route Table linkages.
* **[Security Groups Firewall](docs/engineering/modules/security_groups.md):** Zero-Trust ingress/egress rules and port-level component isolation.
* **[WAF Protection](docs/engineering/modules/waf.md):** Layer-7 Web Application Firewall settings, custom rulesets, and IP rate limits.
* **[ALB Target Routing](docs/engineering/modules/alb.md):** Target groups routing rules, SSL termination, and endpoint configurations.
* **[ASG Compute Clusters](docs/engineering/modules/asg.md):** Launch templates, scaling definitions, and automatic ARM64 Graviton architecture detection.
* **[RDS Multi-AZ Database](docs/engineering/modules/rds.md):** Database clustering, parameter group optimization, and storage encryption details.
* **[ElastiCache Valkey](docs/engineering/modules/elasticache.md):** Ultra-fast caching cluster parameters and cost considerations.
* **[Jumphost (SSH Bastion)](docs/engineering/modules/jumphost.md):** Secured entrypoints mapping whitelisted Cyberjaya developer offices to downstream resources.
* **[Standalone EC2 Environments](docs/engineering/modules/standalone_ec2.md):** Dedicated testing/development servers mimicking identical RDS/S3 linkages.

### 3. Advanced Operational Guides (Engineering)

* **[PostgreSQL Database Comparison](docs/engineering/postgresql-comparison.md):** Managed RDS PostgreSQL 17 Multi-AZ vs. self-installed Percona PostgreSQL 17 on EC2 (comparing Patroni/PgBouncer, telemetry, and local costs).
* **[Secure Bastion & Jumphost Operations](docs/engineering/jumphost.md):** Manual detailing secure client key configurations, Windows/macOS connection commands, and ASIMP-hardened operating parameters.
* **[AMI Hardening Compliance](docs/engineering/ami-design.md):** Pre-baked Ubuntu 26.04 LTS AMIs using Packer, Ansible, and the ASIMP security hardening framework.
* **[GitLab CI/CD & Persistent EFS Storage](docs/engineering/gitlab-efs-cicd.md):** GitLab pipeline automation mounting EFS, tuning performance with `open_file_cache`, and managing dynamic Nginx paths.
* **[Route 53 & Dynamic DNS Troubleshooting](docs/engineering/route53.md):** Domain names matching, certificate auto-validation, and extensive research on ASG dynamic resolver cache issues.

### 4. Strategic Financial Blueprints (Executive)

* **[AWS Sovereign Infrastructure Adoption Roadmap](docs/executive/aws-adoption-roadmap.md):** Precise chronological trigger points for DR and hybrid upgrades tied to financial run-rate increases.
* **[Disaster Recovery & Sovereignty](docs/executive/dr-options.md):** High-availability failover guidelines, AWS Elastic Disaster Recovery (AWS DRS) Strategy modeling, and Malaysian PDPA compliance pathways.
* **[Hybrid Cloud Connections](docs/executive/hybrid-onprem.md):** Evaluation comparing high-cost VPN/Direct Connect with modern cost-optimized API-driven and proxy styles.
* **[Cost Analysis Guide (Dev/Staging)](docs/executive/costing.md):** Comprehensive price modeling in USD and MYR tailored for the `ap-southeast-5` (Malaysia) region. Includes:
  - **Baseline Cost-Optimized Plan (~$141.47 USD/mo):** Budget-oriented layout leveraging shared instances, Valkey caching, and single NAT routing under standard staging traffic.
  - **High-Performance Enterprise Plan (~$898.54 USD/mo):** High-availability layout leveraging multi-NAT, large compute families, and extensive backup limits.
* **[Production Cost Analysis Guide](docs/executive/production-costing.md):** Sovereign Enterprise Production cost model specifically optimized for the 9-ASG and 3-ALB production blueprint under high-concurrency loads:
  - **Baseline Production Plan (~$462.09 USD/mo):** Cost-optimized, secure production network utilizing 20 active t4g.micro instances, Multi-AZ/Single-AZ MariaDB/PostgreSQL, EFS storage, and 3 ALBs.
  - **High-Performance Enterprise Production Plan (~$3,115.96 USD/mo):** High-performance production network utilizing 20 active t4g.medium instances, Multi-AZ/Single-AZ MariaDB/PostgreSQL, high-capacity clustered Valkey session store, and 3 ALBs.

---

## Getting Started

### Prerequisites
* [OpenTofu](https://opentofu.org/downloads.html) >= 1.6.0 installed on your local control node.
* [AWS CLI](https://aws.amazon.com/cli/) configured with administrative rights targeted to `ap-southeast-5`.
* Python >= 3.10 (to run build/prepare automation).

### Local Execution Pipeline


1. **Initialize & Sync Repository:**

   ```bash
   git clone https://github.com/linuxmalaysia/aws-3tier-deployment-for-php-infra.git
   cd aws-3tier-deployment-for-php-infra
   ```

2. **Setup Environment Variables:**

   ```bash
   cp terraform/terraform.tfvars.example terraform/terraform.tfvars
   ```

   *Edit the tfvars configuration with your target database credentials and office IP ranges.*

3. **Execute Automated Deployment Script:**

   The `scripts/deploy.sh` handles linting, auto-formatting, syntax validation, and displays the proposed modifications:

   ```bash
   ./scripts/deploy.sh
   ```

4. **Teardown Clean-up:**

   To safely remove and de-provision resources:

   ```bash
   ./scripts/destroy.sh
   ```

---

## CI/CD Deployment with GitHub Actions

The repository integrates a secure deployment pipeline in `.github/workflows/opentofu.yml` utilizing **AWS OIDC (OpenID Connect)**.

### Pipeline Features
* **Conditional Triggers:** OpenTofu plan/apply executions are dynamically bypassed in fork pull-requests where AWS secrets are restricted. This avoids standard deployment failures while maintaining full local verification.
* **Jekyll Compilation Pages:** The `.github/workflows/jekyll-gh-pages.yml` automatically executes the `scripts/prepare_docs.py` before building and publishing our responsive documentation portal.

---

## Contact & Maintenance

For questions regarding development parameters, AMI baking steps, or local security policies, consult [AGENTS.md](AGENTS.md) or open an issue on the centralized repository.
