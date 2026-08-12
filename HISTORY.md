---
layout: default
okf_version: "0.1"
type: History
title: "Project History: AWS 3-Tier Deployment for AI & Web Infra"
timestamp: "2026-08-05T22:20:36+08:00"
topics: ["aws", "3-tier"]
---

# Project History: AWS 3-Tier Deployment for AI & Web Infra

This document captures the historical narrative, strategic motivations, and engineering decisions behind the **AWS 3-Tier Deployment for AI & Web Infra** project from Day 0 (its initial design concept) up to the enterprise-grade production-ready v1.0.0 release.

---

## Phase 1: Inception & Legacy Design Alignment (Day 0)

The project began with a legacy baseline single-VM design deployment architecture typically used for fast prototyping: a simple monolithic setup on a single virtual machine (VM) hosting an Nginx web server, a backend service, and a local database instance.

While cost-effective and simple, this legacy approach suffered from critical production-readiness failures:
1. **Single Point of Failure (SPOF):** If the VM crashed or required reboots, the entire web application and backend went offline.
2. **Zero Scalability:** Resource starvation (CPU/Memory exhaustion) on traffic spikes directly impacted database transactions and API responses.
3. **Weak Security Boundary:** Database ports exposed on the same public interface as Nginx meant a single compromised web layer service fully compromised the database.
4. **Data Durability Risk:** Running databases directly on VM ephemeral disks risked loss of transactions during VM termination or host migrations.

### The Alignment Decision
To shift from this fragile design to an enterprise architecture, the core team drafted a secure alignment guide (`docs/developer-design-mapping.md`). The guiding target was to map single-VM components into highly resilient, distributed, managed AWS services under a **Zero-Trust Network Principle**.

---

## Phase 2: OpenTofu & Core Modular Foundations

Rather than hardcoding resources, the team adopted **OpenTofu** (the standard open-source fork of Terraform) to drive the infrastructure-as-code strategy. Compatibility research (`docs/opentofu-migration.md`) demonstrated that OpenTofu offered stable state-locking, enhanced performance, and robust support for AWS regional features, especially in the newly opened **AWS Asia Pacific (Malaysia) region (`ap-southeast-5`)**.

A modular approach was strictly enforced:
* **Networking (`vpc` Module):** Isolated VPC containing pairs of Public subnets (for ALBs and Jumphosts), Private subnets (for ASG compute instances), and deep Isolated Database subnets with no direct routes to the internet.
* **Security Boundaries (`security_groups` Module):** Strict port-level firewalls. Load Balancers only allow HTTP/HTTPS ingress. Compute instances only accept traffic from the ALB. Databases only allow connections on port 5432 originating directly from the ASG or authorized standalone testing instances.
* **Layer-7 Protection (`waf` Module):** Directly integrated AWS WAFv2 with Web ACLs applying OWASP top-10 rulesets, SQL Injection protection, and rate-limiting limits to automatically block DDoS attempts.
* **Compute Provisioning (`asg` Module):** Deployed Auto Scaling Groups utilizing cost-optimized Graviton (ARM64) instances to process incoming traffic across multiple Availability Zones, managed passwordlessly via AWS Systems Manager (SSM) instead of standard vulnerable SSH keys.

---

## Phase 3: Cost Optimization and Day-2 Operational Planning

Moving to a highly-available Multi-AZ architecture naturally raises operational costs compared to a single $5/month VM. To justify the cloud transition, the team developed a thorough pricing study (`docs/costing.md`) tailored to the `ap-southeast-5` region.

### The Valkey Integration
To optimize sessions, cached queries, and reduce RDS transaction load, the team integrated **Amazon ElastiCache for Valkey** (`terraform/modules/elasticache/`). Valkey—the open-source, license-compliant successor to Redis OSS—offered identical key-value performance at a **20% lower on-demand pricing footprint** in the Malaysia region ($0.0128/hr for `cache.t4g.micro`).

### Standalone Baking and Packer/Ansible AMIs
To minimize runtime configuration overhead and boot latency in Auto Scaling Groups, the team designed a staging environment coupling each ASG compute group with a standalone testing EC2 instance (`terraform/modules/standalone_ec2/`). These standalone instances served to test and pre-bake custom Ubuntu 26.04 LTS AMIs hardended via the Ansible System Integrity Management Platform (ASIMP) (`docs/ami-design.md`).

---

## Phase 4: Hybrid Integration, DNS Resiliency, and Disaster Recovery

As enterprise demands expanded, several Day-2 operational challenges arose and were systematically documented and resolved:

1. **DNS Failure Research (`docs/route53.md`):** Resolved typical DNS lookup failures in private subnet instances caused by Nginx dynamic resolver cache issues and Route 53 throttle behaviors.
2. **Hybrid Cloud Evaluator (`docs/hybrid-onprem.md`):** Designed an interface connecting on-premises data centers to AWS, evaluating high-cost corporate links (Direct Connect, VPN) against modern cost-effective API-based and Model Context Protocol (MCP) integrations.
3. **Disaster Recovery Playbook (`docs/dr-options.md`):** Drafted high-availability strategies (RTO/RPO targets) to guarantee business continuity. Crucially, the team incorporated **AWS Elastic Disaster Recovery (AWS DRS)** (Strategy E) as a continuous block-level replication mechanism, modeling low-cost staging areas (`t3.small` replicators and gp3 disks) to comply with local data sovereignty mandates under the Malaysian Personal Data Protection Act (PDPA) 2010.
4. **RDS PostgreSQL vs. Percona PostgreSQL Comparison (`docs/postgresql-comparison.md`):** Evaluated cost, telemetry (PMM), and high availability (Patroni/PgBouncer) of managed AWS RDS PostgreSQL 17 Multi-AZ against self-installed Percona PostgreSQL 17 on EC2 to find the exact trade-off point for large enterprise deployments.

---

## Summary of Accomplishments

Through these phases, the project transitioned from a basic architectural template to an absolute masterclass in enterprise cloud design. The final project provides developers with:
* Ready-to-go OpenTofu modules.
* An OIDC-secured GitHub Actions CI/CD pipeline (`docs/cicd.md`).
* Exhaustive engineering documentation for compliance, hybrid integration, and database operations.
