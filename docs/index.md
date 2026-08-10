---
layout: default
okf_version: "0.1"
type: "Documentation Index"
title: "AWS Secure 3-Tier Architecture Documentation"
timestamp: 2026-08-05T22:20:36+08:00
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
3. **[Costing Estimate](executive/costing.html):** Comprehensive monthly cost breakdown, local currency estimates, and Day-2 cost optimization pathways.
4. **[Production Costing Estimate](executive/production-costing.html):** Comprehensive monthly and annual production-scale cost breakdown.
5. **[Hybrid Cloud Integration Guide](executive/hybrid-onprem.html):** Evaluation of API-based, MCP-based, and official AWS network connection systems (VPN, Direct Connect, Transit Gateway) with costing models.

### Engineering & DevOps Implementation Guides
<!-- markdownlint-disable MD029 -->
1. **[System Architecture](engineering/architecture.html):** Deep dive into physical network structure, subnets, routing tables, and AWS resource layout in the Malaysia region.
2. **[AI Agent Data Flow & Zero-Trust Handshake Guide](engineering/ragflow-langfuse.html):** Analysis of end-to-end request lifecycle and secure Zero-Trust handshakes for external AI Agents like Google Antigravity.
3. **[Developer Design Alignment Guide](engineering/developer-design-mapping.html):** Comparative rationale for shifting from legacy single-node VMs to secure, Multi-AZ architecture.
4. **[ASGs & Separation of Concerns Guide](engineering/asg-separation-of-concern.html):** Multi-tier ASG scaling guides, stateless designs, and comparison of Amazon S3 vs. EFS.
5. **[Root OpenTofu/Terraform Files](engineering/root-files.html):** Technical overview of root configuration entries (`main.tf`, `variables.tf`, etc.).
6. **[OpenTofu Migration Guide](engineering/opentofu-migration.html):** Detailed transition paths and compatibility studies for deploying natively with OpenTofu.
7. **[AMI Design & Hardening Guide](engineering/ami-design.html):** Hardened Ubuntu base baking process, Packer/Ansible image pipelines, and ASIMP auditing.
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
- **[Standalone EC2 Module](engineering/modules/standalone_ec2.html):** Secure standalone Ubuntu 26.04 LTS development and application environments.
- **[Fusio API Server Module](engineering/modules/fusio.html):** Dedicated API gateway cluster using Nginx, PHP-FPM, and a MariaDB RDS database.
- **[ElastiCache Valkey Module](engineering/modules/elasticache.html):** Secure ElastiCache Valkey in-memory caching cluster for session and metadata store.
- **[Jumphost Module](engineering/modules/jumphost.html):** Secure public-subnet SSH Jumphost (Bastion) whitelisted for Cyberjaya office with automated downstream ingress configuration.

### Deployment & CI/CD
- **[Automation Scripts](engineering/scripts.html):** Details about CLI helpers (`deploy.sh`, `destroy.sh`, `user_data.sh`).
- **[CI/CD Pipeline](engineering/cicd.html):** GitHub Actions workflow for automatic formatting, testing, validation, and OIDC deployment.
- **[GitLab EFS CI/CD](engineering/gitlab-efs-cicd.html):** Comprehensive guide on GitLab CI/CD, automatic workflows, EFS mounting, dynamic Nginx path configurations, and containerized/S3 alternatives.
- **[Performance Testing & Scaling Roadmap](engineering/performance-testing.html):** Comprehensive analysis of 100 VU, 500 VU, 1,000 VU, 2,500 VU, 5,000 VU, and 10,000 VU loads, detailing needed AWS services, sizing specifications, and granular cost estimates.
- **[Load Testing & Performance Analysis](engineering/performance-analysis.html):** In-depth evaluation of load tests under 100 VU, 500 VU, 1,000 VU, 2,500 VU, 5,000 VU, and 10,000 VU loads, including root cause analyses of database bottlenecks and recommendations.
- **[GitHub Repository Fork Detachment Guide](engineering/github-detach-fork.html):** Complete walk-through on how to safely detach our repository fork on GitHub and establish it as an independent codebase.

---

## Prerequisites

Before deploying the infrastructure, ensure you have the following tools installed and configured:

- **[OpenTofu](https://opentofu.org/) >= 1.6.0** (Recommended) or **Terraform >= 1.5.0**
- **[AWS CLI](https://aws.amazon.com/cli/)** configured with admin-level credentials for `ap-southeast-5`
- **Git** for repository and revision tracking
