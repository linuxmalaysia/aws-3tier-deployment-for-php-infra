---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "Production Infrastructure Costing Analysis"
timestamp: 2026-08-07T15:00:00+08:00
topics: ["aws", "3-tier", "finops", "costing", "production"]
---

# Production Infrastructure Costing Analysis (Anonymized Model)

This document provides a highly granular, transparent, and comprehensive breakdown of the monthly operating costs associated with deploying our **Enterprise Multi-AZ PHP Secure 3-Tier Web Application** on AWS in the **Asia Pacific (Malaysia) Region (`ap-southeast-5`)**.

The target architecture represents an enterprise-scale system mapped directly from production parameters—comprising nine (9) Auto Scaling Groups (ASGs), three (3) Application Load Balancers (ALBs), multi-engine Amazon RDS instances (MariaDB and PostgreSQL), ElastiCache for Valkey, and hybrid/DR components.

All estimates are calculated in **USD** and converted to **Malaysian Ringgit (MYR)** assuming a stable reference conversion rate of **1 USD = 4.50 MYR**.

---

## Architecture Context

To preserve confidentiality, all real-world corporate identifiers, proprietary system names, domains, IP ranges, and namespaces have been systematically anonymized and replaced with standard enterprise placeholders:
* **`pbtpay`** is anonymized to **`secure-app`**
* **`kpkt.gov.my`** is anonymized to **`enterprise.gov.my`**
* **`Radmikv2`** is anonymized to **`EnterpriseRepo`**
* Specific ASGs are renamed to indicate their standard system-tier function.

---

## 1. System Inventory & Specifications

Based on our production design, the infrastructure consists of the following components across three main layers:

### A. Compute & Auto Scaling (ASGs)
The application logic is partitioned into nine (9) distinct Auto Scaling Groups (ASGs) to enforce Separation of Concerns (SoC) and horizontal scalability, spanning two Availability Zones: `ap-southeast-5a` and `ap-southeast-5b`.
1. **`secure-app-core-api-asg`** (Max: 4 instances, 3 active): Core business logic backend APIs.
2. **`secure-app-billing-api-asg`** (Max: 4 instances, 3 active): Integration of downstream third-party billing services.
3. **`secure-app-checkout-processing-asg`** (Max: 6 instances, 5 active): High-priority payment gateway processing tier.
4. **`secure-app-portal-frontend-asg`** (Max: 3 instances, 2 active): Public-facing web application portal.
5. **`secure-app-analytics-dashboard-asg`** (Max: 5 instances, 3 active): Analytics and reporting dashboard interface.
6. **`secure-app-parking-api-asg`** (Max: 2 instances, 1 active): Specialized IoT parkway API interface.
7. **`secure-app-gis-mapping-asg`** (Max: 2 instances, 1 active): Spatial and geography mapping system.
8. **`secure-app-integration-gateway-asg`** (Max: 2 instances, 1 active): Outer API Management and lifecycle layer.
9. **`secure-app-staging-checkout-asg`** (Max: 1 instance, 1 active): Staging environment for dynamic integration testing.

* **Sizing Specs (Enterprise Plan):** Compute nodes run on **`t4g.medium`** Graviton instances (2 vCPU, 4GB RAM) with **30GB gp3 SSD** root volumes.
* **Sizing Specs (Baseline Plan):** Run on **`t4g.micro`** Graviton instances (2 vCPU, 1GB RAM) with **15GB gp3 SSD** root volumes.

### B. Relational Databases (Amazon RDS)
Provides fully managed, highly available transactional databases:
* **MariaDB Instance Group:** Primary and Read Replica (`db.m6g.xlarge` ARM64 under Enterprise; `db.t4g.micro` under Baseline) running in Multi-AZ configuration. Included automated snapshot backups (7-day retention).
* **PostgreSQL Instance:** Complex spatial/vector database (`db.m6g.xlarge` Multi-AZ under Enterprise; `db.t4g.micro` under Baseline).

### C. Performance & Caching (ElastiCache for Valkey)
Offloads read-intensive requests and maintains stateless sessions:
* **Valkey API Caching Cluster (`cache.t4g.medium`):** Single-node cluster for API performance optimization.
* **Valkey Core Session Cluster (`cache.r6g.2xlarge`):** 3-node multi-AZ replication group with auto-failover, encryption-in-transit, and encryption-at-rest.

### D. Storage Tier
* **Amazon EFS (`secure-app-shared-storage`):** Shared file system mounted on AZs `ap-southeast-5a/5b` with 1.29 TiB total capacity (distributed as: 44.70 GiB Standard, 410.26 GiB Infrequent Access, and 869.38 GiB Archive Storage).
* **Amazon S3 Object Storage:** 10 buckets containing static assets, cache backups, cross-region backups, and audit logs. Totaling **14.7 GB** and **2.7 Million objects**.

### E. Load Balancing & Security Gateways
* **3x Application Load Balancers (ALBs):**
  1. `secure-app-public-alb` (Internet-facing, routing core traffic).
  2. `secure-app-checkout-alb` (Internet-facing, dedicated to checkout processing isolation).
  3. `secure-app-internal-alb` (Internal, routing microservices communication on port 80/443).
* **AWS WAFv2 Web ACL:** OWASP protections and rate-limiting whitelists whitelisting Cyberjaya dev office IP ranges.

---

## 2. Infrastructure Cost Models

Assuming 730 operating hours per month in the **`ap-southeast-5` (Malaysia)** region, here is the comparison between our two principal environments:

### Scenario A: Baseline Cost-Optimized Plan
*Ideal for testing, staging, and development environments where base costs are minimized.*

| Component / Layer | AWS Service Details | Sizing Spec | Monthly Cost (USD) | Monthly Cost (MYR) |
| :--- | :--- | :--- | :--- | :--- |
| **Compute Tier (ASGs)** | 22x EC2 Instances across 9 ASGs | `t4g.micro` (ARM64) | $134.86 | RM 606.87 |
| **Compute Storage** | EBS volumes for ASG instances (330 GB total) | gp3 storage volume | $26.40 | RM 118.80 |
| **Database Tier (RDS)** | MariaDB Cluster (Primary + Replica) + PostgreSQL | 3x `db.t4g.micro` (Multi-AZ) | $70.08 | RM 315.36 |
| **Database Storage** | Multi-AZ Database SSD Storage (120 GB total) | gp3 Multi-AZ | $27.60 | RM 124.20 |
| **Cache Tier** | Valkey API Caching + Valkey Core Session | `cache.t4g.micro` | $18.26 | RM 82.17 |
| **Network Entrypoint** | AWS WAFv2 (Web ACL + Basic Core Rules) | Regional WAF Rules | $8.60 | RM 38.70 |
| **Load Balancing** | 3x Application Load Balancer (ALB) | 3 ALBs | $66.78 | RM 300.51 |
| **Bastion / Utility** | 1x SSH Jumphost + 1x Sandbox Utility EC2 | 2x `t4g.micro` + gp3 | $21.32 | RM 95.94 |
| **Secure Egress** | AWS NAT Gateway (Single NAT Gateway + 100 GB) | AWS NAT Gateway | $37.35 | RM 168.08 |
| **Storage (S3 + EFS)** | 1.29 TiB EFS Storage + S3 Buckets | Standard/IA/Archive EFS | $48.50 | RM 218.25 |
| **Network Transit** | AWS Egress Data Transfer (~200 GB) | Internet Egress | $9.00 | RM 40.50 |
| **TOTAL (Baseline)** | **Combined monthly operational spend** | | **$468.75** | **RM 2,109.38** |

* **Annual Baseline Operational Spend:** **$5,625.00 USD / year** (RM 25,312.50 MYR / year)

---

### Scenario B: High-Performance Enterprise Plan
*Designed to meet production service levels, supporting up to 22 concurrent high-performance Graviton nodes under full-load autoscaling.*

| Component / Layer | AWS Service Details | Sizing Spec | Monthly Cost (USD) | Monthly Cost (MYR) |
| :--- | :--- | :--- | :--- | :--- |
| **Compute Tier (ASGs)** | 22x EC2 Instances active across 9 ASGs | `t4g.medium` (ARM64) | $539.44 | RM 2,427.48 |
| **Compute Storage** | EBS volumes for ASG instances (660 GB total) | gp3 storage volume | $52.80 | RM 237.60 |
| **Database Tier (RDS)** | MariaDB Cluster (Primary + Replica) + PostgreSQL | 3x `db.m6g.xlarge` (Multi-AZ) | $1,331.52 | RM 5,991.84 |
| **Database Storage** | Multi-AZ Database SSD Storage (300 GB total) | gp3 Multi-AZ | $69.00 | RM 310.50 |
| **Cache Tier** | Valkey API Caching + Valkey Session Cluster | `cache.t4g.medium` + 3x `cache.r6g.2xlarge` | $1,036.60 | RM 4,664.70 |
| **Network Entrypoint** | AWS WAFv2 (Web ACL + Core Rules + 5M requests) | Regional WAF Rules | $11.00 | RM 49.50 |
| **Load Balancing** | 3x Application Load Balancer (ALB) | 3 ALBs + LCU processing | $84.30 | RM 379.35 |
| **Bastion / Utility** | 1x SSH Jumphost + 1x Sandbox Utility EC2 | 2x `t4g.medium` + gp3 | $53.86 | RM 242.37 |
| **Secure Egress** | AWS NAT Gateway (Dual NAT Gateway + 500 GB) | AWS NAT Gateway | $88.20 | RM 396.90 |
| **Storage (S3 + EFS)** | 1.29 TiB EFS Storage + S3 Buckets | Standard/IA/Archive EFS | $56.80 | RM 255.60 |
| **Network Transit** | AWS Egress Data Transfer (~1 TB) | Internet Egress | $81.00 | RM 364.50 |
| **TOTAL (Enterprise)** | **Combined monthly operational spend** | | **$3,404.52** | **RM 15,320.34** |

* **Annual Enterprise Operational Spend:** **$40,854.24 USD / year** (RM 183,844.08 MYR / year)

---

## 3. Cost-Optimization Pathways (Day-2 Operations)

To achieve maximum efficiency on the high-performance setup, we recommend incorporating three progressive optimization methodologies:

1. **RDS Reserved Instances (RI):** Committing to a 1-year or 3-year term for the MariaDB and PostgreSQL `db.m6g.xlarge` instances yields up to **33% savings**, shaving off ~$440.00/month from database compute charges.
2. **Compute Savings Plans:** Committing to EC2 baseline compute usage reduces the run costs of the active 22 ASG instances and Utility hosts by **25%**, which equates to an additional ~$148.00/month in net savings.
3. **EFS Lifecycle Management:** Since our EFS shared mount maps 869.38 GiB of the 1.29 TiB to cold archival tiers, enforcing lifecycle rules to transition files to **EFS Archive** after 90 days reduces storage rates from $0.30/GB to just $0.01/GB-month.
