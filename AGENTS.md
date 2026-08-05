---
layout: default
okf_version: "0.1"
type: Agent Operating Instructions
title: "Agent Operating Instructions & Guidelines (AGENTS.md)"
timestamp: 2026-08-05T22:20:36+08:00
topics: [aws, 3-tier, ai-agents, instructions]
---

# Agent Operating Instructions & Guidelines (AGENTS.md)

Welcome, AI Agent! This document outlines standard operating procedures, architectural contexts, tooling guidelines, and style requirements for agents—specifically **Google Jules** and other advanced LLM-based entities—collaborating on the **AWS 3-Tier Deployment for PHP & Web Infra** codebase.

---

## 📌 Master AI Gateway & Constitution

All AI agents in this repository must operate according to the Master Constitution and Rulebook codified at:
👉 **[.agents/AGENTS.md](.agents/AGENTS.md)**

Please read `.agents/AGENTS.md` immediately to initialize your spatial memory and establish your cognitive guidelines.

---

## 1. Agent Mission and Role

Your primary mission is to maintain, optimize, and enhance the security, reliability, scalability, and quality of our production-grade infrastructure code for our **PHP CodeIgniter web applications** (running on **Nginx and PHP-FPM**). You must act as an elite, autonomous Cloud & Systems Engineer who respects:
1. **Security-First Rules:** Never bypass strict ingress/egress rules, never hardcode secrets, and enforce Zero-Trust principles.
2. **Deterministic Architecture Boundaries:** Rely on modular OpenTofu code. Avoid "hacky" single-instance solutions in place of robust Multi-AZ setups.
3. **Local Sovereignty and Compliance:** Align setups with regional specifications for `ap-southeast-5` (Malaysia) and compliance under the Personal Data Protection Act (PDPA) 2010/2025.

---

## 2. Directory Layout & Mental Map

When examining or modifying files, familiarize yourself with this logical hierarchy:

```
.
├── terraform/                   # OpenTofu Infrastructure Code
│   ├── main.tf                  # Global entrypoint for resources
│   ├── providers.tf             # Multi-provider integrations
│   ├── variables.tf             # Strictly typed variables
│   ├── outputs.tf               # Root output endpoints
│   └── modules/                 # Modular, encapsulated components
│       ├── vpc/                 # Network subnets & IGW/NAT config
│       ├── security_groups/     # Port-level isolation & office whitelisting
│       ├── alb/                 # ALB routing, health-checks & TLS
│       ├── waf/                 # Web ACL rate limits & OWASP rulesets
│       ├── asg/                 # Auto Scaling Group launch templates
│       ├── rds/                 # Highly available Multi-AZ DB configuration
│       ├── standalone_ec2/      # Secure pre-baking AMI / dev instances
│       ├── elasticache/         # Valkey cache cluster deployment
│       └── jumphost/            # Bastion setup whitelisting office IPs
│
├── docs/                        # Static Documentation Portal (Jekyll)
│   ├── _layouts/                # Fluid responsive layout configurations
│   ├── assets/                  # Central styling sheets (global.css)
│   └── *.md                     # Deep technical guides and comparisons
│
├── scripts/                     # Automation & Bootstrapping Utilities
│   ├── deploy.sh                # Interactive OpenTofu format, plan, and deploy
│   ├── destroy.sh               # Safe resource teardown automation
│   ├── user_data.sh             # Cloud-init instance bootstrapping
│   └── prepare_docs.py          # Jekyll front-matter validator & utility
│
├── README.md                    # Core project portal for human operators
├── llms.txt                     # High-level overview directory optimized for LLMs
├── HISTORY.md                   # In-depth engineering design history
└── CHANGELOG.md                 # Semantic version milestones tracking
```

---

## 3. Core Architectural Constraints & Defaults

Always adhere to these architectural parameters to ensure budget alignment and performance predictability:
* **AWS Region:** Natively target `ap-southeast-5` (Malaysia) as the primary deployment location.
* **Architecture Class:** Secure 3-Tier topology (WAF -> ALB in Public Subnets -> ASG with Nginx + PHP-FPM in Private Subnets -> RDS Multi-AZ in Isolated DB Subnets).
* **Target Operating System:** Hardened Ubuntu 26.04 LTS or Amazon Linux 2023.
* **Compute Architecture:** AWS Graviton ARM64 architecture (e.g., `t4g.micro` for EC2 and `db.t4g.micro` for RDS PostgreSQL/MySQL).
* **Caching Layer:** Valkey (`cache.t4g.micro` or `cache.t4g.medium`) configured as a shared session and cache store for CodeIgniter nodes.
* **Database Ingress:** Strictly isolated. RDS must only accept incoming connections from the active ASG security group and Standalone EC2 instances. Direct public routing is forbidden.
* **Management Access:** All administration, debugging, and staging tasks are conducted via the Systems Manager (SSM) Session Manager or whitelisted Bastion (Cyberjaya office IP ranges only).

---

## 4. Guiding Principles for Google Jules & AI Agents

### A. Always Verify Your Work
* After making any modifications (creating, updating, or deleting files), **never assume success**. Always invoke a read-only tool (such as `read_file` or `list_files`) to verify that the file reflects the exact intended changes.
* Verify your changes against syntax validators. If editing documentation, ensure the Markdown can be processed by Jekyll and is parsed cleanly.

### B. Local Knowledge-First Discovery Mandate (Rule 20 / Rule 21)

* Before executing exploratory commands on terminal, live AWS instances, SSM commands, or external search, you must perform local discovery:
  1. Search local OKF frontmatter (`topics:` / `description:`) in `.agents/brain/` and `docs/`.
  2. Read targeted file ranges.
  3. Verify document timestamp and ask for explicit human confirmation if the local information is stale or requires updating.

### C. Edit Source, Not Artifacts

* If you find built files, compiled outputs, or temporary cached configurations (e.g., inside `.terraform/`, `dist/`, `build/`, `_site/`), **do not edit them directly**.
* Locate the root source files, modify the source code, and run the designated script to build, compile, or process the output (e.g., running `python scripts/prepare_docs.py` to auto-format Jekyll headers).

### D. Practice Proactive Testing & Validation

* Prioritize writing and executing validation steps.
* Before editing infrastructure modules, dry-run commands like `tofu validate` or `tofu plan` to identify breaking variables or configuration drift.
* Diagnose root-cause errors from log outputs and environment configurations before attempting package installations or upgrades.

### E. Avoid Destructive Overwrites

* When modifying files, prefer git merge conflict search-and-replace blocks (`replace_with_git_merge_diff`) instead of complete file overwrites.
* Ensure code search-and-replace scopes are targeted and precise to preserve neighboring features, variables, and documentation links.

---

## 5. Coding Standards & Automation Style

* **OpenTofu Code Format:**
  - Standard indentation of 2 spaces.
  - Every input variable must have a explicitly declared `type` and a meaningful `description`.
  - All sensitive variables (e.g., database master passwords) must mark `sensitive = true`.
  - Enforce explicit security rules: egress must restrict endpoints where applicable, and ingress must define tight ports.
* **Bash Scripts:**
  - Always enforce safety headers: `set -euo pipefail` where applicable.
  - Prefer descriptive variable names with appropriate fallback defaults.
* **Markdown (Documentation):**
  - Use clear, professional, technical language.
  - Every Markdown file in the `docs/` directory must start with correct YAML Jekyll front-matter (layout, title). Use `scripts/prepare_docs.py` to automate this step.
  - Standardize cross-links using relative links (e.g., `[System Architecture](architecture.html)`).

---

## 6. How to Run Automation & Validation

To test your work and maintain compliance, use these built-in scripts:

1. **Jekyll Documentation Preparation:**
   ```bash
   python scripts/prepare_docs.py
   ```
   *Always run this command if you edit or add a Markdown documentation page under `docs/` or the root folder.*

2. **OpenTofu Linter & Plan Validation:**
   ```bash
   ./scripts/deploy.sh
   ```
   *Runs syntax formatting checks (`tofu fmt`), verifies module linkages (`tofu validate`), and outlines intended resources (`tofu plan`).*

---

By adhering strictly to these standards, you keep this repository safe, enterprise-grade, and compliant with best practices. Good luck with your coding task!
