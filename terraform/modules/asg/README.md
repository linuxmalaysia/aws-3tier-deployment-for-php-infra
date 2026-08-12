---
layout: default
okf_version: "0.1"
type: Portal
title: "AWS Auto Scaling Group (ASG) Module"
timestamp: "2026-08-05T22:20:36+08:00"
topics: ["aws", "3-tier"]
---

# AWS Auto Scaling Group (ASG) Module

This module deploys an Auto Scaling Group (ASG) of EC2 instances spanning multiple Availability Zones. It automates high-availability application scaling and supports dynamic resource scaling based on real-time CPU consumption.

## Core Features

- **Multi-AZ Resilience:** ASG instances are launched strictly inside private subnets, ensuring they are shielded from direct internet exposure.
- **Dynamic Graviton / ARM64 Auto-detection:**
  - The module looks up the official Amazon Linux 2023 AMI dynamically.
  - If the `instance_type` belongs to the AWS Graviton family (e.g., starts with `t4g`, `m6g`, `c6g` etc.), the module automatically switches to fetch the **ARM64** Amazon Linux 2023 AMI. Otherwise, it defaults to the standard **x86_64** AMI.
- **SSM Integration:** Installs and configures IAM instance profiles with `AmazonSSMManagedInstanceCore` policies, allowing administrators to establish secure terminal shell sessions with instances without deploying bastion hosts or opening public SSH ports.
- **Nginx Bootstrapping:** Provisions instances with an automated bootstrapping `user_data` script that updates system packages, installs Nginx, starts the service, and creates a customized region-specific welcome index page.
- **Dynamic CPU Scaling:**
  - **Scale Out:** Triggers when average CPU utilization matches or exceeds **70%** for two consecutive evaluation periods.
  - **Scale In:** Triggers when average CPU utilization falls below or matches **30%** for two consecutive evaluation periods.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `environment` | Environment name for tagging (e.g., production, dev) | `string` | n/a | yes |
| `private_app_subnet_ids` | List of private subnets where instances will reside | `list(string)` | n/a | yes |
| `asg_sg_id` | Security Group ID associated with the ASG instances | `string` | n/a | yes |
| `target_group_arn` | The ARN of the ALB Target Group to register instances to | `string` | n/a | yes |
| `ami_id` | Specific AMI ID override (if left empty, AMI is auto-fetched) | `string` | `""` | no |
| `instance_type` | EC2 compute instance size (Graviton-compatible default) | `string` | `"t3.micro"` | no |
| `min_size` | Minimum active instance count in the ASG | `number` | `2` | no |
| `max_size` | Maximum active instance count in the ASG | `number` | `5` | no |
| `desired_capacity` | Desired starting instance count in the ASG | `number` | `2` | no |

## Outputs

| Name | Description |
|------|-------------|
| `asg_name` | The name of the Auto Scaling Group |
| `asg_arn` | The ARN of the Auto Scaling Group |
