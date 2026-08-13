---
layout: default
okf_version: "0.1"
type: "Agent Skill"
title: "OpenTofu (Terraform) Infrastructure & Cloud Engineering Skill"
timestamp: "2026-08-13T12:00:00+08:00"
topics: ["opentofu", "aws", "architecture", "networking", "compute"]
name: opentofu-cloud-engineering
description: "Covers procedures, standards, and troubleshooting patterns for OpenTofu configurations, network designs, compute nodes, databases, and DNS configurations."
---

# OpenTofu (Terraform) Infrastructure & Cloud Engineering Skill

This custom agent skill incorporates all network designs, compute parameters, database models, and cloud-engineering constraints used within this secure AWS 3-Tier deployment.

## When to Use This Skill
- Use this when working inside `terraform/` or modifying network security controls.
- Use this when modifying compute launch templates or cloud-init user data scripts.
- Use this when configuring database RDS clusters, Valkey caches, or SSM management keys.
- Use this when performing dry-run validations or infrastructure plans.

## How to Use It (Procedures and Conventions)

### 1. Network & Load Balancing Security Boundary
- Public ALB ingress on Port 80 (HTTP) is strictly restricted to internal VPC CIDR ranges (customizable via `http_ingress_cidr_blocks`, defaulting to `["10.0.0.0/16"]`) to satisfy zero-trust network principles. Public external access is strictly limited to HTTPS (port 443).
- Establish microsegmentation with secure security groups: compute nodes accept ingress *only* from the ALB, and RDS accepts ingress *only* from compute nodes.

### 2. Compute Hardening & Secure Metadata Extraction
- **IMDSv2 Enforcement:** Secure EC2 metadata access by requiring session tokens on all launch templates (`metadata_options { http_tokens = "required" }` inside launch templates) to thwart Server-Side Request Forged (SSRF) threats.
- **Async Metadata Retrieval:** Compute bootstrap templates parallelize metadata extraction by executing synchronous `curl` requests in the background (`&`), writing them to safe temporary files created with `mktemp -d` and safely deleted via a shell `trap` on `EXIT`.
- **Administrative Access:** Centralize debugging and terminal access using Systems Manager (SSM) Session Manager instead of direct SSH key injection where possible.

### 3. Databases and Cache State Offloading
- The database tier has been updated from PostgreSQL to RDS MariaDB (version 10.11, port 3306) with native parameter group overrides.
- Compute state is offloaded off-instance using an Amazon ElastiCache for Valkey cluster to enable horizontal ASG scaling.
- Shared persistent storage across ASG instances is managed using Amazon EFS with proper performance tuning.

### 4. Optional DNS & Route 53 Configurations
- Include optional Route 53 alias mappings pointing to the Application Load Balancer.
- Standard troubleshooting patterns for DNS resolution failures (such as resolver cache, systemd-resolved behaviors, query throttling) are documented at `docs/engineering/route53.md`.

### 5. OpenTofu Execution Mandates
- To initialize and validate OpenTofu/Terraform configurations locally without active AWS credentials, use:
  ```bash
  tofu init -backend=false && tofu validate
  ```

---
*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-13*
