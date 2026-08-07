---
layout: default
okf_version: "0.1"
type: Portal
title: "AWS Relational Database Service (RDS) Module"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier"]
---

# AWS Relational Database Service (RDS) Module

This module deploys a secure, fully-managed RDS Database instance running in Multi-AZ configuration to ensure maximum availability and seamless automatic failover in the event of an availability zone outage.

## Features

- **Multi-AZ Availability:** Automatically provisions a primary database instance in one AZ and a synchronous hot standby instance in a secondary AZ.
- **Deep Private Isolation:** Placed strictly inside dedicated isolated database subnets without any routes to the internet or NAT gateways.
- **Dynamic Parameter Group Tuning:**
  - Creates a dedicated parameter group with custom database parameters.
  - Automatically adapts the DB parameter group `family` (e.g., `postgres16`, `postgres15`, or `mysql8.0`) based on the selected database engine and major version.
- **Storage Encryption:** Enforces EBS storage encryption (`storage_encrypted = true`) using AWS managed KMS keys.
- **Storage Autoscaling:** Supports storage scale thresholds (from an initial 20 GB up to 100 GB max) to seamlessly accommodate business data growth without manual intervention.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `environment` | Environment name for tagging (e.g., production, dev) | `string` | n/a | yes |
| `private_db_subnet_ids` | List of isolated private subnets for DB placement | `list(string)` | n/a | yes |
| `db_sg_id` | Security Group ID associated with the database | `string` | n/a | yes |
| `db_engine` | Database engine choice (`postgres`, `mysql`) | `string` | `"mysql"` | no |
| `db_engine_version` | Database engine version | `string` | `"8.0.35"` | no |
| `db_instance_class` | Instance hardware size (e.g., `db.t4g.micro`) | `string` | `"db.t3.micro"` | no |
| `db_allocated_storage` | Initial allocated storage (GB) | `number` | `20` | no |
| `db_max_allocated_storage` | Upper storage scale limit (GB) | `number` | `100` | no |
| `db_name` | Default database schema name to create | `string` | `"mydb"` | no |
| `db_username` | Database administrator username | `string` | `"admin"` | no |
| `db_password` | Database administrator password | `string` | n/a | yes |
| `multi_az` | Enable Multi-AZ configuration | `bool` | `true` | no |
| `db_port` | Inbound communication port | `number` | `3306` | no |

## Outputs

| Name | Description |
|------|-------------|
| `db_instance_endpoint` | The connection endpoint for the database instance |
| `db_instance_arn` | The ARN of the RDS Database instance |
