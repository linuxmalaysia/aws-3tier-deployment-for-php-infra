---
layout: default
okf_version: "0.1"
type: "Module Technical Guide"
title: "Web Application Firewall (WAF) Module"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier", "security", "firewall"]
---

# Web Application Firewall (WAF) Module

The WAF Module provisions an AWS WAFv2 Web ACL (Web Application Firewall) configured with modern security rules to defend against automated layer-7 attacks, SQL Injection (SQLi) attempts, and brute-force traffic floods.

---

## Active Protection Rule Sets

1. **Common Rule Set (OWASP Top 10):**
   - Implements AWS Managed Common Rules (`AWSManagedRulesCommonRuleSet`) which protect against standard vulnerabilities, unauthorized administrative path access, and exploitation techniques.
2. **SQLi Defense (SQL Injection Protection):**
   - Implements AWS Managed SQLi Rules (`AWSManagedRulesSQLiRuleSet`) to identify and block malicious SQL injections in query parameters, headers, or request bodies.
3. **IP Rate Limiting:**
   - Adds a custom rate-based rule to restrict the maximum number of requests a single client IP address can send within a sliding 5-minute window (default: `2000` requests).

---

## Edge Association

- **ALB Association (`aws_wafv2_web_acl_association`):** Directly attaches the regional Web ACL to the Application Load Balancer ARN to filter traffic at the network edge.

---

## Inputs and Outputs

For a detailed list of all input parameters and output values, please refer to the module's inline documentation at `terraform/modules/waf/README.md`.
