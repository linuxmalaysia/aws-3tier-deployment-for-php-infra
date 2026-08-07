---
layout: default
okf_version: "0.1"
type: Portal
title: "Route 53 Module"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier"]
---

# Route 53 Module

This module automates the provisioning of a public Amazon Route 53 Hosted Zone and creates an `A` record (Alias) pointing to the Application Load Balancer.

## Features
- Provision public Route 53 Hosted Zone for custom domain registration.
- Provision dynamic DNS routing to Application Load Balancer via `A` Alias records (supporting both root domains and subdomains).
- Output Hosted Zone configuration and Name Servers (NS) for registrar configuration.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `environment` | Environment name (e.g. production, staging) | `string` | n/a | yes |
| `domain_name` | The root domain name (e.g., example.com) | `string` | n/a | yes |
| `subdomain` | The subdomain to point to the ALB (e.g., app). If empty, points to root. | `string` | `""` | no |
| `alb_dns_name` | The DNS name of the Application Load Balancer | `string` | n/a | yes |
| `alb_zone_id` | The Canonical Hosted Zone ID of the Application Load Balancer | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| `hosted_zone_id` | The ID of the Route 53 Hosted Zone |
| `name_servers` | The list of Name Servers assigned to the Hosted Zone |
| `fqdn` | The Fully Qualified Domain Name pointing to the ALB |
