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

---

## Technical Overview

The architecture divides infrastructure components into discrete logical and physical tiers to achieve top-tier scalability, performance, and threat mitigation:

- **Presentation / Web Layer:** Application Load Balancer (ALB) receiving external traffic and filtered through AWS WAFv2 (OWASP rules + rate limiting).
- **Application / Compute Layer:** Auto Scaling Group (ASG) of Nginx + PHP-FPM (CodeIgniter PHP Application) running inside private subnets, auto-scaled on CPU usage, and managed via AWS Systems Manager (SSM).
- **Database Layer:** Multi-AZ RDS database deployed within isolated subnets, allowing connections exclusively from the application tier.

---

## Documentation Index

Explore different sections of our infrastructure documentation:

### Core Configuration
1. **[System Architecture](architecture.html):** Deep dive into the physical network structure, routing tables, and AWS resource layout in the Malaysia region, including how the Developer's first design is mapped.
2. **[Developer Design Alignment Guide](developer-design-mapping.html):** Rationale and comparison of shifting from legacy single-node PHP VMs to an enterprise secure AWS design.
3. **[ASGs & Separation of Concerns Guide](asg-separation-of-concern.html):** Best practice guide detailing auto-scaling with distinct ASGs, stateless principles, and the role of Amazon S3, EFS, or both.
4. **[Root OpenTofu/Terraform Files](root-files.html):** Overview of the root configuration entries (`main.tf`, `variables.tf`, `outputs.tf`, `providers.tf`).
5. **[OpenTofu Migration Guide](opentofu-migration.html):** Detailed compatibility research and transition path for deploying using OpenTofu on AWS.
6. **[AMI Design & Hardening Guide](ami-design.html):** Architectural guide outlining the pre-baked AMI strategy, Packer/Ansible pipeline, and ASIMP compliance integration.
7. **[Route 53 & DNS Troubleshooting](route53.html):** Deep dive into custom domain integration, ACM SSL/TLS setup, and extensive research on resolving ASG private subnet DNS resolution failures.
8. **[Secure Developer Access Guide](jumphost.html):** Comprehensive guide on using our secure SSH Jumphost (Bastion) to access private and standalone nodes from Cyberjaya, with Windows/macOS/Linux client setups and private key security guidelines.
9. **[Hybrid Cloud Integration Guide](hybrid-onprem.html):** Comprehensive evaluation of secure, cost-optimized API connections alongside official AWS hybrid network solutions (VPN, Direct Connect, Transit Gateway) with granular MYR/USD costing models for ap-southeast-5.
10. **[Disaster Recovery Options & National Sovereignty Guide](dr-options.html):** Production-ready playbook covering the 4 standard AWS cloud DR options aligned with our Multi-AZ architecture, detailed local sovereignty/PDPA/CBPDT compliance reviews, and granular USD/MYR costing comparisons.
11. **[RDS PostgreSQL 17 vs. Percona Server for PostgreSQL 17 Guide](postgresql-comparison.html):** Comprehensive technical comparison of performance, telemetry, observability (PMM vs CloudWatch/Performance Insights), architectural designs, and costs in USD/MYR for ap-southeast-5.
12. **[CodeIgniter Deployment Guide](codeigniter-php-fpm.html):** Detailed guide on deploying and optimizing CodeIgniter on Nginx + PHP-FPM with Valkey-based session cache integration.

### Infrastructure Submodules
- **[VPC Module](modules/vpc.html):** Core networking, public/private subnets, internet gateways, and NAT configurations.
- **[Security Groups Module](modules/security_groups.html):** Strict firewall rulesets and port-level isolation.
- **[WAF Module](modules/waf.html):** Layer-7 Web Application Firewall protecting the ALB.
- **[ALB Module](modules/alb.html):** Application Load Balancer and health-check configurations.
- **[ASG Module](modules/asg.html):** Auto Scaling Group, Launch Templates, and dynamic Graviton auto-detection.
- **[RDS Module](modules/rds.html):** Multi-AZ database configuration and parameter group tuning.
- **[Standalone EC2 Module](modules/standalone_ec2.html):** Secure standalone Ubuntu 26.04 LTS development and application environments.
- **[ElastiCache Valkey Module](modules/elasticache.html):** Secure ElastiCache Valkey in-memory caching cluster for session and metadata store.
- **[Jumphost Module](modules/jumphost.html):** Secure public-subnet SSH Jumphost (Bastion) whitelisted for Cyberjaya office with automated downstream ingress configuration.

### Deployment & CI/CD
- **[Automation Scripts](scripts.html):** Details about CLI helpers (`deploy.sh`, `destroy.sh`, `user_data.sh`).
- **[CI/CD Pipeline](cicd.html):** GitHub Actions workflow for automatic formatting, testing, validation, and OIDC deployment.
- **[GitLab EFS CI/CD](gitlab-efs-cicd.html):** Comprehensive guide on GitLab CI/CD, automatic workflows, EFS mounting, dynamic Nginx path configurations, and containerized/S3 alternatives.
- **[Costing Estimate](costing.html):** Comprehensive monthly cost breakdown, local currency estimates, and Day-2 cost optimization pathways.
- **[Production Costing Estimate](production-costing.html):** Comprehensive monthly and annual production-scale cost breakdown from production specifications.

---

## Prerequisites

Before deploying the infrastructure, ensure you have the following tools installed and configured:

- **[OpenTofu](https://opentofu.org/) >= 1.6.0** (Recommended) or **Terraform >= 1.5.0**
- **[AWS CLI](https://aws.amazon.com/cli/)** configured with admin-level credentials for `ap-southeast-5`
- **Git** for repository and revision tracking
