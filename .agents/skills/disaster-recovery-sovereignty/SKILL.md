---
layout: default
okf_version: "0.1"
type: "Agent Skill"
title: "Disaster Recovery, High Availability, and National Sovereignty Skill"
timestamp: "2026-08-13T12:00:00+08:00"
topics: ["disaster-recovery", "high-availability", "compliance", "costing", "sovereignty"]
name: disaster-recovery-sovereignty
description: "Covers procedural guidelines, architecture reviews, costing calculations, and regulatory alignment for disaster recovery and sovereignty configurations."
---

# Disaster Recovery, High Availability, and National Sovereignty Skill

This custom agent skill encapsulates all operational guidelines, architectural matrices, cost-estimation rules, and sovereignty workflows regarding our systems design and compliance under Malaysian regulations.

## When to Use This Skill
- Use this when modifying or analyzing disaster recovery (DR) option designs or costing estimation projections.
- Use this when auditing compliance against Section 129 of the Malaysian Personal Data Protection Act (PDPA).
- Use this when analyzing financial plans, regional cost multipliers, or AWS Pricing Calculator parameters.

## How to Use It (Procedures and Conventions)

### 1. Disaster Recovery Patterns
- **Option Two Malaysia (`docs/executive/dr-option-two-malaysia.md`):** Configures same-region (`ap-southeast-5`) replication using a separate AWS account to protect against account-level ransomware or administrative compromise. Include cross-account IAM mapping, AWS CLI recovery commands, and Pricing Calculator templates.
- **3+1 DR Options Evaluation (`docs/executive/dr-options-evaluation.md`):** Written in UK English. Aligns the CodeIgniter, Valkey, and RDS MariaDB setups with the AWS Disaster Recovery Workloads whitepaper, detailing data plane vs. control plane resilience and classic DR patterns (Pilot Light, Warm Standby, Multi-Site Active-Active, Backup & Restore).
- **Adoption & DR Maturity Roadmap (`docs/executive/aws-adoption-roadmap.md`):** Links run-rate increases to operational DR targets (e.g., hybrid connections, AWS DRS replication triggers).

### 2. Local Currency & Banker's Rounding Costing Constraints
- Project projections assume a standard local exchange rate: **1 USD = 4.50 MYR**.
- When performing cost recalculations, always enforce exact Python float representation rounding (**banker's rounding** / round-to-even) to validate cost values. For example, $1037.73 USD converts exactly to RM 4,669.78 MYR based on standard bank rounding.
- High-Performance and Baseline cost plans must be verified in both `docs/executive/costing.md` and `docs/executive/production-costing.md` using corresponding test checks (`tests/test_costing_recalculation_consistency.py`).

### 3. Architecture Reviews & AWS-Native vs. Self-Hosted Custom Stack
- **Comparative Review (`docs/aws-vs-self-hosted-review.md`):** Detailed analysis for PHP (CodeIgniter & Fusio) architecture.
- **12-Layer Comparison Guide (`docs/engineering/aws-vs-onprem-comparison.md`):** Compares AWS components (ECS, RDS, Cognito, ALB, WAFv2, ElastiCache Valkey) to on-prem self-hosted open-source software alternatives (Podman 5+ with systemd Quadlets, Percona Server for PostgreSQL 17+, Keycloak/Authentik, HAProxy, BunkerWeb WAF, Gitea, and Valkey) using UK English spelling, visual badges, and professional planning liability disclaimers.

---
*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-13*
