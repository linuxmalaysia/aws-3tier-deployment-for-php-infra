---
layout: default
okf_version: "0.1"
type: "Module Technical Guide"
title: "RDS Module"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier", "database", "rds"]
---

# RDS Module

The RDS Module deploys a secure, fully-managed RDS Database instance running in Multi-AZ configuration to ensure maximum availability and seamless automatic failover in the event of an availability zone outage.

---

## Technical Details

- **Multi-AZ Availability:** Automatically provisions a primary database instance in one AZ and a synchronous hot standby instance in a secondary AZ.
- **Deep Private Isolation:** Placed strictly inside dedicated isolated database subnets without any routes to the internet or NAT gateways.
- **Dynamic Parameter Group Tuning:**
  - Creates a dedicated parameter group with custom database parameters.
  - Automatically adapts the DB parameter group `family` (e.g., `postgres16`, `postgres15`, or `mysql8.0`) based on the selected database engine and major version.
- **Storage Encryption:** Enforces EBS storage encryption (`storage_encrypted = true`) using AWS managed KMS keys.
- **Storage Autoscaling:** Supports storage scale thresholds (from an initial 20 GB up to 100 GB max) to seamlessly accommodate business data growth without manual intervention.

---

## Inputs and Outputs

For a detailed list of all input parameters and output values, please refer to the module's inline documentation at `terraform/modules/rds/README.md`.
