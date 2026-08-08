---
layout: default
okf_version: "0.1"
type: "Module Technical Guide"
title: "Fusio API Server Module"
timestamp: 2026-08-05T22:45:00+08:00
topics: ["aws", "3-tier", "api-gateway", "fusio"]
---

# Fusio API Server Module

This module deploys a secure, auto-scaled, and highly-available Fusio API Server infrastructure connected to a MariaDB RDS database, alongside a standalone development/staging instance.

*Note: The current deployment bootstraps Nginx and PHP-FPM with a mock/placeholder Fusio console landing page, representing the API Server without a live active Fusio database connection or full engine installation.*

## Features

- **Dedicated Compute Tier:** Deploys a dedicated Auto Scaling Group (ASG) running Fusio API Server, separated from frontend Nginx or other tiers.
- **Zero-Trust Network Principle:** Restricts inbound database traffic strictly on port 3306 from only the Fusio ASG security group and standalone security group.
- **ALB Path-Based Routing:** Seamlessly routes `/api*` and `/fusio*` traffic to the Fusio target group on the Application Load Balancer.
- **Staging and Testing Parity:** Includes a conditional standalone staging/development server that has the same connectivity and runtime configuration for pre-baking compliance.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `environment` | Environment name for tagging (e.g., production, dev) | `string` | n/a | yes |
| `vpc_id` | The ID of the VPC where resources are deployed | `string` | n/a | yes |
| `private_app_subnet_ids` | List of private subnets for placement | `list(string)` | n/a | yes |
| `alb_sg_id` | Security Group ID of the Application Load Balancer | `string` | n/a | yes |
| `db_sg_id` | Security Group ID of the main RDS database layer | `string` | n/a | yes |
| `https_listener_arn` | The ARN of the HTTPS listener on the ALB | `string` | n/a | yes |
| `instance_type` | EC2 hardware size for ASG instances (e.g., `t4g.micro`) | `string` | `"t4g.micro"` | no |
| `min_size` | Minimum size of the ASG | `number` | `2` | no |
| `max_size` | Maximum size of the ASG | `number` | `4` | no |
| `desired_capacity` | Desired capacity of the ASG | `number` | `2` | no |
| `enable_standalone` | Whether to enable a standalone dev EC2 instance | `bool` | `true` | no |
| `standalone_instance_type`| Hardware size for the standalone dev EC2 instance | `string` | `"t4g.micro"` | no |
| `db_port` | Database connection port | `number` | `3306` | no |
| `ami_id` | AMI ID override for the launch template / instances | `string` | `""` | no |
| `ubuntu_ami_filter_name` | AMI search filter pattern for Ubuntu Server | `string` | `"ubuntu/images/hvm-ssd-gp3/ubuntu-resolute-26.04-*-server-*"` | no |

## Outputs

| Name | Description |
|------|-------------|
| `asg_name` | The name of the Fusio API Server Auto Scaling Group |
| `standalone_instance_id` | The ID of the Fusio Standalone Dev EC2 instance |
