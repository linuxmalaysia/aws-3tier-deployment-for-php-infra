---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "Root Terraform Configuration"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier"]
---

**[DEVOPS EXECUTION]**

# Root Terraform Configuration

The root folder of the `terraform/` directory orchestrates the execution order, specifies environmental variables, defines provider versions, and outputs key service endpoints.

---

## Files Overview

### 1. `providers.tf`
Specifies minimum required Terraform version requirements and registers external providers.
- **Minimum Terraform Version:** `>= 1.5.0`
- **AWS Provider Version:** `~> 5.0`
- **Region configuration:** Dynamically loaded from variables (defaults to `ap-southeast-5`).

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}
```

### 2. `main.tf`
Serves as the central manifest, calling modules in sequential dependency orders (Networking -> Security Groups -> ALB -> WAF -> ASG -> RDS -> Route 53) and passing cross-module attributes.
- **Example:** VPC subnet IDs are fed directly into ALB subnets, ASG subnets, and RDS subnets.
- **Example:** Security Group IDs are automatically mapped to protect dependencies.
- **Example:** Route 53 setup uses the ALB DNS name and Canonical Zone ID to route custom domain aliases.

### 3. `variables.tf`
Declares environmental configurations, default configurations, and input parameter structures.
- **Defaults for Malaysia Deployment:**
  - `aws_region`: `"ap-southeast-5"`
  - `db_engine`: `"postgres"`
  - `db_engine_version`: `"16"`
  - `db_instance_class`: `"db.t4g.micro"` (Graviton architecture)
  - `instance_type`: `"t4g.micro"` (Graviton compute)
  - `enable_route53`: `true` (whether to provision a Route 53 hosted zone and record)
  - `domain_name`: `"linuxmalaysia.com"` (the target root domain name)
  - `subdomain`: `"app"` (the frontend application subdomain)

### 4. `outputs.tf`
Exposes crucial deployment endpoints, such as the public ALB endpoint, the RDS endpoint, the WAF Web ACL ARN, and the Route 53 Name Servers for domain delegation.

```hcl
output "alb_dns_name" {
  value       = module.alb.alb_dns_name
  description = "Public Load Balancer Endpoint"
}

output "rds_endpoint" {
  value       = module.rds.db_instance_endpoint
  description = "Isolated RDS Database Endpoint"
}

output "waf_web_acl_arn" {
  value       = module.waf.waf_web_acl_arn
  description = "WAF v2 Web ACL ARN"
}

output "route53_name_servers" {
  value       = try(module.route53[0].name_servers, [])
  description = "Route 53 delegated Name Servers for registrar configuration"
}

output "route53_fqdn" {
  value       = try(module.route53[0].fqdn, "")
  description = "Route 53 FQDN pointing to the Application Load Balancer"
}
```

### 5. `terraform.tfvars.example`
A template file used to configure local infrastructure credentials and system settings safely. Copy this template before running your deployments:

```bash
cp terraform.tfvars.example terraform.tfvars
```