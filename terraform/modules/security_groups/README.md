---
layout: default
okf_version: "0.1"
type: Portal
title: "AWS Security Groups Module"
timestamp: 2026-08-05T22:20:36+08:00
topics: [aws, 3-tier]
---

# AWS Security Groups Module

This module implements the **Zero-Trust Network Principle** across the 3-Tier topology, strictly defining ingress and egress boundaries for each architectural layer (Presentation/ALB, Application/EC2, and Database/RDS).

## Layered Security Architecture

1. **ALB Security Group (`alb_sg`):**
   - **Ingress:** Allows public inbound traffic from anywhere (`0.0.0.0/0` and `::/0`) on port `80` (HTTP) and port `443` (HTTPS).
   - **Egress:** Allows outbound connections to any destination (restricted locally by target server communication requirements).

2. **ASG/EC2 Security Group (`asg_sg`):**
   - **Ingress:** Restricts inbound connections exclusively to traffic originating from the **ALB Security Group** on the configured application port (default: `80`). No direct internet ingress is permitted.
   - **Egress:** Allows outbound connections to the internet to fetch package updates, operating system patches, and remote software dependencies.

3. **Database Security Group (`db_sg`):**
   - **Ingress:** Restricts database connection ingress exclusively to traffic originating from the **ASG/EC2 Security Group** on the database port (default: `5432` for PostgreSQL, `3306` for MySQL).
   - **Egress:** Fully restricted/blocked for maximum protection against database data exfiltration or external database command abuse.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `vpc_id` | The ID of the VPC where security groups will be deployed | `string` | n/a | yes |
| `environment` | Environment name for tagging (e.g., production, dev) | `string` | n/a | yes |
| `http_port` | Inbound port used for web server connections | `number` | `80` | no |
| `db_port` | Inbound port used for database connections | `number` | `5432` | no |

## Outputs

| Name | Description |
|------|-------------|
| `alb_sg_id` | Security Group ID for the Application Load Balancer |
| `asg_sg_id` | Security Group ID for the Auto Scaling Group instances |
| `db_sg_id` | Security Group ID for the RDS Database instance |
