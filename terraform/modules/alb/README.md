---
layout: default
okf_version: "0.1"
type: Portal
title: "AWS Application Load Balancer (ALB) Module"
timestamp: 2026-08-05T22:20:36+08:00
topics: [aws, 3-tier]
---

# AWS Application Load Balancer (ALB) Module

This module deploys a highly available, public-facing Application Load Balancer (ALB) that acts as the entry point for all incoming HTTP web traffic. It handles request distribution and provides standard target health checking.

## Architecture

- **Load Balancer (`aws_lb`):** An external, internet-facing application load balancer mapped across multiple public subnets to provide high availability.
- **Target Group (`aws_lb_target_group`):** A standard target group with active health checks to monitor the health of the underlying EC2 instances managed by the Auto Scaling Group.
- **Listener (`aws_lb_listener`):** Configured on port `80` (HTTP) to forward traffic to the target group.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `environment` | Environment name for tagging (e.g., production, dev) | `string` | n/a | yes |
| `vpc_id` | VPC ID where target group and load balancer will run | `string` | n/a | yes |
| `public_subnet_ids` | List of public subnet IDs to distribute the ALB across | `list(string)` | n/a | yes |
| `alb_sg_id` | Security Group ID associated with the ALB | `string` | n/a | yes |
| `http_port` | Inbound port used for web server connections | `number` | `80` | no |

## Outputs

| Name | Description |
|------|-------------|
| `alb_arn` | The Amazon Resource Name (ARN) of the ALB |
| `alb_dns_name` | Public DNS Name of the external Load Balancer |
| `target_group_arn` | The ARN of the ALB Target Group |
