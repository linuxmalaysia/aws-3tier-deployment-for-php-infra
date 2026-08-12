---
layout: default
okf_version: "0.1"
type: "Module Technical Guide"
title: "Auto Scaling Group (ASG) Module"
timestamp: "2026-08-05T22:20:36+08:00"
topics: ["aws", "3-tier", "compute", "autoscaling"]
---

**[DEVOPS EXECUTION]**

# Auto Scaling Group (ASG) Module

This module deploys an Auto Scaling Group (ASG) of EC2 instances spanning multiple Availability Zones. It automates high-availability application scaling and supports dynamic resource scaling based on real-time CPU consumption.

---

## Technical Details

- **Multi-AZ Resilience:** ASG instances are launched strictly inside private subnets, ensuring they are shielded from direct internet exposure.
- **Dynamic Graviton / ARM64 Auto-detection:**
  - The module looks up the official Amazon Linux 2023 AMI dynamically.
  - If the `instance_type` belongs to the AWS Graviton family (e.g., starts with `t4g`, `m6g`, `c6g` etc.), the module automatically switches to fetch the **ARM64** Amazon Linux 2023 AMI. Otherwise, it defaults to the standard **x86_64** AMI.
- **SSM Integration:** Installs and configures IAM instance profiles with `AmazonSSMManagedInstanceCore` policies, allowing administrators to establish secure terminal shell sessions with instances without deploying bastion hosts or opening public SSH ports.
- **Nginx Bootstrapping:** Provisions instances with an automated bootstrapping `user_data` script that updates system packages, installs Nginx, starts the service, and creates a customized region-specific welcome index page.
- **Dynamic CPU Scaling:**
  - **Scale Out:** Triggers when average CPU utilization matches or exceeds **70%** for two consecutive evaluation periods.
  - **Scale In:** Triggers when average CPU utilization falls below or matches **30%** for two consecutive evaluation periods.

---

## Inputs and Outputs

For a detailed list of all input parameters and output values, please refer to the module's inline documentation at [terraform/modules/asg/README.md](../../../terraform/modules/asg/README.md).
