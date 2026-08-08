---
layout: default
okf_version: "0.1"
type: "Module Technical Guide"
title: "ElastiCache Valkey Module"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier", "caching", "valkey"]
---

**[DEVOPS EXECUTION]**

# ElastiCache Valkey Module

The ElastiCache Valkey Module deploys a secure, fully-managed **Amazon ElastiCache for Valkey** cache cluster inside the private database subnets of your VPC.

Valkey is a high-performance, fully open-source key-value database stewarded by the Linux Foundation. It acts as a drop-in replacement for Redis OSS, offering identical client protocol and command compatibility while delivering **20% lower on-demand pricing** for self-designed (node-based) clusters.

---

## Technical Details

- **Deep Private Isolation:** Placed strictly inside dedicated database subnets without internet egress.
- **Valkey Engine Selection:** Uses `valkey` engine with version `7.2` as the default modern cache cluster, avoiding Redis OSS license premium.
- **Transit and At-Rest Encryption:**
  - Enforces TLS in-transit encryption (`transit_encryption_enabled = true`).
  - Enforces AES-256 at-rest encryption (`at_rest_encryption_enabled = true`).
- **Dynamic Ingress Firewalling:**
  - Inbound traffic on port `6379` is allowed exclusively from the application Auto Scaling Group (ASG) Security Group.
  - Optionally allows inbound port `6379` connections from standalone staging/developer instances to support 1:1 environment parity for integration testing.

---

## Inputs and Outputs

For a detailed list of all input parameters and output values, please refer to the module's inline documentation at `terraform/modules/elasticache/README.md`.