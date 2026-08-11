---
layout: default
okf_version: "0.1"
type: "Module Technical Guide"
title: "Standalone EC2 Instance Module"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier"]
---

**[DEVOPS EXECUTION]**

# Standalone EC2 Instance Module

This module provisions secure Standalone EC2 Instances, standardly defaulting to **Ubuntu 24.04 LTS** (fetched via `data.aws_ami.ubuntu_canonical`). Running other operating systems—including other Debian-derived releases (Ubuntu 26.04, Debian 11/12), RHEL-derived distributions (RHEL 9/10, AlmaLinux, Rocky Linux, Oracle Linux), or Amazon Linux 2023—is fully supported but requires passing an explicit compatible `ami_id` variable override and supplying matching bootstrap configurations.

---

## Technical Details

- **Secure Network Isolation:**
  - Standalone instances are launched strictly inside the **VPC Private Application Subnets**.
  - They do not have public IP addresses and are completely hidden from direct public internet ingress.
  - Outbound traffic (e.g., package updates via package managers like `apt-get`/`dnf`, package validation, and security auditing scans via `ASIMP`) is securely routed through the managed NAT Gateways.
- **SSM Integration:**
  - Deploys dedicated IAM Roles and Instance Profiles with `AmazonSSMManagedInstanceCore` policies attached.
  - Enables developers to establish secure terminal shell sessions with standalone instances using AWS Systems Manager (SSM) without setting up bastion hosts or opening public SSH ports.
- **Chained Security Grouping:**
  - Deploys a dedicated security group (`standalone-ec2-sg`) for standalone instances.
  - Restricts inbound traffic on port 80/443 strictly to the Application Load Balancer (ALB) security group, enabling developers to run web-facing test services or APIs behind the secure ALB.
- **Bootstrapping user_data:**
  - Standardizes initial packages, applies upgrades, and installs Nginx as a placeholder server.
  - Ready to run custom ASIMP (Ansible System Integrity Management Platform) hardening playbooks.

---

## Inputs and Outputs

For a detailed list of all input parameters and output values, please refer to the module's inline documentation at [terraform/modules/standalone_ec2/README.md](../../../terraform/modules/standalone_ec2/README.md).
