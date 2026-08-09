---
layout: default
okf_version: "0.1"
type: "Module Technical Guide"
title: "VPC Module"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier", "vpc", "networking"]
---

**[DEVOPS EXECUTION]**

# VPC Module

The VPC Module deploys the foundational multi-AZ networking infrastructure for the 3-tier layout. It partitions the network into public subnets, private application subnets, and isolated private database subnets, ensuring high availability and physical logical boundaries.

---

## Architectural Details

- **VPC (`aws_vpc`):** Created with a custom CIDR (default `10.0.0.0/16`) and has `enable_dns_support` and `enable_dns_hostnames` set to `true` to facilitate intra-VPC DNS resolution.
- **Internet Gateway (`aws_internet_gateway`):** Attached to the VPC to route external traffic to and from the public subnets.
- **Subnets (`aws_subnet`):**
  - **Public Subnets:** Deployed across multiple AZs. Maps public IP addresses automatically on launch. Hosts ALBs and NAT Gateways.
  - **Private App Subnets:** Deployed across multiple AZs. Holds ASG instances. Routes outbound internet traffic via NAT Gateways.
  - **Private DB Subnets:** Dedicated subnets for RDS DB placement. Completely lacks routes to the NAT Gateways or Internet Gateways to minimize access.
- **NAT Gateways (`aws_nat_gateway`):** Provisioned in public subnets with a dedicated Elastic IP (`aws_eip`) in each AZ to provide high-availability outbound routes for instances in private subnets.
- **Route Tables and Associations:** Configured to manage separate traffic routes for public, private application, and database subnets.

---

## Inputs and Outputs

For a detailed list of all input parameters and output values, please refer to the module's inline documentation at [terraform/modules/vpc/README.md](../../../terraform/modules/vpc/README.md).
