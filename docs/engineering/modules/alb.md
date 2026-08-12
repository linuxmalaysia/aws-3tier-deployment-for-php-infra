---
layout: default
okf_version: "0.1"
type: "Module Technical Guide"
title: "Application Load Balancer (ALB) Module"
timestamp: "2026-08-05T22:20:36+08:00"
topics: ["aws", "3-tier"]
---

**[DEVOPS EXECUTION]**

# Application Load Balancer (ALB) Module

This module deploys a highly available, public-facing Application Load Balancer (ALB) that acts as the entry point for all incoming HTTP web traffic. It handles request distribution and active health checking.

---

## Technical Components

- **Load Balancer (`aws_lb`):** An external, internet-facing application load balancer mapped across multiple public subnets to provide high availability.
- **Target Group (`aws_lb_target_group`):** A target group with active health checks to monitor the health of the underlying EC2 instances managed by the Auto Scaling Group.
  - **Path:** `/`
  - **Protocol:** `HTTP`
  - **Healthy/Unhealthy Threshold:** `3`
  - **Interval:** `30` seconds
  - **Timeout:** `5` seconds
- **Listener (`aws_lb_listener`):** Configured on port `80` (HTTP) to forward traffic to the target group.

---

## Inputs and Outputs

For a detailed list of all input parameters and output values, please refer to the module's inline documentation at [terraform/modules/alb/README.md](../../../terraform/modules/alb/README.md).
