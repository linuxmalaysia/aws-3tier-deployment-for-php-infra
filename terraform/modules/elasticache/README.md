---
layout: default
okf_version: "0.1"
type: Portal
title: "ElastiCache Valkey Module"
timestamp: "2026-08-05T22:20:36+08:00"
topics: ["aws", "3-tier"]
---

# ElastiCache Valkey Module

This module deploys a highly secure, fully managed **Amazon ElastiCache for Valkey** cluster inside the private database subnets of your VPC.

Valkey is a fully open-source, high-performance, key-value data store developed under the Linux Foundation as a drop-in replacement for Redis OSS. It offers identical CLI compatibility and up to **20% lower on-demand pricing** for node-based configurations, or **33% lower** for serverless workloads.

---

## Technical Features

- **Private Isolation:** Placed strictly inside dedicated database subnets.
- **Strict Ingress Firewalling:** Access is limited to port 6379 from the application Auto Scaling Group (`asg_sg_id`) and standalone developer/staging instances (`standalone_sg_id`).
- **Data Encryption:** Transit encryption (TLS/SSL) and at-rest encryption are both enforced.
- **Multi-AZ Failover Support:** Automatically scales from a single node to high-availability multi-AZ replication groups.

---

## Inputs

| Name | Description | Type | Default | Required |
| --- | --- | --- | --- | --- |
| `environment` | Environment name (e.g., production, staging) | `string` | n/a | yes |
| `vpc_id` | The ID of the VPC | `string` | n/a | yes |
| `private_db_subnet_ids` | List of private subnet IDs for the database layer | `list(string)` | n/a | yes |
| `asg_sg_id` | Security group ID of the application ASG instances | `string` | n/a | yes |
| `standalone_sg_id` | Security group ID of the standalone staging instances | `string` | `""` | no |
| `node_type` | Instance type of the Valkey cluster nodes | `string` | `"cache.t4g.micro"` | no |
| `num_cache_clusters` | Number of cache nodes in the replication group | `number` | `1` | no |
| `engine_version` | Engine version of the Valkey cluster | `string` | `"7.2"` | no |
| `parameter_group_name` | Parameter group name to associate with Valkey | `string` | `"default.valkey7"` | no |

---

## Outputs

| Name | Description |
| --- | --- |
| `primary_endpoint_address` | The primary connection endpoint address for the Valkey cluster |
| `security_group_id` | The ID of the security group assigned to the Valkey cluster |
| `subnet_group_name` | The name of the subnet group assigned to the Valkey cluster |
