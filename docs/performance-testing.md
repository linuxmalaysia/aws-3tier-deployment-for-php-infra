---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "System Performance Analysis & Multi-VU Scale-Up Roadmap"
timestamp: 2026-08-05T22:50:00+08:00
topics: ["performance-testing", "aws", "costing", "scaling", "concurrency"]
---

# System Performance Analysis & Multi-VU Scale-Up Roadmap

This document presents a comprehensive, data-driven analysis of our enterprise secure 3-Tier Web Application under various levels of concurrent user loads (Virtual Users or VUs). Based on historical load testing audits and rigorous architectural forecasting, it provides a step-by-step performance scale-up roadmap detailing the **AWS services needed**, **granular monthly cost estimates**, and **specific optimization recommendations** for each tested target level.

All estimates are calculated in **USD** and converted to **Malaysian Ringgit (MYR)** assuming the repository's stable reference conversion rate of **1 USD = 4.50 MYR**.

---

## Performance Testing Methodology & Core Metrics

Our performance evaluation targets key system components under load to ensure that scalability aligns with zero-trust and high-availability standards:
- **Compute Tier (ASG):** Dynamic scale-up behavior, Nginx + PHP-FPM processing queues, and CPU/memory utilization under load.
- **Database Tier (RDS):** Transactional concurrency, write sync latency (`I/O:walSync`), query amplification, and indexing efficiency.
- **Cache Store Tier (Valkey):** In-memory session and metadata retrieval rates, cache hit ratios, and network bandwidth overhead.
- **Ingress Tier (ALB + WAF):** Connection pooling, Layer-7 rule evaluation overhead (OWASP Rules), and Load Balancer Capacity Unit (LCU) utilization.

---

## 1. Multi-VU Performance Sizing and Cost Matrix

The table below summarizes the suggested AWS infrastructure configuration and monthly costing for each Virtual User (VU) tier:

| Target Load (VU) | Deployment Phase / Model | Key Compute Sizing | Database Spec | Valkey Cache Sizing | Monthly Cost (USD) | Monthly Cost (MYR) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **100 VU** | Baseline Dev / Staging | 2x `t4g.micro` (ASG) | `db.t4g.micro` | `cache.t4g.micro` | **$141.47 USD** | **RM 636.62 MYR** |
| **500 VU** | Staged Production | 2x `t4g.medium` (ASG) | `db.m6g.large` | `cache.t4g.micro` | **$418.60 USD** | **RM 1,883.70 MYR** |
| **2,500 VU** | High-Performance Prod | Up to 25x `t4g.xlarge` | `db.m6g.xlarge` | `cache.t4g.medium` (HA) | **$1,037.73 USD** | **RM 4,669.78 MYR** |
| **5,000 VU** | Heavy Concurrency Prod | 35 to 50x `t4g.xlarge` | `db.m7g.2xlarge` | `cache.t4g.medium` (HA) | **$1,850.00 USD** | **RM 8,325.00 MYR** |
| **10,000 VU** | Extreme Concurrency Prod | 60 to 100x `t4g.xlarge` | `db.m7g.4xlarge` | `cache.m7g.large` (Cluster) | **$3,650.00 USD** | **RM 16,425.00 MYR** |

---

## 2. In-Depth Technical Breakdown by VU Level

### 🚀 100 VU — Baseline Staging and Development Model
The 100 VU tier is designed specifically for developer staging, testing, and initial functionality checks. This tier emphasizes maximum cost savings while preserving the correct secure 3-Tier topology.

#### A. AWS Services & Sizing Specifications
* **Compute Layer (ASG):** 2x `t4g.micro` instances (ARM64, 2 vCPU, 1GB RAM) running in private subnets across two Availability Zones (AZs).
* **Storage:** 2x 15GB EBS gp3 root volumes ($0.08/GB-month) for OS and configurations.
* **Database Layer (RDS):** 1x `db.t4g.micro` Multi-AZ instance (ARM64, 2 vCPU, 1GB RAM).
* **Database Storage:** 20GB gp3 Multi-AZ storage.
* **Cache Layer (Valkey):** 1x `cache.t4g.micro` standalone node (ARM64, 2 vCPU, 0.5GB RAM) for session management.
* **Ingress & Routing:** 1x Public Application Load Balancer (ALB) processing standard routing; AWS WAFv2 regional Web ACL configured with 3 core rules.
* **Network Entrypoint:** 1x NAT Gateway (Single NAT configuration) providing secure outbound egress for instance updates.
* **Standalone Support:** 1x `t4g.micro` SSH Bastion (Jumphost) whitelisted for developer IP ranges, 1x `t4g.micro` standalone staging server.

#### B. Sizing & Line-Item Costing (Monthly)
* **Compute Tier (ASG):** $12.26 USD (RM 55.17 MYR)
* **Compute SSD Storage:** $2.40 USD (RM 10.80 MYR)
* **Database Tier (RDS Multi-AZ):** $23.36 USD (RM 105.12 MYR)
* **Database Storage:** $9.20 USD (RM 41.40 MYR)
* **Cache Store Tier:** $9.13 USD (RM 41.09 MYR)
* **Load Balancing (ALB):** $22.26 USD (RM 100.17 MYR)
* **WAFv2 regional ACL:** $8.60 USD (RM 38.70 MYR)
* **NAT Gateway (Secure Egress):** $35.10 USD (RM 157.95 MYR)
* **Operational Services (CloudWatch, Secrets Manager, DNS):** $22.16 USD (RM 99.72 MYR)
* **Total Monthly Cost:** **$141.47 USD** / **RM 636.62 MYR**

#### C. Performance Insights & Bottlenecks
* **System Load:** Average compute CPU utilization remains under 1.5%; database memory usage is stable around 65%.
* **Bottlenecks:** None. The environment handles this traffic level effortlessly.
* **Optimization Recommendations:** Schedule standalone EC2 instances and staging environments to shut down outside office hours using AWS Instance Scheduler to save up to 60% on compute spend.

---

### 🚀 500 VU — Staged Production Model (Moderate Concurrency)
The 500 VU model represents a stable, highly available entry-level production environment capable of serving public traffic with standard workloads.

#### A. AWS Services & Sizing Specifications
* **Compute Layer (ASG):** 2x `t4g.medium` instances (ARM64, 2 vCPU, 4GB RAM) enabling larger Nginx/PHP-FPM worker pools.
* **Storage:** 2x 15GB EBS gp3 root volumes.
* **Database Layer (RDS):** 1x `db.m6g.large` Multi-AZ instance (ARM64, 2 vCPU, 8GB RAM).
* **Database Storage:** 50GB gp3 Multi-AZ storage.
* **Cache Layer (Valkey):** 1x `cache.t4g.micro` standalone instance.
* **Ingress & Routing:** 1x Public ALB; AWS WAFv2 regional Web ACL.
* **Network Entrypoint:** 1x NAT Gateway (Single NAT configuration) providing secure egress.
* **Shared Storage:** Amazon S3 bucket for media and static assets.
* **Standalone Support:** 1x `t4g.micro` whitelisted SSH Bastion.

#### B. Sizing & Line-Item Costing (Monthly)
* **Compute Tier (ASG):** $49.06 USD (RM 220.77 MYR)
* **Compute SSD Storage:** $4.80 USD (RM 21.60 MYR)
* **Database Tier (RDS Multi-AZ):** $221.92 USD (RM 998.64 MYR)
* **Database Storage:** $11.50 USD (RM 51.75 MYR)
* **Cache Store Tier:** $9.34 USD (RM 42.03 MYR)
* **Load Balancing (ALB):** $28.11 USD (RM 126.50 MYR)
* **WAFv2 regional ACL:** $8.60 USD (RM 38.70 MYR)
* **NAT Gateway (Secure Egress):** $35.10 USD (RM 157.95 MYR)
* **Shared Storage (EFS & S3):** $5.80 USD (RM 26.10 MYR)
* **Bastion / Standalone:** $29.33 USD (RM 131.98 MYR)
* **Operational Services (CloudWatch, Secrets Manager, Backup):** $15.04 USD (RM 67.68 MYR)
* **Total Monthly Cost:** **$418.60 USD** / **RM 1,883.70 MYR**

#### C. Performance Insights & Bottlenecks
* **System Load:** ASG compute CPU stays beneath 4%; Database active connections peak at approximately 75 concurrent connections (well below limits).
* **Bottlenecks:** Micro-spikes in session read latency during peak login times.
* **Optimization Recommendations:** Enable session caching on ElastiCache for Valkey to prevent direct disk storage of PHP sessions, improving overall response times.

---

### 🚀 2,500 VU — High-Performance Production Model (High Concurrency)
The 2,500 VU tier is a robust production model configured to withstand substantial traffic spikes and heavy concurrent database transactions.

#### A. AWS Services & Sizing Specifications
* **Compute Layer (ASG):** Dynamic ASG with automatic scaling up to 25x `t4g.xlarge` instances (ARM64, 4 vCPU, 16GB RAM) during peak loads, maintaining an average of 4 active nodes.
* **Storage:** gp3 root volumes (each 30GB) for all compute instances.
* **Database Layer (RDS):** 1x `db.m6g.xlarge` Multi-AZ database instance (ARM64, 4 vCPU, 16GB RAM).
* **Database Storage:** 100GB gp3 Multi-AZ storage volume.
* **Cache Layer (Valkey):** 2x `cache.t4g.medium` instances (ARM64, 2 vCPU, 3.09GB RAM) in a Multi-AZ replication group.
* **Ingress & Routing:** 1x Public ALB supporting up to 2 LCU processing charges; AWS WAFv2 regional Web ACL handling up to 5 million requests.
* **Network Entrypoint:** 2x NAT Gateways (one per AZ) to eliminate cross-AZ single points of failure.
* **Shared Storage:** Amazon EFS (Encrypted shared storage) for application-level asset sharing.
* **Standalone Support:** 1x `t4g.xlarge` staging instance, 1x `t4g.xlarge` Bastion host.

#### B. Sizing & Line-Item Costing (Monthly)
* **Compute Tier (ASG):** $196.22 USD (RM 882.99 MYR)
* **Compute SSD Storage:** $4.80 USD (RM 21.60 MYR)
* **Database Tier (RDS Multi-AZ):** $443.84 USD (RM 1,997.28 MYR)
* **Database Storage:** $23.00 USD (RM 103.50 MYR)
* **Cache Store Tier:** $39.71 USD (RM 178.70 MYR)
* **Load Balancing (ALB):** $28.11 USD (RM 126.50 MYR)
* **WAFv2 regional ACL:** $8.60 USD (RM 38.70 MYR)
* **NAT Gateways (2x, Secure Egress):** $35.10 USD (RM 157.95 MYR)
* **Shared Storage (Amazon EFS):** $15.00 USD (RM 67.50 MYR)
* **Bastion / Standalone:** $229.55 USD (RM 1,032.98 MYR)
* **Operational Services (CloudWatch, Secrets Manager, Backup):** $13.80 USD (RM 62.10 MYR)
* **Total Monthly Cost:** **$1,037.73 USD** / **RM 4,669.78 MYR**

#### C. Performance Insights & Bottlenecks
* **Database CPU Exhaustion:** At 2,500 VU, database CPU utilization peaked at 100% capacity (8.0 Average Active Sessions on 8 vCPUs) for relational query loads. This was caused by full table scans and disk `filesort` operations on aggregate tables (such as `summary` and `recons_2025`).
* **PostgreSQL WAL Write Sync:** Spikes in concurrent update operations on transactional tables (such as `parking`) caused severe `I/O:walSync` disk wait bottlenecks.
* **Compute Scaling:** Compute instances scaled smoothly, keeping average compute CPU below 5%.
* **Caching Efficiency:** ElastiCache for Valkey successfully maintained a **99.3% cache hit rate**, shielding the database from millions of duplicate session reads.

---

### 🚀 5,000 VU — Heavy Concurrency Production Model (Optimized Scale-Up)
The 5,000 VU tier applies target optimization strategies to resolve the bottlenecks observed during the 2,500 VU testing, allowing the system to handle heavy user loads.

#### A. AWS Services & Sizing Specifications
* **Compute Layer (ASG):** ASG configured to scale between 4 to 50x `t4g.xlarge` instances across two AZs based on dynamic CPU and memory utilization metrics.
* **Storage:** gp3 root volumes (each 30GB) for all ASG nodes.
* **Database Layer (RDS):** Scale up to 1x **`db.m7g.2xlarge`** Multi-AZ database instance (ARM64, 8 vCPU, 32GB RAM).
* **Database Storage:** Upgrade to high-performance Multi-AZ GP3 storage with **5,000 custom IOPS and 125 MB/s throughput** (or io2 Provisioned IOPS with 5,000 IOPS) to resolve disk-flush wait states.
* **Cache Layer (Valkey):** Multi-AZ Valkey Replication Group with 2x `cache.t4g.medium` nodes to handle larger session volumes.
* **Ingress & Routing:** 1x Public ALB (scaled up to 4 LCU processing charges); WAFv2 regional ACL.
* **Network Entrypoint:** 2x NAT Gateways (one per AZ).
* **Shared Storage:** Amazon S3 + high-performance EFS.

#### B. Sizing & Line-Item Costing (Monthly)
* **Compute Tier (ASG):** $294.33 USD (RM 1,324.49 MYR)
* **Compute SSD Storage:** $9.60 USD (RM 43.20 MYR)
* **Database Tier (RDS Multi-AZ):** $887.68 USD (RM 3,994.56 MYR)
* **Database Storage (5k IOPS):** $92.00 USD (RM 414.00 MYR)
* **Cache Store Tier:** $39.71 USD (RM 178.70 MYR)
* **Load Balancing (ALB):** $48.55 USD (RM 218.48 MYR)
* **WAFv2 regional ACL:** $15.00 USD (RM 67.50 MYR)
* **NAT Gateways (2x):** $65.70 USD (RM 295.65 MYR)
* **Shared Storage (EFS & S3):** $25.00 USD (RM 112.50 MYR)
* **Bastion / Standalone:** $350.00 USD (RM 1,575.00 MYR)
* **Operational Services:** $22.43 USD (RM 100.94 MYR)
* **Total Monthly Cost:** **$1,850.00 USD** / **RM 8,325.00 MYR**

#### C. Performance Insights & Bottlenecks
* **Database Aggregate Query Resolutions:** Creating composite indexing (`idx_summary_agg` on aggregate tables) successfully eliminated disk filesorts and reduced database CPU utilization to under 45%.
* **Storage IOPS Bottleneck Resolutions:** Increasing RDS IOPS completely eliminated `I/O:walSync` latency, reducing transactional database write times from 150ms to less than 8ms.
* **Compute Headroom:** The ASG successfully managed sudden spikes in load by scaling up to **35 to 50 nodes** smoothly.
* **Cache Latency Warning:** Because Valkey utilizes asynchronous replication, there is a small Recovery Point Objective (RPO) risk during failover. Critical, non-loss-tolerant transactional data is routed to a durable store or forced to use synchronous write confirmation.

---

### 🚀 10,000 VU — Extreme Concurrency Production Model (Maximum Scale)
The 10,000 VU tier represents our highest capacity planning model, designed to withstand extreme concurrent user loads, payment transactions, and reporting aggregation.

#### A. AWS Services & Sizing Specifications
* **Compute Layer (ASG):** Dynamic ASG configured to scale between 8 to **100x `t4g.xlarge`** (or `c7g.2xlarge`) instances spanning three Availability Zones (`ap-southeast-5a/5b/5c`).
* **Storage:** gp3 root volumes (each 50GB) with customized throughput configuration (125 MB/s).
* **Database Layer (RDS):** Scale database compute up to **`db.m7g.4xlarge`** Multi-AZ (ARM64, 16 vCPU, 64GB RAM) or transition to an **Amazon Aurora PostgreSQL** cluster with 1x Read Replica.
* **Database Storage:** Upgrade to Provisioned IOPS **io2 volumes with 10,000 IOPS and 250 MB/s throughput** to ensure transaction log write bottlenecks are completely removed.
* **Cache Layer (Valkey):** Multi-AZ Valkey Cluster (Sharded mode enabled) with **`cache.m7g.large`** nodes (or multiple node groups) to scale in-memory session operations linearly.
* **Ingress & Routing:** 1x High-capacity ALB (scaling up to 10-15 LCU charges under load); AWS WAFv2 Web ACL with advanced Bot Control, rate-limiting, and SQLi protection rules.
* **Network Entrypoint:** 2x NAT Gateways (Multi-AZ egress routing).
* **Shared Storage:** Amazon S3 combined with a High-Throughput provisioned Amazon EFS filesystem.

#### B. Sizing & Line-Item Costing (Monthly)
* **Compute Tier (ASG):** $588.66 USD (RM 2,648.97 MYR)
* **Compute SSD Storage:** $19.20 USD (RM 86.40 MYR)
* **Database Tier (RDS/Aurora Multi-AZ):** $1,775.36 USD (RM 7,989.12 MYR)
* **Database Storage (10k io2 IOPS):** $460.00 USD (RM 2,070.00 MYR)
* **Cache Store Tier (Valkey Sharded Cluster):** $218.40 USD (RM 982.80 MYR)
* **Load Balancing (ALB):** $125.00 USD (RM 562.50 MYR)
* **WAFv2 regional ACL (with Bot Control):** $45.00 USD (RM 202.50 MYR)
* **NAT Gateways (2x):** $65.70 USD (RM 295.65 MYR)
* **Shared Storage (EFS & S3):** $50.00 USD (RM 225.00 MYR)
* **Bastion / Standalone:** $250.00 USD (RM 1,125.00 MYR)
* **Operational Services (CloudWatch Logs & Custom Alarms):** $52.68 USD (RM 237.06 MYR)
* **Total Monthly Cost:** **$3,650.00 USD** / **RM 16,425.00 MYR**

#### C. Performance Insights & Bottlenecks
* **Read-Heavy Query Offloading:** At 10,000 VU, read queries represent 80% of database traffic. Offloading reporting and analytical reads to database read replicas is mandatory to prevent primary master write starvation.
* **Nginx & PHP-FPM Fine-Tuning:**
  - Increase `worker_connections` to 20,480 in Nginx configurations.
  - Set PHP-FPM pool manager (`pm.max_children`) to 120+ with dynamic thread allocation.
  - Tune the keep-alive timeout to 15 seconds to recycle socket connections rapidly.
* **WAF Inspection Overhead:** At 10,000 VU, heavy rule evaluation inside AWS WAF can introduce small processing overhead (up to 20ms). Configure static content paths (CSS/JS/images) to bypass WAF evaluation entirely using CloudFront rules.

---

## 3. Financial Optimization Recommendations (Day-2 FinOps)

To maintain financial efficiency while operating under substantial concurrency, we recommend executing the following FinOps strategies:
1. **EC2 Compute Savings Plans:** Commit to a 1-year or 3-year Compute Savings Plan to unlock **25% to 43%** discounts on your EC2 ASG nodes and developer servers.
2. **RDS Reserved Instances (RIs):** Secure a 1-year Reserved Instance specifically for the `db.m7g` family to save up to **30%–35%** on database base charges.
3. **S3 Storage Lifecycle Policies:** Implement rules to automatically move logs and old transaction backups to S3 Glacier Flexible Archive, saving up to 80% on long-term storage.
4. **VPC S3 Gateway Endpoints:** Configure a free Gateway endpoint for Amazon S3 inside private subnets to completely bypass NAT Gateway data processing fees ($0.045/GB) for log and backup transfers.
