---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "Production Infrastructure Costing Analysis"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier", "finops", "costing", "production"]
---

# Production Infrastructure Costing Analysis (ap-southeast-5)

*Note: This document represents the **Sovereign Enterprise Production Cost Model** based on the audited 9-ASG and 3-ALB blueprint. For our developer-focused, staging and SaaS-alternative environment costs, please refer to our separate [AWS Costing Optimization Guide](costing.html) model.*

This document provides a highly granular, transparent, and comprehensive breakdown of the monthly and annual operating costs associated with deploying our enterprise **secure 3-Tier Web Application** on AWS in the **Asia Pacific (Malaysia) Region (`ap-southeast-5`)**. It incorporates real-world systems metrics and performance bottlenecks observed during various load-testing stages, including a detailed roadmap to scale the infrastructure up.

All estimates are calculated in **USD** and converted to **Malaysian Ringgit (MYR)** assuming a stable reference conversion rate of **1 USD = 4.50 MYR**.

---

## Anonymization and Corporate Mapping

In compliance with our confidentiality policy, all proprietary system names, organizational identifiers, and repositories are fully anonymized according to the following mapping:
- `pbtpay` maps to `secure-app`
- `kpkt.gov.my` maps to `enterprise.gov.my`
- `Radmikv2` maps to `EnterpriseRepo`

### Security and TLS Configuration

To maintain strict zero-trust and enterprise compliance, the system enforces the following security standards:
- **Redirection Policy:** All inbound traffic is automatically redirected from unencrypted **HTTP:80 to HTTPS:443** at the Application Load Balancer.
- **SSL/TLS Certificates:** Public endpoints are secured using a wildcard certificate issued via ACM. The certificate's Subject Alternative Name (SAN) set is fully enumerated to cover:
  - `*.enterprise.gov.my` (Wildcard coverage for exactly one level of subdomains, e.g., `app.enterprise.gov.my`, `checkout.enterprise.gov.my`, and `api.enterprise.gov.my`).
  - `enterprise.gov.my` (Explicitly included apex domain to cover the base root domain).
  - *Coverage Limitations:* This certificate does not cover deeper nested subdomain levels (e.g., `v1.api.enterprise.gov.my` or `auth.checkout.enterprise.gov.my`). Public hostnames requiring coverage beyond a single subdomain level must be provisioned with separate certificates.
- **Minimum Protocol Version:** To mitigate vulnerabilities associated with legacy cryptographic protocols, the ALB listener enforces a minimum security policy of **TLS 1.2+**.

---

## Infrastructure Assets Inventory

To ensure robust Availability Zone fault tolerance across two Availability Zones, the system deploys:

### Auto Scaling Groups (Modeled Production Inventory)

The following nine (9) Auto Scaling Groups (ASGs) represent the complete modeled production-scale inventory of the enterprise system as described in our production-scale architectural blueprint (`DRC With HA - AWS PBTPAY`). Note that the local, active Terraform configuration provisions only the core compute ASG tier, but this list captures the fully-scaled production model:
1. **`secure-app-map-my-asg`** (Peta Perkhidmatan, Max = 2)
2. **`secure-app-stag-checkout-my-asg`** (Staging Environment, Max = 1)
3. **`secure-app-apiparking-my-asg`** (Parking API, Max = 6)
4. **`secure-app-dashboardpay-my-asg`** (Pembayaran Dashboard, Max = 6)
5. **`secure-app-apibill-my-asg`** (Bil API, Max = 6)
6. **`secure-app-apicore-my-asg`** (Core API, Max = 8)
7. **`secure-app-checkout-my-asg`** (Checkout API, Max = 8)
8. **`secure-app-fusio-my-asg`** (Fusio API Manager, Max = 4)
9. **`secure-app-main-portal-my-asg`** (Main Portal, Max = 4)

### Ingress & Routing

3x Application Load Balancers (ALBs):
1. `secure-app-my-alb` (Internet-facing public ALB)
2. `secure-app-internal-my-alb` (Dalaman service communications)
3. `secure-app-checkout-my-alb` (Dedicated payment processing load balancer)

* Note: While three ALBs are listed architecturally for design completeness, both Scenario A and Scenario B pricing models in this document include only the provisioned public ALB (`secure-app-my-alb`) to align perfectly with the active modular Terraform configuration.

---

## Cost Breakdown Assumptions and Pricing Citations

All cost estimates utilize regional AWS Price List snapshots dated May 2026 for the Malaysia (`ap-southeast-5`) region:
- **Baseline Hours:** Calculations assume exactly 730 monthly hours per instance/node.
- **Compute (EC2):** Hourly rate of $0.0336 for `t4g.medium` and $0.1344 for `t4g.xlarge` (ARM64 Graviton).
- **Compute SSD Storage (EBS):** $0.08 per GB-month for gp3 volumes.
- **Database (RDS):** Multi-AZ PostgreSQL 1x `db.m6g.large` instance ($0.304/hr) and 1x `db.m6g.xlarge` instance ($0.608/hr).
- **Database SSD Storage:** gp3 Multi-AZ storage rate of $0.23 per GB-month.
- **Valkey Caching:** $0.0128/hr for `cache.t4g.micro` and $0.0544/hr for `cache.t4g.medium` (Valkey engine adoption).
- **Load Balancing (ALB):** Base ALB rate of $0.0225/hr ($16.43/mo) plus 1,460 monthly LCU-hours at $0.008/LCU-hour ($11.68/mo) resulting in $28.11/mo (Baseline and Enterprise scenarios).
- **Secure Egress (NAT):** 1x NAT Gateway base rate of $0.045/hr ($32.85/mo) plus 50GB NAT data processed ($2.25/mo) totaling $35.10/mo.
- **Shared Storage (EFS):** Standard EFS storage rate of $0.30 per GB-month.
- **WAFv2:** Regional WAF Web ACL base fee of $5.00/mo, plus 3 rules (OWASP Core, SQLi, Rate Limit) * $1.00/rule/mo ($3.00/mo), plus requests charged at $0.60 per million.
- **Operational Services:** AWS Backup (RDS/EBS snapshots) at $0.05/GB-month, CloudWatch metrics/dashboards, Secrets Manager at $0.40/secret/mo, and Route 53 zone management.

---

## Architectural Cost Scenarios

We compare two highly optimized deployment configurations below.

### Scenario A: Baseline Cost-Optimized Plan

Designed specifically for staging, development, and low-traffic environments. This plan utilizes smaller resource sizes to maintain network security and separation of concerns while keeping costs low.

| Component / Layer | AWS Service Details | Sizing Spec | Hourly / Unit Rate | Monthly Cost (USD) | Monthly Cost (MYR) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Compute Tier (ASG)** | **Amazon EC2** (Nginx + PHP-FPM) | `t4g.medium` (ARM64) | $0.0336 / hr / inst | $49.06 | RM 220.77 |
| **Compute SSD Storage** | **Amazon Elastic Block Store (EBS)** | gp3 volume | $0.08 / GB-month | $4.80 | RM 21.60 |
| **Database Tier (RDS)** | **Amazon RDS PostgreSQL** (Multi-AZ) | `db.m6g.large` | $0.304 / hr | $221.92 | RM 998.64 |
| **Database SSD Storage** | **Amazon RDS GP3 Volume** | gp3 Multi-AZ | $0.23 / GB-month | $11.50 | RM 51.75 |
| **Cache Store Tier** | **Amazon ElastiCache for Valkey** | `cache.t4g.micro` | $0.0128 / hr | $9.34 | RM 42.03 |
| **Load Balancing** | **Application Load Balancer (ALB)** | 1 ALB Instance | $0.0225 / hr base + LCU | $28.11 | RM 126.50 |
| **Network Entrypoint** | **AWS WAFv2 Web ACL** | Regional Rules | $5.00 / ACL / mo + rules | $8.60 | RM 38.70 |
| **Secure Egress** | **AWS NAT Gateway** | AWS NAT Gateway | $0.045 / hr + data | $35.10 | RM 157.95 |
| **Storage Tier** | **Amazon S3 & EFS** | Encrypted S3 & EFS | Various rates | $5.80 | RM 26.10 |
| **Bastion / Standalone** | **Amazon EC2 Standalone Instances** | `t4g.micro` | $0.0084 / hr | $29.33 | RM 131.98 |
| **Operational Services** | **CloudWatch, Secrets Manager, Backup** | Regional Services | Nominal rates | $15.04 | RM 67.68 |
| **TOTAL** | **Estimated Monthly Baseline Cost** | | | $418.60 | RM 1,883.70 |

* **Annual Baseline Operational Spend:** **$5,023.20 USD** (equivalent to **RM 22,604.40 MYR** per year).

---

### Scenario B: High-Performance Enterprise Plan

Designed for active production workloads, incorporating Multi-AZ high availability and larger instances to support heavy concurrency.

| Component / Layer | AWS Service Details | Sizing Spec | Hourly / Unit Rate | Monthly Cost (USD) | Monthly Cost (MYR) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Compute Tier (ASG)** | **Amazon EC2** (Nginx + PHP-FPM) | `t4g.xlarge` (ARM64) | $0.1344 / hr / inst | $196.22 | RM 882.99 |
| **Compute SSD Storage** | **Amazon Elastic Block Store (EBS)** | gp3 volume | $0.08 / GB-month | $4.80 | RM 21.60 |
| **Database Tier (RDS)** | **Amazon RDS PostgreSQL** (Multi-AZ) | `db.m6g.xlarge` | $0.608 / hr | $443.84 | RM 1,997.28 |
| **Database SSD Storage** | **Amazon RDS GP3 Volume** | gp3 Multi-AZ | $0.46 / GB-month | $23.00 | RM 103.50 |
| **Cache Store Tier** | **Amazon ElastiCache for Valkey** | `cache.t4g.medium` | $0.0544 / hr | $39.71 | RM 178.70 |
| **Load Balancing** | **Application Load Balancer (ALB)** | 1 ALB Instance | $0.0225 / hr base + LCU | $28.11 | RM 126.50 |
| **Network Entrypoint** | **AWS WAFv2 Web ACL** | Regional Rules | $5.00 / ACL / mo + rules | $8.60 | RM 38.70 |
| **Secure Egress** | **AWS NAT Gateway** | AWS NAT Gateway | $0.045 / hr + data | $35.10 | RM 157.95 |
| **Shared Storage** | **Amazon EFS** | Encrypted shared storage | $0.30 / GB-month | $15.00 | RM 67.50 |
| **Bastion / Standalone** | **Amazon EC2 Standalone Instances** | `t4g.xlarge` | $0.1344 / hr | $229.55 | RM 1,032.98 |
| **Operational Services** | **CloudWatch, Secrets Manager, Backup** | Regional Services | Nominal rates | $13.80 | RM 62.10 |
| **TOTAL** | **Estimated Monthly Enterprise Cost** | | | $1,037.73 | RM 4,669.78 |

* **Annual Enterprise Operational Spend:** **$12,452.76 USD** (equivalent to **RM 56,037.42 MYR** per year).

---

## 5,000 VU Performance Insights and Service Recommendations

The historical performance testing results for the `secure-app` system under 100 VU, 500 VU, and 2,500 VU provide critical, actionable insights into planning for a robust **5,000 VU concurrent load**:

1. **Database Layer (The Primary Bottleneck):**
   - **MariaDB Concurrency (Historical/External Test Data):** At 2,500 VU, the DB Load (AAS) peaked at the vCPU limit (8.0 AAS), caused by inefficient queries on `summary` (e.g. `SELECT pbtid, SUM(total)...`) and `recons_2025` forcing full table scans and disk `filesort` I/O wait events (`wait/io/table/sql/handler`). For 5,000 VU, we must scale up DB sizing to **`db.m7g.2xlarge`** and apply composite indexing `idx_summary_agg` on `summary (type, total, pbtid)`.
   - **PostgreSQL Transactions:** At 2,500 VU, PostgreSQL failed due to intense transaction update contention on the `parking` table, driving a massive spike in `I/O:walSync` wait events. For 5,000 VU, we must upgrade PostgreSQL storage. We can either provision custom high-performance **gp3 storage** with 5,000 IOPS and 125 MB/s throughput, or transition to a **Dedicated Provisioned IOPS (io2) volume** with 5,000 Provisioned IOPS to sustain massive concurrent WAL log flushes safely, alongside scaling the database to **`db.m7g.xlarge`** or larger.
2. **Compute Tier Scaling:**
   - During high concurrency (2,500 VU), the Auto Scaling Groups successfully scaled up to 25 instances, keeping the average CPU under 5%. Thus, Graviton-based instances (such as `t4g.medium` or `t4g.xlarge`) are highly recommended. For 5,000 VU, ensure your launch templates and scaling policies allow ASG sizes to reach up to 35-50 nodes seamlessly.
3. **Caching Layer (The MVP):**
   - **Amazon ElastiCache for Valkey** maintained a superb cache hit rate of over 99.3%, shielding the DB from millions of repetitive requests. To sustain 5,000 VU, Valkey caching nodes should be configured in a Multi-AZ replication group (`cache.t4g.medium` or larger). Note that Valkey utilizes asynchronous replication, which carries an inherent Recovery Point Objective (RPO) of a few seconds and a small risk of potential data loss during failovers. For any critical, non-loss-tolerant sessions, they should be directed to a durable session store (like DynamoDB or RDS) or configured to use synchronous Valkey writes.

---

## 3. Cost-Optimization Pathways (Day-2 Operations)

To maximize financial efficiency without compromising on performance or scalability, we recommend the following Day-2 operations:
1. **AWS Savings Plans & Reserved Instances (RIs):**
   - **EC2 Commitment:** Commit to a 1-year or 3-year term **EC2 Compute Savings Plan** (All Upfront or Partial Upfront options), which applies globally to all EC2 instances (including `t4g.medium` and `t4g.xlarge` compute ASGs and standalone developer servers) and delivers **25% - 43%** savings on compute hourly charges.
   - **RDS Commitment:** Commit to 1-year or 3-year term **RDS Reserved Instances** (All Upfront or Partial Upfront options) specifically for Multi-AZ PostgreSQL (`db.m6g.large` or `db.m6g.xlarge`), delivering up to **30% - 45%** savings on database compute.
2. **Private VPC Gateway S3 Endpoints:** Set up a free Gateway endpoint for Amazon S3 to bypass NAT Gateway data processing charges ($0.045/GB) for large document and log transfers.
3. **EFS Lifecycle Management:** Configure policies to transition infrequently accessed shared configuration files to lower-cost Infrequent Access (IA) or Archive storage tiers automatically, saving up to 90%.
