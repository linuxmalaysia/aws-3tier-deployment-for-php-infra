---
layout: default
okf_version: "0.1"
type: Portal
title: "AWS Secure SSH Jumphost (Bastion) Module"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier"]
---

# AWS Secure SSH Jumphost (Bastion) Module

This module provisions a highly secure, cost-optimized SSH Jumphost (Bastion) running inside the VPC's public subnet. It is whitelisted exclusively for incoming connections from your developer office network (e.g., Cyberjaya, Selangor, Malaysia) on port 22.

The module also injects ingress SSH security group rules directly into the Auto Scaling Group (ASG) and Standalone EC2 instances' security groups, allowing developers to establish secure SSH proxying/tunnels into the private environment.

## Core Features

- **Static Public Routing:** Allocates and associates a dedicated AWS Elastic IP (EIP) with the Jumphost, giving developers a stable public IP to configure in their SSH client configurations.
- **Strict Ingress Whitelisting:** Leverages AWS security groups to restrict SSH (TCP port 22) access to the specified office CIDR only, preventing brute-force and port-scanning attempts from other parts of the internet.
- **SSH Chaining to Private Resources:** Attaches managed security group ingress rules to the private subnet ASG and standalone compute groups, enabling passwordless SSH key proxying.
- **Operating System Versatility:** Allows switching between canonical **Ubuntu 24.04/26.04 LTS** (fully compatible with **ASIMP** OS-level hardening) and cloud-optimized **Amazon Linux 2023** via input parameters.
- **SSM-Managed Backup:** Connects to AWS Systems Manager (SSM) by default via an IAM instance profile, providing a safe, passwordless shell backup route for system administrators.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `environment` | Environment name for tagging (e.g., production, dev) | `string` | n/a | yes |
| `vpc_id` | The ID of the VPC | `string` | n/a | yes |
| `public_subnet_ids` | List of public subnet IDs in the VPC | `list(string)` | n/a | yes |
| `instance_type` | EC2 compute instance size (Graviton-compatible default) | `string` | `"t4g.micro"` | no |
| `allowed_ssh_cidr` | IP CIDR allowed to connect to the Jumphost via SSH | `string` | `"103.188.0.0/16"` | no |
| `jumphost_os` | Operating System pattern ('ubuntu' or 'amazon-linux-2023') | `string` | `"ubuntu"` | no |
| `ami_id` | Specific AMI ID override (if left empty, AMI is auto-fetched) | `string` | `""` | no |
| `ubuntu_ami_filter_name` | The search pattern name for the Ubuntu AMI | `string` | `"ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-*-server-*"` | no |
| `asg_sg_id` | Security Group ID associated with the Auto Scaling Group | `string` | n/a | yes |
| `standalone_sg_id` | Security Group ID associated with Standalone EC2 instances | `string` | `""` | no |

## Outputs

| Name | Description |
|------|-------------|
| `jumphost_public_ip` | The static Elastic IP address assigned to the Jumphost |
| `jumphost_private_ip` | The private IP address of the Jumphost within the VPC |
| `security_group_id` | The ID of the security group assigned to the Jumphost |
| `instance_id` | The ID of the Jumphost EC2 instance |
