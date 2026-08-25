---
layout: default
okf_version: "0.1"
type: "Documentation Index"
title: "AWS Secure 3-Tier Architecture Documentation"
timestamp: "2026-08-05T22:20:36+08:00"
topics: ["aws", "3-tier"]
---

# AWS Secure 3-Tier Architecture Documentation

Welcome to the official technical documentation for our **AWS 3-Tier Deployment for PHP CodeIgniter Web Application** project. This project is optimized for deployment in the **AWS Asia Pacific (Malaysia) region (`ap-southeast-5`)** utilizing AWS Graviton (ARM64) instances, Multi-AZ RDS Database, and AWS WAFv2 regional protection.

This deployment is structured natively in OpenTofu, adhering to strict modular boundaries, security best practices, and the **Zero-Trust Network Principle** for PHP-FPM and Nginx execution.

The documentation is organized by reader persona into two core sections:
1. **[Executive Blueprints](executive/aws-adoption-roadmap.html):** Isolating financial planning, compliance, disaster recovery policies, and adoptions.
2. **[Engineering Guides](engineering/architecture.html):** Dedicated to technical implementation, deployment commands, security, and CI/CD steps.

---

## Documentation Index

Explore different sections of our infrastructure documentation:

### Executive Strategic Blueprints
1. **[AWS Sovereign Infrastructure Adoption Roadmap](executive/aws-adoption-roadmap.html):** Strategic chronological timeline mapping financial run-rates and milestones to DR and network resiliency phases.
2. **[Disaster Recovery Options & National Sovereignty Guide](executive/dr-options.html):** Production-ready playbook covering DR options, regulatory compliance under the Malaysian PDPA, and MYR/USD costing models.
3. **[AWS Disaster Recovery (DR) Strategy & Options Evaluation](executive/dr-options-evaluation.html):** Strategic evaluation of 3+1 disaster recovery options discussed for the Malaysia region, aligned with AWS Cloud DR whitepapers and UK English standards.
4. **[Costing Estimate](executive/costing.html):** Comprehensive monthly cost breakdown, local currency estimates, and Day-2 cost optimization pathways.
5. **[Production Costing Estimate](executive/production-costing.html):** Comprehensive monthly and annual production-scale cost breakdown.
6. **[Hybrid Cloud Integration Guide](executive/hybrid-onprem.html):** Evaluation of API-based, MCP-based, and official AWS network connection systems (VPN, Direct Connect, Transit Gateway) with costing models.

### Engineering & DevOps Implementation Guides
<!-- markdownlint-disable MD029 -->
1. **[System Architecture](engineering/architecture.html):** Deep dive into physical network structure, subnets, routing tables, and AWS resource layout in the Malaysia region.
2. **[AI Agent Data Flow & Zero-Trust Handshake Guide](engineering/ragflow-langfuse.html):** Analysis of end-to-end request lifecycle and secure Zero-Trust handshakes for external AI Agents like Google Antigravity.
3. **[Developer Design Alignment Guide](engineering/developer-design-mapping.html):** Comparative rationale for shifting from legacy single-node VMs to secure, Multi-AZ architecture.
4. **[ASGs & Separation of Concerns Guide](engineering/asg-separation-of-concern.html):** Multi-tier ASG scaling guides, stateless designs, and comparison of Amazon S3 vs. EFS.
5. **[Root OpenTofu/Terraform Files](engineering/root-files.html):** Technical overview of root configuration entries (`main.tf`, `variables.tf`, etc.).
6. **[OpenTofu Migration Guide](engineering/opentofu-migration.html):** Detailed transition paths and compatibility studies for deploying natively with OpenTofu.
7. **[AMI Design & Hardening Guide](engineering/ami-design.html):** Hardened Debian & RHEL base baking process, Packer/Ansible image pipelines, and ASIMP auditing.
8. **[Route 53 & DNS Troubleshooting](engineering/route53.html):** ACM SSL/TLS setup, custom domain mapping, and dynamic DNS caching resolution audits.
9. **[Secure Developer Access Guide](engineering/jumphost.html):** SSH Bastion setup, whitelisting Cyberjaya endpoints, client configurations, and key security.
10. **[RDS PostgreSQL 17 vs. Percona Server for PostgreSQL 17 Guide](engineering/postgresql-comparison.html):** Database engine comparisons, telemetry (PMM vs CloudWatch), and cost structures in ap-southeast-5.
11. **[CodeIgniter Deployment Guide](engineering/codeigniter-php-fpm.html):** Optimizing CodeIgniter on Nginx and PHP-FPM, utilizing ElastiCache for Valkey session scaling.
<!-- markdownlint-enable MD029 -->

### Security Hardening & Compliance Reports (ASIMP)
<!-- markdownlint-disable MD029 -->
1. **[Security Posture Assessment (SPA) Checklist](engineering/security-posture-assessment.html):** Comprehensive security controls audit checklist, governance roadmap, and SLA timeline.
2. **[Output of ASIMP](engineering/asimp-output.html):** Standardized, multi-engine security hardening progress and consolidated scorecard report.
3. **[Output of Lynis](engineering/lynis-output.html):** Detailed Unix-based host configuration scanning and hardening index rating scorecard.
4. **[Output of OpenSCAP](engineering/openscap-output.html):** Detailed CIS Level 2 benchmark profile compliance checklist and OVAL vulnerability reports.
<!-- markdownlint-enable MD029 -->

### Infrastructure Submodules
- **[VPC Module](engineering/modules/vpc.html):** Core networking, public/private subnets, internet gateways, and NAT configurations.
- **[Security Groups Module](engineering/modules/security_groups.html):** Strict firewall rulesets and port-level isolation.
- **[WAF Module](engineering/modules/waf.html):** Layer-7 Web Application Firewall protecting the ALB.
- **[ALB Module](engineering/modules/alb.html):** Application Load Balancer and health-check configurations.
- **[ASG Module](engineering/modules/asg.html):** Auto Scaling Group, Launch Templates, and dynamic Graviton auto-detection.
- **[RDS Module](engineering/modules/rds.html):** Multi-AZ database configuration and parameter group tuning.
- **[Standalone EC2 Module](engineering/modules/standalone_ec2.html):** Secure standalone Debian-derived and RHEL-derived development and application environments.
- **[Fusio API Server Module](engineering/modules/fusio.html):** Dedicated API gateway cluster using Nginx, PHP-FPM, and a MariaDB RDS database.
- **[ElastiCache Valkey Module](engineering/modules/elasticache.html):** Secure ElastiCache Valkey in-memory caching cluster for session and metadata store.
- **[Jumphost Module](engineering/modules/jumphost.html):** Secure public-subnet SSH Jumphost (Bastion) whitelisted for Cyberjaya office with automated downstream ingress configuration.

### Deployment & CI/CD
- **[Autonomous AI Pair-Programming & Multi-Agent Operations with Google Jules](jules-platform-guide.html):** Comprehensive technical guide documenting end-to-end repository creation, OpenTofu IaC, Ansible automation, GitHub Pages CI/CD, PR comment workflows, and Google Antigravity delegation.
- **[Wazuh SIEM & XDR Deployment Guide](engineering/wazuh-installation.html):** Comprehensive guide detailing Wazuh deployment options across AWS Cloud (ap-southeast-5 Graviton), On-Premises AlmaLinux 10, and local WSL2 Windows 11 demo environments with Podman.
- **[AI Processing Stack, Flowise + Qdrant + LiteLLM Integration, & API Gateway Guide](engineering/ai-processing-stack.html):** Deep-dive into AI processing infrastructure, Flowise visual workflow orchestration, Qdrant vector retrieval, LiteLLM proxy routing, and production PHP CodeIgniter API request patterns.
- **[ASIMP for AI Agents: Cognitive Twin Integration & Persistent Memory Guide](engineering/asimp-for-ai-agents.html):** Comprehensive integration guide detailing how ASIMP pairs with autonomous AI agents (Google Jules/Antigravity) using the Deep State of Mind (DSOM) framework, AGENTS.md, and .agents/brain/ context.
- **[SOP: Local Knowledge-First Discovery & OKF Context Protocol](engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.html):** Standard Operating Procedure detailing the 5-step local discovery flow and metadata-first context protocol for AI agents and human operators before executing remote commands.
- **[AWS CLI Installation and Infrastructure Discovery Guide](engineering/aws-cli-guide.html):** Standard instructions for installing, configuring, and utilizing version 2 of the AWS CLI to discover and query our 3-tier PHP infrastructure in ap-southeast-5.
- **[Automation Scripts](engineering/scripts.html):** Details about CLI helpers (`deploy.sh`, `destroy.sh`, `user_data.sh`).
- **[CI/CD Pipeline](engineering/cicd.html):** GitHub Actions workflow for automatic formatting, testing, validation, and OIDC deployment.
- **[GitLab EFS CI/CD](engineering/gitlab-efs-cicd.html):** Comprehensive guide on GitLab CI/CD, automatic workflows, EFS mounting, dynamic Nginx path configurations, and containerized/S3 alternatives.
- **[Performance Testing & Scaling Roadmap](engineering/performance-testing.html):** Comprehensive analysis of 100 VU, 500 VU, 1,000 VU, 2,500 VU, 5,000 VU, and 10,000 VU loads, detailing needed AWS services, sizing specifications, and granular cost estimates.
- **[Load Testing & Performance Analysis](engineering/performance-analysis.html):** In-depth evaluation of load tests under 100 VU, 500 VU, 1,000 VU, 2,500 VU, 5,000 VU, and 10,000 VU loads, including root cause analyses of database bottlenecks and recommendations.
- **[GitHub Repository Fork Detachment Guide](engineering/github-detach-fork.html):** Complete walk-through on how to safely detach our repository fork on GitHub and establish it as an independent codebase.
- **[AWS Services vs. On-Premises Open-Source Comparison Guide](engineering/aws-vs-onprem-comparison.html):** A comprehensive 12-layer mapping comparing cloud-native services with self-hosted, on-premises open-source solutions.
- **[DR Option Two Malaysia and Account Separation Guide](executive/dr-option-two-malaysia.html):** Detailed blueprint for copying production to a new AWS account in Malaysia, CLI command discovery, and pricing calculator parameters.
- **[Strategic Comparative Review: AWS-Native Managed Platform vs. Self-Hosted Custom Stack](aws-vs-self-hosted-review.html):** Comparative analysis evaluating operational leverage vs. raw hardware control of AWS-managed vs. custom-engineered self-hosted stacks.
- **[Legal Notice, Critical Assumptions & Disclaimer of Liability](legal-notice.html):** Critical notice and disclaimer establishing educational parameters, assumptions, and liability exclusions.

### Diátaxis Documentation System

- **[About the Diátaxis Framework](explanation/diataxis-framework.html):** Architectural choices and benefits of structuring our secure 3-tier PHP stack documentation into Tutorials, How-To Guides, Reference, and Explanations.
- **[Setting up a Development Sandbox (Tutorial)](tutorials/setup-development-sandbox.html):** Guided lesson to configure your local sandbox environment, establish virtual dependencies, and run validation test suites.
- **[Deploying & Destroying Infrastructure (How-To Guide)](how-to/deploy-infrastructure.html):** Action-focused guide for executing standard pre-flights, formatting, validating, planning, and applying OpenTofu stacks.
- **[Auditing Ansible & Podman Security (How-To Guide)](how-to/audit-ansible-and-podman.html):** Practical playbook to audit playbooks and Quadlet container files against hardening baselines using standard library parsers.
- **[Generating Sitemaps & LLM Assets (How-To Guide)](how-to/generate-sitemaps-and-llm-assets.html):** Synchronizing and compiling metadata indexes, text sitemaps, and escaped XML context representations for search engine and AI agent ingestion.
- **[CLI & Scripts Reference Manual (Reference)](reference/scripts-reference.html):** Exhaustive parameters, options, entry points, and exit codes for all helper utilities.
- **[Static Analysis Audit Rules (Reference)](reference/static-analysis-rules.html):** In-depth structural rules, prohibited keys, and validation signatures for our automated Ansible and Podman security linter checks.
- **[Lightweight Parsing & Metadata Parallelization (Explanation)](explanation/lightweight-parsers.html):** Deep-dive on why we avoid heavy external parsing packages in air-gapped runtimes, and how synchronous concurrent IMDSv2 metadata fetches work.

---

## Prerequisites

Before deploying the infrastructure, ensure you have the following tools installed and configured:

- **[OpenTofu](https://opentofu.org/) >= 1.6.0** (Recommended) or **Terraform >= 1.5.0**
- **[AWS CLI](https://aws.amazon.com/cli/)** configured with admin-level credentials for `ap-southeast-5`
- **Git** for repository and revision tracking
