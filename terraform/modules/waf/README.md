---
layout: default
okf_version: "0.1"
type: Portal
title: "AWS WAFv2 Module"
timestamp: 2026-08-05T22:20:36+08:00
topics: [aws, 3-tier]
---

# AWS WAFv2 Module

This module deploys an AWS WAFv2 Web ACL (Web Application Firewall) configured with modern security rules to defend against automated layer-7 attacks, SQL Injection (SQLi) attempts, and brute-force traffic floods.

## Integrated Protections

1. **Common Rule Set (OWASP Top 10 Core Protections):**
   - Implements AWS Managed Common Rules (`AWSManagedRulesCommonRuleSet`) which protect against a wide range of common vulnerabilities, unauthorized administrative path access, and exploitation techniques.
2. **SQLi Defense (SQL Injection Protection):**
   - Implements AWS Managed SQLi Rules (`AWSManagedRulesSQLiRuleSet`) to identify and block malicious SQL injections in query parameters, headers, or request bodies.
3. **IP Rate Limiting:**
   - Adds a custom rate-based rule to restrict the maximum number of requests a single client IP address can send within a sliding 5-minute window (default: `2000` requests).

## Associations

- **ALB Association (`aws_wafv2_web_acl_association`):** Directly attaches the regional Web ACL to the Application Load Balancer ARN to filter traffic at the network edge.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `environment` | Environment name for tagging (e.g., production, dev) | `string` | n/a | yes |
| `alb_arn` | The ARN of the Application Load Balancer to protect | `string` | n/a | yes |
| `rate_limit` | The maximum request threshold per client IP (requests/5 mins) | `number` | `2000` | no |

## Outputs

| Name | Description |
|------|-------------|
| `waf_web_acl_arn` | The ARN of the AWS WAFv2 Web ACL |
