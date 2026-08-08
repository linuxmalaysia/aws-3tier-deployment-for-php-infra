---
layout: default
okf_version: "0.1"
type: "Module Technical Guide"
title: "Fusio API Server Module"
timestamp: 2026-08-05T22:45:00+08:00
topics: ["aws", "3-tier", "api-gateway", "fusio"]
---

# Fusio API Server Module

The Fusio API Server module deploys a highly secure, scalable, and fully managed API services cluster using [Fusio Project](https://www.fusio-project.org/) natively configured for Nginx, PHP-FPM, and a MariaDB RDS database.

---

## Technical Details

- **Separated ASG Compute Tier:** The Fusio API Server runs inside its own, isolated Auto Scaling Group (ASG) in secure private app subnets, keeping it strictly decoupled from other web frontends or backend applications.
- **Dedicated Developer / Staging Instance:** Provisions a standalone developer and staging server connected to the same staging databases to support active development, testing, and pre-baking AMI verification.
- **Zero-Trust Database Connectivity:** Security group rules (`aws_security_group_rule`) explicitly authorize MariaDB inbound ingress on port 3306 to the main RDS security group *exclusively* from the Fusio ASG and Fusio Standalone security groups.
- **Path-Based ALB Routing:** Leverages Application Load Balancer listener rules to route all incoming API requests under `/api*` and developer portal console requests under `/fusio*` to the active Fusio ASG target group.
- **SSM Remote Management:** All Fusio instances are integrated with AWS Systems Manager (SSM) Core policy for secure, passwordless, agent-based remote management, avoiding direct public SSH exposure.

---

## Inputs and Outputs

For a detailed specification of all input configuration parameters and outputs, refer to the module's inline documentation at `terraform/modules/fusio/README.md`.
