---
layout: default
okf_version: "0.1"
type: Portal
title: "AWS Standalone EC2 Instance Module"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier"]
---

# AWS Standalone EC2 Instance Module

This module provisions secure Standalone EC2 Instances running **Ubuntu 26.04 LTS** (or other target releases) to support application build-up requirements, development sandboxes, staging tools, or other application resources that are not suited for Auto Scaling Group deployment.

## Core Features

- **Secure Network Isolation:** Deployed strictly in VPC Private Application Subnets with zero direct public ingress. All egress flows securely through NAT Gateways.
- **SSM Managed Core:** Includes pre-packaged IAM instance profiles configured with `AmazonSSMManagedInstanceCore`, enabling secure, passwordless remote Shell administration without requiring public SSH ports or bastion hosts.
- **Dedicated Security Grouping:** Chains ingress dynamically from the public-facing Application Load Balancer (ALB) on port 80/443 for sandbox web access testing.
- **Architectural Flexibility:** Supports dynamic AMI lookups for both ARM64 (Graviton) and x86_64 CPU architectures based on the specified `instance_type`.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `environment` | Environment name for tagging (e.g., production, dev) | `string` | n/a | yes |
| `vpc_id` | The ID of the VPC | `string` | n/a | yes |
| `private_app_subnet_ids` | List of private subnets where instances will reside | `list(string)` | n/a | yes |
| `alb_sg_id` | Security Group ID associated with the public ALB | `string` | n/a | yes |
| `instance_type` | EC2 compute instance size (Graviton-compatible default) | `string` | `"t4g.micro"` | no |
| `ami_id` | Specific AMI ID override (if left empty, AMI is auto-fetched) | `string` | `""` | no |
| `ubuntu_ami_filter_name` | The search pattern name for the Ubuntu AMI | `string` | `"ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-*-server-*"` | no |
| `instance_count` | Number of standalone EC2 instances to provision | `number` | `1` | no |

## Outputs

| Name | Description |
|------|-------------|
| `instance_ids` | The list of generated Standalone EC2 Instance IDs |
| `private_ips` | The list of private IP addresses assigned to the instances |
| `security_group_id` | The ID of the security group assigned to the instances |
