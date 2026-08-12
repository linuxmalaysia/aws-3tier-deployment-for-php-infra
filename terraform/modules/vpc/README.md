---
layout: default
okf_version: "0.1"
type: Portal
title: "AWS VPC Module"
timestamp: "2026-08-05T22:20:36+08:00"
topics: ["aws", "3-tier"]
---

# AWS VPC Module

This module deploys a highly available, multi-AZ virtual network infrastructure adhering to AWS security best practices. It divides the VPC into public subnets, private application subnets, and isolated private database subnets across specified availability zones (defaulting to the AWS Malaysia region `ap-southeast-5`).

## Architecture

- **VPC (`aws_vpc`):** A custom virtual private cloud with DNS support and DNS hostnames enabled.
- **Internet Gateway (`aws_internet_gateway`):** Connected to the VPC to allow inbound/outbound internet traffic for public subnets.
- **Public Subnets (`aws_subnet`):** Subnets that assign public IP addresses on launch. These host the Application Load Balancer and NAT Gateways.
- **Private App Subnets (`aws_subnet`):** Isolated subnets that do not assign public IPs. Outbound traffic is routed securely via the NAT Gateways. These host the application ASG (EC2 instances).
- **Private DB Subnets (`aws_subnet`):** Isolated subnets without direct NAT or internet routes, providing maximum security for the database (RDS) tier.
- **NAT Gateways (`aws_nat_gateway`):** Deployed in each public subnet with associated Elastic IPs to guarantee high-availability internet access for private app subnets.
- **Route Tables and Associations:** Configured to manage separate traffic routes for public, private application, and database subnets.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `vpc_cidr` | CIDR block for the custom VPC | `string` | `"10.0.0.0/16"` | no |
| `environment` | Environment name for tagging (e.g., production, dev) | `string` | n/a | yes |
| `public_subnet_cidrs` | List of CIDR blocks for public subnets | `list(string)` | n/a | yes |
| `private_app_subnet_cidrs` | List of CIDR blocks for private application subnets | `list(string)` | n/a | yes |
| `private_db_subnet_cidrs` | List of CIDR blocks for private database subnets | `list(string)` | n/a | yes |
| `availability_zones` | List of targeted Availability Zones | `list(string)` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| `vpc_id` | The ID of the created VPC |
| `public_subnet_ids` | List of public subnet IDs |
| `private_app_subnet_ids` | List of private application subnet IDs |
| `private_db_subnet_ids` | List of private database subnet IDs |
