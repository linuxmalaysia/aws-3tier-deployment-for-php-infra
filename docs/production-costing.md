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

## Confidentiality & Anonymization Policy

To preserve operational confidentiality and maintain robust security boundaries, all real-world corporate identifiers, proprietary system names, domains, IP ranges, and source namespaces have been systematically anonymized and replaced with standard enterprise placeholders. No original corporate or system names remain in this published document.

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
6. **`secure-app-parking-api-asg`** (Max: 2 instances, 1 active): Specialized IoT parkway API.
7. **`secure-app-gis-mapping-asg`** (Max: 2 instances, 1 active): Spatial and geography mapping system.
8. **`secure-app-integration-gateway-asg`** (Max: 2 instances, 1 active): Outer API Management and lifecycle layer.
9. **`secure-app-staging-checkout-asg`** (Max: 1 instance, 1 active): Staging environment for dynamic integration testing.

Across these 9 functional ASGs, the system runs exactly **20 active EC2 compute instances** in its standard operating capacity.

* **Sizing Specs (Enterprise Plan):** Compute nodes run on **`t4g.medium`** Graviton instances (2 vCPU, 4GB RAM) with **30GB gp3 SSD** root volumes.
* **Sizing Specs (Baseline Plan):** Run on **`t4g.micro`** Graviton instances (2 vCPU, 1GB RAM) with **15GB gp3 SSD** root volumes.

### B. Relational Databases (Amazon RDS)

Provides fully managed, highly available transactional database engines:
* **MariaDB Engine:** Running in Multi-AZ configuration (Primary in `ap-southeast-5a` and standby replication in `ap-southeast-5b` for automatic failover) on `db.m6g.xlarge` (Enterprise) or `db.t4g.micro` (Baseline). Paired with an active Single-AZ Read Replica on `db.m6g.xlarge` / `db.t4g.micro` running in `ap-southeast-5b` for read scaling (the replica does not have its own standby).
* **PostgreSQL Engine:** Running in Multi-AZ configuration on `db.m6g.xlarge` (Enterprise) or `db.t4g.micro` (Baseline) for high-performance spatial/vector operations.

### C. Performance & Caching (ElastiCache for Valkey)

Offloads read-intensive requests and maintains stateless sessions:
* **Valkey API Caching Service:** 1-node single-AZ standalone cache instance (`cache.t4g.medium` for Enterprise; `cache.t4g.micro` for Baseline) dedicated to API query optimization.
* **Valkey Core Session Service:** High-availability Multi-AZ replication group. Under the Enterprise Plan, this is a **3-node** clustered replication group utilizing **`cache.r6g.2xlarge`** instances spanning both AZs with auto-failover, transit encryption, and encryption-at-rest. Under the Baseline Plan, this is simplified to a single-node **`cache.t4g.micro`** instance.

### D. Storage Tier

* **Amazon EFS (`secure-app-shared-storage`):** Shared file system mounted on AZs `ap-southeast-5a/5b` with 1.29 TiB total capacity (distributed as: 44.70 GiB Standard, 410.26 GiB Infrequent Access, and 869.38 GiB Archive Storage).
* **Amazon S3 Object Storage:** 10 buckets containing static assets, cache backups, cross-region backups, and audit logs. Totaling **14.7 GB** and **2.7 Million objects**.

### E. Load Balancing & Security Gateways

* **3x Application Load Balancers (ALBs):**
  1. `secure-app-public-alb` (Internet-facing, routing core traffic).
  2. `secure-app-checkout-alb` (Internet-facing, dedicated to checkout processing isolation).
  3. `secure-app-internal-alb` (Internal, routing microservices communication on port 80/443).
* **AWS WAFv2 Web ACL:** OWASP protections and rate limiting, with an IP allowlist for the Cyberjaya dev office whitelisted for Cyberjaya dev office IP ranges.

---

## 2. Infrastructure Cost Models

All estimations are based on **AWS official pricing rates** in the **`ap-southeast-5` (Malaysia)** region.
* **AWS Price Snapshot Date:** April 25, 2026
* **FX Effective Date:** April 25, 2026 (1 USD = 4.50 MYR)
* **Tax Treatment:** All prices net of local 8.00% SST (Sales and Service Tax) and local sales taxes.
* **Pricing Basis:** Standard On-Demand billing assuming 730 operating hours per month.
* **DR & Hybrid Connect Charges:** Excluded from the baseline and enterprise annual totals below (modeled separately under section 3).

---

### Scenario A: Baseline Cost-Optimized Plan

*Ideal for testing, staging, and development environments where base costs are minimized.*

| Component / Layer | AWS Service Details | Sizing Spec | Driver Qty / Rate | Monthly Cost (USD) | Monthly Cost (MYR) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Compute Tier (ASGs)** | 20x active EC2 ASG instances | `t4g.micro` (ARM64) | 20 * $0.0084/hr * 730 hrs | $122.64 | RM 551.88 |
| **Compute Storage** | EBS volumes for ASG instances | gp3 storage volume | 20 * 15 GB * $0.08/GB-mo | $24.00 | RM 108.00 |
| **Database Tier (RDS)** | MariaDB (Primary Multi-AZ + Single-AZ Replica) + PostgreSQL (Single-AZ) | 3x `db.t4g.micro` | 1 * $0.032/hr (Multi-AZ) + 2 * $0.016/hr (Single-AZ) | $46.72 | RM 210.24 |
| **Database Storage** | Multi-AZ Database SSD Storage | gp3 Multi-AZ / Single | 20 GB (Multi-AZ) * $0.23 + 40 GB (Single-AZ) * $0.115 | $9.20 | RM 41.40 |
| **Cache Tier** | Valkey API Caching + Valkey Core Session | 2x `cache.t4g.micro` | 2 * $0.0125/hr * 730 hrs | $18.26 | RM 82.17 |
| **Network Entrypoint** | AWS WAFv2 (Web ACL + Basic Core Rules) | Regional WAF Rules | $5.00/ACL + $1.00/Rule * 3 + $0.60 (1M reqs) | $8.60 | RM 38.70 |
| **Load Balancing** | 3x Application Load Balancer (ALB) | 3 ALBs | 3 * $0.0225/hr * 730 hrs (base, <1 LCU) | $49.28 | RM 221.76 |
| **Bastion / Utility** | 1x SSH Jumphost + 1x Sandbox Utility EC2 | 2x `t4g.micro` + gp3 | 2 * $6.13 (compute) + 2 * 15GB * $0.08 (storage) | $14.66 | RM 65.97 |
| **Secure Egress** | AWS NAT Gateway (Single NAT Gateway) | AWS NAT Gateway | 1 * $0.045/hr * 730 hrs + 100 GB * $0.045/GB | $37.35 | RM 168.08 |
| **Storage (S3 + EFS)** | 1.29 TiB EFS Storage + S3 Buckets | Standard/IA/Archive EFS | S3 ($4.84) + EFS ($32.36) | $37.20 | RM 167.40 |
| **Network Transit** | AWS Egress Data Transfer | Internet Egress | ~200 GB (100 GB free, remaining @ $0.09/GB) | $9.00 | RM 40.50 |
| **TOTAL (Baseline)** | **Combined monthly operational spend** | | **Sum of all items above** | **$462.09** | **RM 2,079.41** |

* **Annual Baseline Operational Spend:** **$5,545.08 USD / year** (RM 24,952.86 MYR / year)

---

### Scenario B: High-Performance Enterprise Plan

*Designed to meet production service levels, supporting 20 active ASG compute instances alongside dedicated developer utility environments.*

| Component / Layer | AWS Service Details | Sizing Spec | Driver Qty / Rate | Monthly Cost (USD) | Monthly Cost (MYR) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Compute Tier (ASGs)** | 20x active EC2 ASG instances | `t4g.medium` (ARM64) | 20 * $0.0336/hr * 730 hrs | $490.56 | RM 2,207.52 |
| **Compute Storage** | EBS volumes for ASG instances | gp3 storage volume | 20 * 30 GB * $0.08/GB-mo | $48.00 | RM 216.00 |
| **Database Tier (RDS)** | MariaDB (Primary Multi-AZ + Single-AZ Replica) + PostgreSQL (Multi-AZ) | 3x `db.m6g.xlarge` | 2 * $0.608/hr (Multi-AZ) + 1 * $0.304/hr (Single-AZ) | $1,109.60 | RM 4,993.20 |
| **Database Storage** | Multi-AZ Database SSD Storage | gp3 Multi-AZ / Single | 200 GB (Multi-AZ) * $0.23 + 100 GB (Single-AZ) * $0.115 | $57.50 | RM 258.75 |
| **Cache Tier** | Valkey API Caching + Valkey Session Cluster | `cache.t4g.medium` + 3x `cache.r6g.2xlarge` | 1 * $0.062/hr * 730 + 3 * $0.452/hr * 730 | $1,035.14 | RM 4,658.13 |
| **Network Entrypoint** | AWS WAFv2 (Web ACL + Core Rules + 5M requests) | Regional WAF Rules | $5.00/ACL + $1.00/Rule * 3 + $0.60 * 5 (5M reqs) | $11.00 | RM 49.50 |
| **Load Balancing** | 3x Application Load Balancer (ALB) | 3 ALBs + LCU processing | 3 * $0.0225/hr * 730 hrs + LCU processing charges | $84.30 | RM 379.35 |
| **Bastion / Utility** | 1x SSH Jumphost + 1x Sandbox Utility EC2 | 2x `t4g.medium` + gp3 | 2 * $24.53 (compute) + 2 * 30GB * $0.08 (storage) | $53.86 | RM 242.37 |
| **Secure Egress** | AWS NAT Gateway (Dual NAT Gateway) | AWS NAT Gateway | 2 * $0.045/hr * 730 hrs + 500 GB * $0.045/GB | $88.20 | RM 396.90 |
| **Storage (S3 + EFS)** | 1.29 TiB EFS Storage + S3 Buckets | Standard/IA/Archive EFS | S3 ($18.30) + EFS ($38.50) | $56.80 | RM 255.60 |
| **Network Transit** | AWS Egress Data Transfer | Internet Egress | ~1 TB (100 GB free, remaining @ $0.09/GB) | $81.00 | RM 364.50 |
| **TOTAL (Enterprise)** | **Combined monthly operational spend** | | **Sum of all items above** | **$3,115.96** | **RM 14,021.82** |

* **Annual Enterprise Operational Spend:** **$37,391.52 USD / year** (RM 168,261.84 MYR / year)

---

## 3. Cost-Optimization Pathways (Day-2 Operations)

To achieve maximum efficiency on the high-performance setup, we recommend incorporating three progressive optimization methodologies:

1. **RDS Reserved Instances (RI):** Committing to a 1-year or 3-year term for the MariaDB and PostgreSQL `db.m6g.xlarge` instances yields up to **33% savings**, shaving off ~$366.17/month from database compute charges.
2. **Compute Savings Plans:** Committing to EC2 baseline compute usage reduces the run costs of the active 20 ASG instances and Utility hosts by **25%**, which equates to an additional ~$136.10/month in net savings.
3. **EFS Lifecycle Management:** Our EFS shared mount holds exactly 1.29 TiB of files, with 869.38 GiB already stored directly in the **EFS Archive** class (which has a 90-day minimum storage duration and remains unchanged). The remaining **454.96 GiB** currently in EFS Standard and Infrequent Access (IA) is modeled for optimization.
   - Enforcing an `AFTER_90_DAYS` lifecycle rule—based on each file's last access time in the Standard tier—to transition inactive files directly to the EFS Archive class reduces the storage rate from $0.30/GB to $0.01/GB-month.
   - Factoring in transition tiering charges ($0.01 per GB transitioned) and data-access retrieval charges ($0.01 per GB retrieved from Archive/IA) for typical monthly patterns, this results in a net monthly EFS saving of **$82.50 USD / month** (RM 371.25 MYR / month).
