---
layout: default
okf_version: "0.1"
type: Changelog
title: Changelog
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier"]
---

# Changelog

All notable changes to the **AWS 3-Tier Deployment for AI & Web Infra** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-04

### Added
- **Amazon ElastiCache for Valkey Module:** Deployed `elasticache` submodule to run license-compliant, cost-effective Valkey clusters in private subnets, delivering a 20% on-demand price discount compared to Redis OSS.
- **Secure SSH Jumphost (Bastion) Module:** Deployed `jumphost` submodule in the public subnet utilizing whitelisted incoming SSH rules restricted exclusively to Cyberjaya developer CIDRs, with automated downstream security group rule injection.
- **Disaster Recovery (DR) and National Sovereignty Guide:** Comprehensive analysis of five DR options, aligning Multi-AZ deployments with AWS DRS continuous block-level replication (Strategy E), local compliance pathways under the Malaysian PDPA (2010 & 2025 CBPDT guidelines), and detailed MYR/USD monthly estimates.
- **RDS PostgreSQL 17 vs. Percona Server 17 Comparison:** Deep technical comparison covering pricing, Patroni/PgBouncer HA layouts, PMM telemetry, and extension differences.
- **GitLab CI/CD & EFS Pipeline Integration:** Advanced guide documenting NFS persistent mounts on ASG compute clusters, metadata performance optimization (`open_file_cache`), and pipeline design alternatives.
- **Hybrid Cloud Integration Guide:** Cost-effective evaluation comparing site-to-site VPN/Direct Connect with API and MCP-proxy cloud-to-on-premise integrations.
- **Pre-baked AMI Hardening Guide:** Guidelines for pre-baking Ubuntu 26.04 LTS AMIs using HashiCorp Packer, Ansible, and the ASIMP system integrity hardening framework.
- **Route 53 & Private Subnet DNS Resolution Guide:** Practical diagnostics covering the Nginx resolver cache bug and Route 53 throttle behaviors.
- **Developer Design Mapping Guide:** Technical playbook detailing the shift from legacy single-node Ubuntu virtual machines to secure AWS-native 3-tier configurations.

### Changed
- **Default Region Optimization:** Updated OpenTofu configurations to default to `ap-southeast-5` (Malaysia) utilizing Graviton-based instances (`t4g.micro` for compute, `db.t4g.micro` for RDS Multi-AZ Postgres 16) for regional cost optimization.
- **CI/CD Pipeline Security:** Transitioned the GitHub Actions workflow to run OpenTofu formatting and planning conditionally only when AWS OIDC role secrets are available, resolving pull request pipeline execution failures from external forks.

### Fixed
- **Nginx Dynamic Resolver Cache:** Resolved Auto Scaling Group connection degradation by implementing dynamic resolver configurations and TTL resets in downstream compute instances.

---

## [0.5.0] - 2026-04-15

### Added
- **AWS WAFv2 Application Protection:** Layer-7 protection with custom rate limiting, core OWASP rule sets, and SQL Injection blocking rules associated with the Application Load Balancer.
- **Auto Scaling Group CPU-based Triggering:** Deployed Launch Templates and scaling policies driving dynamic VM scaling across multiple Availability Zones.

### Changed
- **Subnet Port Isolation:** Tightened security group rules so that private compute clusters only accept traffic from the public-facing ALB security group.

---

## [0.1.0] - 2026-01-10

### Added
- **Core OpenTofu Multi-AZ Blueprint:** Initial project layout with VPC subnets, Internet Gateways, NAT Gateways, and ALB listener configurations.
- **Multi-AZ RDS Module:** Highly-available PostgreSQL database layer isolating storage traffic in deep private subnets with default volume encryption.
