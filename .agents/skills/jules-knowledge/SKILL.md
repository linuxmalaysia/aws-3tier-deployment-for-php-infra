---
layout: default
okf_version: "0.1"
type: "Agent Skill"
title: "Google Jules Infrastructure & Cloud Engineering Skill"
timestamp: "2026-08-05T22:20:36+08:00"
topics: ["aws", "3-tier", "ai-agents", "instructions"]
description: "Comprehensive workspace instructions, architectural mappings, security boundaries, and automation practices curated from Google Jules. Use this when performing Cloud and Systems Engineering tasks in this repository."
name: jules-knowledge
---

# Google Jules Infrastructure & Cloud Engineering Skill

This skill embeds the full engineering knowledge, context, standards, and constraints of Google Jules—an elite Cloud and Systems Engineer assisting in maintaining and optimizing the secure AWS 3-Tier Web & AI Infrastructure workspace. Other AI Agents, including Google Antigravity, must strictly follow and leverage this knowledge base.

---

## 1. Introduction, Core Purpose, and Navigation

1. **Google Antigravity & Agent Skills Integration:** The repository supports Google Antigravity Skills, with this workspace-specific skill located at `.agents/skills/jules-knowledge/SKILL.md` containing comprehensive guidelines, architectural mapping, and standard operating procedures curated from Google Jules.
2. **Developer Integration Guide:** A developer integration guide for Google Antigravity Skills and the Agent Skills ecosystem is documented at `docs/antigravity-skills.md` and registered across all major documentation indices (`docs/index.md`, `README.md`, and `llms.txt`).
3. **AI Agent Guidelines (`AGENTS.md`):** The `AGENTS.md` file in the root directory outlines operating guidelines, standards, and behavioral constraints tailored for AI agents (specifically Google Jules) to ensure deterministic OpenTofu practices and strict adherence to architectural standards.
4. **LLM Crawling Index (`llms.txt`):** The `llms.txt` file is located in the root directory following the `llmstxt.org` specification, serving as an index for LLM web crawlers and AI agents to discover, parse, and navigate all architecture, costing, scripting, and disaster recovery guides.
5. **Developer Portal (`README.md`):** The root `README.md` is fully updated to serve as a comprehensive developer portal, structuring navigation paths to local repository files, OpenTofu (Terraform) submodules, and their fully compiled, respective Jekyll GitHub Pages documentation URLs.
6. **Comprehensive Documentation Standard:** The project requires comprehensive Markdown documentation for all modules, scripts, and workflows to support generating documentation pages for GitHub Pages. Centralized documentation is stored in the `docs/` folder configured for Jekyll.

---

## 2. Regional Defaults & Cloud Platform Target

7. **Default Target Region & Compute:** The default deployment target is the AWS Asia Pacific (Malaysia) region (`ap-southeast-5`), using ARM64/Graviton instances (`t4g.micro` for EC2/ASG and `db.t4g.micro` for RDS PostgreSQL 16) by default.
8. **Dynamic AMI Selection:** The Auto Scaling Group (`asg`) module dynamically selects the appropriate Amazon Linux 2023 AMI (ARM64 or x86_64) based on the configured EC2 instance type family.
9. **Native OpenTofu Alignment:** The infrastructure configuration and documentation have been updated to target OpenTofu natively. Outdated Terraform references were corrected, including setting the recommended version specification to `OpenTofu >= 1.6.0` (while preserving backward compatibility with `Terraform >= 1.5.0`).
10. **Sandbox Execution Constraint:** The sandbox execution environment does not have the `terraform` or `tofu` CLI binaries installed by default.

---

## 3. OpenTofu Modular Infrastructure Design

11. **Secure 3-Tier Architecture:** The repository is structured to deploy a secure AWS 3-tier architecture (ALB, ASG, Multi-AZ RDS) integrated with AWS WAFv2 using OpenTofu.
12. **Highly Modular Directory Structure:** The OpenTofu infrastructure is modularly organized under the `terraform/` directory, including submodules for `vpc`, `security_groups`, `waf`, `alb`, `asg`, `rds`, `standalone_ec2`, `route53`, `elasticache` (Valkey), and `jumphost` (Bastion).
13. **Optional Route 53 Module Integration:** The architecture incorporates an optional Route 53 module controlled via the `enable_route53` root boolean variable. This module provisions a public hosted zone and creates an A Alias record pointing directly to the Application Load Balancer.
14. **Type-Safe Variable Definitions:** The invalid syntax type specification `boolean` in `terraform/variables.tf` for the `enable_standalone_ec2` variable was corrected to `bool` to satisfy OpenTofu and Terraform verification checks.

---

## 4. Auto Scaling Groups & Standalone Instances

15. **Staging & Testing Pairings:** The system architecture pairs each of the three Auto Scaling Group (ASG) application groups (Frontend Nginx, Backend, and AI Tier) with a dedicated standalone EC2 instance connected to the same databases/shared storage (RDS, S3, or EFS) to serve as a staging and testing environment for pre-baking AMIs.
16. **Secure Standalone EC2 Deployment:** The OpenTofu infrastructure includes a `standalone_ec2` module (at `terraform/modules/standalone_ec2/`) to deploy standalone Ubuntu 26.04 LTS development and application instances inside secure private subnets, integrated with AWS Systems Manager (SSM) for passwordless management.
17. **Legacy-to-Cloud Alignment & Hardening:** The architecture documentation includes a detailed developer alignment guide (at `docs/engineering/developer-design-mapping.md`) that maps legacy, single-VM configurations to AWS-native managed services and secure private subnets, with the target operating system upgraded to Ubuntu 26.04 LTS hardened via the ASIMP (Ansible System Integrity Management Platform) framework.
18. **Multi-Tier ASG Separation of Concerns:** A comprehensive architectural guide on Auto Scaling Groups (ASGs) and Separation of Concerns is available at `docs/engineering/asg-separation-of-concern.md`. It explains multi-tier ASG designs, state management, and provides comparative guidelines and implementation details for Amazon S3 and Amazon EFS in auto-scaling environments.

---

## 5. Database & Caching Architecture

19. **PostgreSQL Migration & Comparison:** A comprehensive technical comparison guide comparing AWS RDS PostgreSQL 17 (Multi-AZ) and self-installed Percona Server for PostgreSQL 17 on EC2 (detailing costing models in USD/MYR for `ap-southeast-5`, architectural layouts with Patroni/PgBouncer, telemetry comparison with PMM, and extension differences like `pg_stat_monitor`) is documented at `docs/engineering/postgresql-comparison.md` and integrated into the Jekyll site navigation.
20. **Amazon ElastiCache for Valkey Integration:** The repository supports Amazon ElastiCache for Valkey as a modern, license-compliant replacement for Redis OSS, which delivers 20% lower on-demand pricing ($0.0128/hr for `cache.t4g.micro` and $0.0544/hr for `cache.t4g.medium` in `ap-southeast-5`) with high security (transit & at-rest encryption, subnet group, and strict security groups limiting ingress to compute ASG and standalone nodes on port 6379).

---

## 6. Security, Bastion SSH & AMI Baking Compliance

21. **SSH Bastion Jumphost Module:** The OpenTofu infrastructure includes a `jumphost` module (at `terraform/modules/jumphost/`) to deploy a secure SSH Jumphost (Bastion) in the public subnet. It allocates a static Elastic IP, whitelists incoming SSH exclusively from a configured Cyberjaya developer office CIDR, and automatically injects SSH ingress rules into private downstream compute security groups.
22. **Developer SSH Hardening & Access Guide:** A detailed developer access and SSH hardening guide is available at `docs/engineering/jumphost.md` outlining connection steps for Windows (PowerShell, PuTTY), macOS, and Linux, security procedures for private key protection (`chmod`, Windows NTFS ACLs via `icacls`), and OS-level hardening instructions using the ASIMP framework.
23. **CIS Compliant AMI Baking Strategy:** The project documents its Amazon Machine Images (AMI) baking and compliance strategy at `docs/engineering/ami-design.md`, utilizing HashiCorp Packer and Ansible with the ASIMP framework to bake secure, CIS Level 2-compliant Ubuntu 26.04 LTS images for each Auto Scaling Group.

---

## 7. Disaster Recovery, National Sovereignty & Hybrid Integrations

24. **AWS-Native vs. On-Premises RAGFlow & Langfuse:** A comprehensive architectural and economic guide comparing AWS-native and on-premises deployments for RAGFlow + Langfuse is documented at `docs/engineering/ragflow-langfuse.md` and integrated into the Jekyll site navigation, detailing the critical role of GPUs in visual layout analysis (DeepDoc) and OCR, hybrid API/MCP integration, and localized cost/sovereignty trade-offs.
25. **PDPA-Aligned In-Region vs. Cross-Region DR Decision Matrix:** The Disaster Recovery Options & Sovereignty Guide (`docs/executive/dr-options.md`) includes specific, separate classifications for both In-Region and Cross-Region deployments in its decision matrix (Section 5), supported by a detailed technical approach (Section 2.3) addressing field-level encryption/tokenization, KMS cryptographic isolation, programmatic failover circuit breakers, and Transfer Impact Assessments (TIAs) under PDPA Section 129.
26. **AWS Disaster Recovery (DR) & Sovereignty Guide:** A comprehensive AWS Disaster Recovery (DR) and National Sovereignty Guide is documented at `docs/executive/dr-options.md` and integrated into the Jekyll site navigation and index, detailing four standard cloud DR options alongside AWS Elastic Disaster Recovery (AWS DRS) as a fifth continuous block-level replication option, aligned with the Multi-AZ 3-tier system architecture, regulatory compliance pathways under the Malaysian Personal Data Protection Act (PDPA) 2010 (and 2025 CBPDT Guidelines), and highly detailed monthly cost estimates in USD and MYR.
27. **AWS Elastic Disaster Recovery (AWS DRS) Integration:** AWS Elastic Disaster Recovery (AWS DRS) is integrated as 'Strategy E' in `docs/executive/dr-options.md`, modeling continuous asynchronous block-level replication (RPO in seconds/minutes, RTO in minutes) from on-premises or cloud servers into a lightweight staging area subnet (using low-cost `t3.small` replication instances and gp3 staging volumes) to support cost-optimized, sovereign recovery under Malaysian regulatory rules.
28. **Hybrid Cloud Integration & Costing Guide:** A comprehensive hybrid cloud integration and costing guide comparing cost-effective API-based and AI-native MCP-based (Model Context Protocol via AWS API Gateway MCP Proxy) connections against official AWS hybrid networking solutions (Site-to-Site VPN, Direct Connect, and Transit Gateway) in the `ap-southeast-5` (Malaysia) region is documented at `docs/executive/hybrid-onprem.md` and integrated into the Jekyll site navigation.

---

## 8. Financial Management & Detailed Cost Breakdown

<!-- markdownlint-disable MD029 -->
29. **Baseline vs. High-Performance Financial Plans:** The system costing documentation (at `docs/executive/costing.md`) includes detailed Baseline Cost-Optimized (~$141.47 USD/mo) and High-Performance (~$898.54 USD/mo) Plans, which incorporate ElastiCache for Valkey, dedicated standalone EC2 instances, a secure SSH Jumphost ($10.98/mo), and AWS Route 53 hosting/query costs ($1.30/mo).
30. **Infrastructure Cost Breakdown Page:** An AWS infrastructure cost estimation breakdown page is available at `docs/executive/costing.md` and integrated into the Jekyll site navigation and index.
<!-- markdownlint-enable MD029 -->

---

## 9. Build Scripts, Automation Workflows & CI/CD

31. **Landing Web Page Brand Consistency:** The bootstrap script `scripts/user_data.sh` generates a landing web page with a footer that references 'OpenTofu' instead of 'Terraform' for managed deployment visualization.
32. **GitLab CI/CD & Persistent NFS Integration:** A comprehensive deployment guide for integrating GitLab CI/CD pipelines with shared AWS EFS storage (mounted on ASGs and standalone instances), persistent NFS configurations, dedicated Nginx server paths, EFS metadata performance tuning (via `open_file_cache`), and robust architectural alternatives (e.g., S3 pulling or Docker on ECS) is documented at `docs/engineering/gitlab-efs-cicd.md`.
33. **GitHub Actions OpenTofu OIDC Pipeline:** A GitHub Actions CI/CD pipeline is configured in `.github/workflows/opentofu.yml` to automatically lint, validate, plan, and apply the infrastructure configuration using OpenTofu (`opentofu/setup-opentofu@v1`).
34. **Conditional Job Execution:** The GitHub Actions workflow conditionalizes jobs requiring AWS credentials (such as `opentofu-plan` and `opentofu-apply`) to run only when `secrets.AWS_ROLE_TO_ASSUME` is populated, avoiding credential loading failures in environments without secrets (e.g., fork pull requests).
35. **OpenTofu Migration & Commands Guide:** A comprehensive research and migration guide detailing AWS's compatibility, authentication, state management, commands, and managed service integrations with OpenTofu is available at `docs/engineering/opentofu-migration.md`.
36. **Deployment & Destruction Bash Utilities:** Bash scripts for deploying and destroying the infrastructure are provided under `scripts/deploy.sh` and `scripts/destroy.sh` and use the OpenTofu (`tofu`) CLI.
37. **GitHub Pages Deployment Pipeline:** The GitHub Pages deployment pipeline is defined in `.github/workflows/jekyll-gh-pages.yml` (replacing the redundant `pages.yml`), which automates document preparation using Python, Jekyll building from `./docs`, and deployment of the documentation site on pushes to the `main` branch.
38. **Pre-Build Documentation Preparation:** A pre-build Python script (`scripts/prepare_docs.py`) is used to recursively scan the `docs/` directory and prepend Jekyll front matter (layout and auto-extracted titles) to Markdown documentation files that lack it.

---

## 10. Historical Narrative & Changelog Milestones

39. **Strategic Engineering Log:** The historical narrative detailing strategic engineering choices from Day 0 (the monolithic single-VM starting point) is documented in `HISTORY.md`, and its development milestones are structured as a standard-compliant changelog in `CHANGELOG.md`.

---

## 11. Jekyll Documentation, Dynamic Layout, and High-Fidelity PDF Generation

40. **Custom Responsive Sidebar Layout:** The documentation layout features a custom responsive Jekyll theme configured in `docs/_layouts/default.html` and `docs/assets/css/global.css` with a left navigation sidebar and a main content area. It is styled for 100% width on desktop using a `260px 1fr` grid, and transitions to a stacked vertical layout below `992px` to support tablet and mobile screens, featuring touch-friendly navigation button grids and horizontally scrollable tables.
41. **Horizontal Table & Diagram Wrapping Safeguard:** To prevent standard code blocks from overflowing horizontally, `#content pre` in `docs/assets/css/global.css` is configured with `white-space: pre-wrap`. However, to prevent text-based diagrams and tables from wrapping and breaking their alignment, a lightweight JavaScript script in `docs/_layouts/default.html` dynamically scans for box-drawing characters and applies a `.no-wrap` class, which overrides wrapping with `white-space: pre !important` and enables modern, customized horizontal scrollbars.
42. **PDF Pagination Page-Break Safeguard:** To prevent blank first pages during PDF generation or printing, `html`, `body`, and `#container` are configured with `height: auto !important` and `min-height: auto !important` inside the `@media print` CSS block in `docs/assets/css/global.css` to override screen-specific `100vh` constraints.
43. **High-Fidelity PDF Generation Workflow:** The Jekyll-based documentation layout supports high-fidelity printing to A4 PDF with a clean white ("day") background via a comprehensive `@media print` CSS block in `docs/assets/css/global.css`, an integrated interactive "PRINT PDF" JavaScript button in `docs/_layouts/default.html`, and an automated PDF generation workflow configured in `.github/workflows/pdf-generation.yml` using `misaelnieto/web_to_pdf_action@v0.3.1`.
44. **Route 53 DNS Failure Modes Analysis:** The project documents and explains Route 53 domain mapping, ACM SSL/TLS validation, and common causes of Auto Scaling Group DNS resolution failures (such as the Nginx dynamic resolver cache issue, systemd-resolved behaviors, security group rules, and Route 53 query throttling) in a dedicated technical guide at `docs/engineering/route53.md`.
