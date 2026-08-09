---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "AWS Secure App Performance Analysis & Load Testing Report"
timestamp: 2026-08-06T12:00:00+08:00
topics: ["performance-testing", "aws", "scaling", "bottlenecks", "concurrency"]
---

**[DEVOPS EXECUTION]**

# AWS Secure App Performance Analysis & Load Testing Report

This document presents a comprehensive performance analysis and root cause investigation of our enterprise secure 3-Tier Web Application under various levels of concurrent user loads (Virtual Users or VUs). Based on actual system performance audits under the load testing reports (*"Analisa Sistem Semasa dan Selepas Ujian Prestasi AWS Secure App"*), we map the technical outcomes against the infrastructure costing projections.

For full alignment, this report correlates directly with the **[System Performance Analysis & Multi-VU Scale-Up Roadmap](performance-testing.html)**, detailing the dual impact of traffic loads on both system performance and financial costing.

---

## Performance & Cost Correlation Matrix

| Target Load (VU) | Deployment Phase / Model | Monthly Cost (USD) | Performance Status | Critical Bottleneck Identified | Mapping to Cost & Sizing Reference |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **100 VU** | Baseline Dev / Staging | **$141.47 USD** | **PASS (Cemerlang)** | None (System is highly idle) | [100 VU Sizing Specs](performance-testing.html#100-vu--baseline-staging-and-development-model) |
| **500 VU** | Cost-Optimized Staged Model | **$418.60 USD** | **PASS (Cemerlang)** | Single Points of Failure (Non-HA Valkey & NAT) | [500 VU Sizing Specs](performance-testing.html#500-vu--cost-optimized-staged-model) |
| **2,500 VU** | High-Performance Prod | **$1,236.03 USD** | **FAIL (Bottleneck)** | RDS MariaDB Query CPU & PostgreSQL storage write sync | [2,500 VU Sizing Specs](performance-testing.html#2500-vu--high-performance-production-model-high-concurrency) |
| **5,000 VU** | Heavy Concurrency Prod | **$1,948.12 USD** | **PASS (Optimized)** | Resolving 2,500 VU issues via custom indexing & PIOPS | [5,000 VU Sizing Specs](performance-testing.html#5000-vu--heavy-concurrency-production-model-optimized-scale-up) |
| **10,000 VU** | Extreme Concurrency Prod | **$3,808.88 USD** | **PASS (Maximum Scale)** | WAF rules overhead, PHP-FPM / Nginx worker limits | [10,000 VU Sizing Specs](performance-testing.html#10000-vu--extreme-concurrency-production-model-maximum-scale) |

All estimates assume the stable conversion rate of **1 USD = 4.50 MYR**.

---

## 1. Technical Breakdown by VU Load Level

### 🚀 Ujian Prestasi 100 VU

The 100 VU load test acts as our baseline benchmark to verify basic multi-tier functionality and network routing under steady traffic.

#### A. Test Conditions

* **Date & Start Time:** October 6, 2025, 10:10 PM
* **Date & End Time:** October 6, 2025, 10:19 PM
* **Ramp-up Duration:** 3 minutes (from 10:10 PM to 10:13 PM)
* **Steady-State Duration:** 6 minutes (from 10:13 PM to 10:19 PM)

#### B. Component Performance Results

* **Compute Layer (ASG):** **PASS (Cemerlang)**. CPU utilization on all application servers remained under **0.5%**. There was no Nginx queue buildup or packet loss.
* **Cache Layer (Valkey):** **PASS (Cemerlang)**. Deployed as a single `cache.t4g.small` instance. It successfully maintained a **99.37% Cache Hit Rate** (approximately 43,000 hits vs. 250 misses per 5-minute interval).
* **Database Layer (RDS MariaDB):** **PASS (Cemerlang)**. Database Load remained extremely low with Average Active Sessions (AAS) hovering between **0.5 to 1.0 sessions**.
* **Database Layer (RDS PostgreSQL):** **PASS (Cemerlang)**. Completely idle throughout the test (0.0 AAS).

#### C. Problems Encountered & Root Causes

No performance problems were encountered. The application tier, cache cluster, and database engines easily absorbed the traffic.

#### D. Recommendations & Sizing Mapping

* Maintain the standard cost-saving `t4g.micro` and `db.t4g.micro` setup for development staging as described in the **[100 VU Costing Guide](performance-testing.html#vu--baseline-staging-and-development-model)**.
* Implement AWS Instance Scheduler to automate the shutdown of dev environments outside of office hours to save up to 60% on billing.

---

### 🚀 Ujian Prestasi 500 VU

The 500 VU test evaluates system scalability under moderate workload spikes and assesses caching efficiency under increased login activity.

#### A. Test Conditions

* **Date & Start Time:** October 6, 2025, 10:22 PM
* **Date & End Time:** October 6, 2025, 10:42 PM
* **Ramp-up Duration:** 8 minutes (from 10:22 PM to 10:30 PM)
* **Steady-State Duration:** 12 minutes (from 10:30 PM to 10:42 PM)

#### B. Component Performance Results

* **Compute Layer (ASG):** **PASS (Cemerlang)**. Average compute CPU remained under **4.0%**. No server failures occurred.
* **Cache Layer (Valkey):** **PASS (Cemerlang)**. Deployed on `cache.t4g.small`. Cache requests peaked at **190,000 hits** and **1,100 misses** per 5-minute interval during steady-state. CPU utilization of Valkey was extremely low, indicating massive capacity headroom.
* **Database Layer (RDS MariaDB):** **PASS (Cemerlang)**. Database activity remained nearly flat (AAS close to 0), proving that the Valkey cache layer successfully intercepted almost all read/lookup requests.
* **Database Layer (RDS PostgreSQL):** **PASS (Cemerlang)**. Stable, near-idle performance.

#### C. Problems Encountered & Root Causes

* **Micro-Spikes in Session Retrieval:** During peak login times, very minor, micro-second latency spikes were observed on session lookup queries.
* **Single Points of Failure (SPOFs):** The database caching node and NAT Gateway configurations were non-HA in this baseline setup. A failure of the single cache node would instantly redirect massive traffic to the database, causing a cascading collapse.

#### D. Recommendations & Sizing Mapping

* To support workloads up to 500 VU reliably in staging and QA environments, adopt the specifications in the **[500 VU Sizing Specs](performance-testing.html#vu--cost-optimized-staged-model)**.
* To transition safely to production, eliminate single points of failure by upgrading the cache layer to a Multi-AZ Valkey Replication Group with 2x `cache.t4g.medium` nodes and setting up dual NAT Gateways.

---

### 🚀 Ujian Prestasi 2,500 VU (Critical Transition Point)

The 2,500 VU test serves as a major stress-test milestone representing full production capacity. This load exposed critical architectural limitations on the database tier.

#### A. Test Conditions

* **Date & Start Time:** October 6, 2025, 11:24 PM
* **Date & End Time:** October 6, 2025, 11:54 PM
* **Ramp-up Duration:** 10 minutes (from 11:24 PM to 11:34 PM)
* **Steady-State Duration:** 20 minutes (from 11:34 PM to 11:54 PM)

#### B. Component Performance Results

* **Compute Layer (ASG):** **PASS (Cemerlang)**. The dynamic Auto Scaling Groups scaled up aggressively from baseline to **25 active instances** (`GroupMinSize = 25`) across multiple Availability Zones. Average compute CPU utilization per instance stayed below **5.0%**.
* **Cache Layer (Valkey):** **PASS (Cemerlang)**. Maintained a **99.36% Cache Hit Rate**, successfully offloading billions of session and read queries from the primary database.
* **Database Layer (RDS MariaDB):** **FAIL (Bottleneck)**. Database load surged to a peak of **8.0 AAS** on the **8-vCPU** `db.m7g.2xlarge` test configuration. While CPU-active load remained low (approximately **1.5 AAS**, yielding around **18.75% CPU utilization**), the system was bottlenecked by storage waits, with approximately **6.5 AAS** blocked on handler wait states.
* **Database Layer (RDS PostgreSQL):** **FAIL (Bottleneck)**. Database load spiked from idle to severe write congestion, heavily dominated by disk flush wait states.

#### C. Problems Encountered & Root Causes

##### 1. RDS MariaDB Query Wait Event Bottleneck

* **Problem:** Average Active Sessions (AAS) peaked at **8.0 AAS** on the **8-vCPU** `db.m7g.2xlarge` test configuration, causing transaction delays. The metrics breakdown reveals:
  - **Total Database Load (AAS):** **8.0 AAS**.
  - **CPU-Active AAS:** Approximately **1.5 AAS** actively running on CPU.
  - **CPU Utilization:** Approximately **18.75%** of physical capacity (based on 1.5 active sessions across 8 vCPUs), indicating the instance was not CPU-starved.
  - **Wait-State Breakdown:** Dominated by `wait/io/table/sql/handler` (approximately **6.5 AAS**), representing sessions blocked on row retrieval and table handling.
* **Root Cause:** A complete absence of composite indexes on aggregate tables (such as `summary` and `recons_2025`). This forced the database engine to perform **full table scans** and expensive **disk filesort** operations for heavy analytical lookups.
* **Dominant Wait Metric:** `wait/io/table/sql/handler` (processes waiting for disk and table lookups).
* **Anonymized SQL Query Contributors:**

  ```sql

  SELECT tenant_id, SUM(total) AS total
  FROM summary
  WHERE status = ?
  GROUP BY tenant_id;

  SELECT *
  FROM recons_2025
  WHERE reference_id = ?
    AND is_reconciled = ?;

  ```

##### 2. RDS PostgreSQL Storage WAL Write Congestion (I/O Bottleneck)

* **Problem:** Database load spiked into severe congestion, delaying transactional updates.
* **Root Cause:** High concurrency of UPDATE queries on the `parking` table. The default gp3 storage volume ran out of write capability under sustained, concurrent transactional traffic, forcing the PostgreSQL backend processes to stall while waiting to flush the Write-Ahead Log (WAL) to disk.
* **Dominant Wait Metric:** `I/O:walSync` (backend processes stalled waiting for disk-flush confirmation).
* **Anonymized SQL Query Contributor:**

  ```sql

  UPDATE "parking"
  SET "end_ts" = ?, "is_extend" = ?, "trxid" = ?, "updated_at" = ?
  WHERE "refno" = ? AND "user_id" = ?;

  ```

#### D. Recommendations & Sizing Mapping

* Immediately execute database tuning and storage upgrades. It is critical to scale the database specs to `db.m7g.2xlarge` with Provisioned IOPS as detailed in the **[2,500 VU Sizing Specs](performance-testing.html#vu--high-performance-production-model-high-concurrency)**.
* **Composite Index Remediation:**
  - Create a composite index on the MariaDB `summary` table: `idx_summary_agg (status, tenant_id, total)`.
  - Create a composite index on the MariaDB `recons_2025` table: `idx_recons_lookup (reference_id, is_reconciled)`.
  - Create a composite index on the PostgreSQL `parking` table: `idx_parking_lookup (refno, user_id)` to optimize lookup efficiency under dynamic transactional updates.
* **Storage Performance Remediation:** Upgrade PostgreSQL storage from GP3 General Purpose to **io2 Provisioned IOPS (PIOPS) with at least 5,000 IOPS** to resolve the `I/O:walSync` sync-latency bottleneck.

---

### 🚀 Ujian Prestasi 5,000 VU (Post-Tuning Verification)

At the 5,000 VU tier, the target optimizations designed from the 2,500 VU failures were deployed and tested to verify stability under heavy production load.

#### A. Test Conditions

* **Date & Start Time:** October 6, 2025, 11:59 PM
* **Date & End Time:** October 7, 2025, 12:34 AM
* **Ramp-up Duration:** 15 minutes (from 11:59 PM to 12:14 AM, Oct 7)
* **Steady-State Duration:** 20 minutes (from 12:14 AM to 12:34 AM, Oct 7)

#### B. Component Performance Results

* **Compute Layer (ASG):** **PASS (Optimized)**. Scaled up dynamically to **35 - 50 active EC2 nodes** (`t4g.xlarge` instances). Application server CPU remained under **45%** average utilization, comfortably handling the increased load.
* **Cache Layer (Valkey):** **PASS (Optimized)**. Deployed as a Multi-AZ replication group with 2x `cache.t4g.medium` nodes, successfully serving **99.3%** of read operations from memory.
* **Database Layer (RDS MariaDB):** **PASS (Optimized)**. Deployed on a `db.m7g.2xlarge` instance class. Thanks to the newly created composite indexes (`idx_summary_agg` and `idx_recons_lookup`), full table scans and disk filesorts were eliminated, dropping DB CPU utilization to below **45%** (under 4.0 AAS).
* **Database Layer (RDS PostgreSQL):** **PASS (Optimized)**. Deployed on `db.m7g.2xlarge` with Provisioned IOPS. Transactional sync latency `I/O:walSync` fell from 150ms to **under 8ms**, allowing smooth execution of concurrent updates.

#### C. Problems Encountered & Root Causes

* **Cache Durability Concerns:** Valkey 7.2 runs without synchronous write persistence by default. The `WAIT` command (which blocks the client until a specified number of replicas acknowledge the write) provides only high-probability replication-based durability rather than true engine-level strong consistency or transactional disk-log persistence. Under massive write spikes or multi-AZ network partition events, session data could be lost before replication completes.

#### D. Recommendations & Sizing Mapping

* Deploy the optimized architecture outlined in the **[5,000 VU Sizing Specs](performance-testing.html#vu--heavy-concurrency-production-model-optimized-scale-up)**.
* For non-loss-tolerant transactional session data, ensure writes are routed directly to RDS or another durable store. If using Valkey for durable session management, note that upgrading to Valkey 9.0 alone does not enable synchronous durability; you must clearly separate the configuration paths depending on your deployment model and remove the `active-durability` parameter reference:
  - **AWS ElastiCache managed clusters:** Configure the `Durability` parameter and require verification that `EffectiveDurability=sync` is active.
  - **Self-hosted Valkey instances:** Start the database engine explicitly with `--durability sync` to guarantee synchronous replication logging to replica nodes before acknowledging client writes.

---

### 🚀 Ujian Prestasi 10,000 VU (Extreme Concurrency)

The 10,000 VU tier represents our highest capacity scenario, simulating extreme concurrent payment transactions, geo-spatial lookups, and reporting aggregation.

#### A. Test Conditions

* **Date & Start Time:** October 6, 2025, 10:46 PM
* **Date & End Time:** October 6, 2025, 11:21 PM
* **Ramp-up Duration:** 15 minutes (from 10:46 PM to 11:01 PM)
* **Steady-State Duration:** 20 minutes (from 11:01 PM to 11:21 PM)

#### B. Component Performance Results

* **Compute Layer (ASG):** **PASS (Maximum Scale)**. ASG scaled smoothly to **100 active nodes** across three Availability Zones (`ap-southeast-5a`, `ap-southeast-5b`, and `ap-southeast-5c`), with average CPU under **45%**.
* **Cache Layer (Valkey):** **PASS (Maximum Scale)**. Deployed as a Multi-AZ Sharded Valkey Cluster on `cache.m7g.large` instances, scaling session read throughput linearly.
* **Database Layer (RDS MariaDB & PostgreSQL):** **PASS (Maximum Scale)**. Deployed on `db.m7g.4xlarge` (16 vCPUs, 64GB RAM) with **io2 Provisioned IOPS (10,000 IOPS and 250 MB/s throughput)**, successfully handling massive transactional loads.

#### C. Problems Encountered & Root Causes

* **Write Master Starvation:** Reporting and query lookups accounted for **80%** of total database traffic. Running heavy read-aggregations on the primary master occasionally starved concurrent transaction write locks.
* **HTTP Connection Pooling Exhaustion:** Standard Nginx `worker_connections` and PHP-FPM worker pools (`pm.max_children`) were exhausted, causing minor Gateway Timeout errors.
* **WAF Inspection Overhead:** The regional ALB-attached WAF ACL introduced a minor latency overhead of **up to 20ms** due to evaluating hundreds of regex patterns for every request.

#### D. Recommendations & Sizing Mapping

* Deploy the extreme high-capacity configurations specified in the **[10,000 VU Sizing Specs](performance-testing.html#vu--extreme-concurrency-production-model-maximum-scale)**.
* **Database Read Replica Offloading:** Offload analytical reads and report generation entirely from the primary database master. Transition to a high-availability database cluster (e.g., Multi-AZ Aurora cluster) with dedicated Read Replicas.
* **Nginx & PHP-FPM Tuning:**
  - Increase `worker_connections` to **20,480** in Nginx configuration.
  - Configure the PHP-FPM process manager to use **static allocation (`pm = static`)** for dedicated production environments (consistent with the production standard in **[CodeIgniter Deployment Guide](codeigniter-php-fpm.html)**), scaling `pm.max_children` to **120+** for this extreme workload; this target value must be precisely sized and validated based on measured vCPU capacity and measured per-process memory consumption (assuming ~45MB per PHP-FPM process) to prevent memory exhaustion under peak load.
  - Tune the keep-alive timeout to **15 seconds** to recycle socket connections rapidly.
* **WAF Web ACL Optimization:** Nest and optimize Web ACL rules, utilize precise regex match patterns, and deploy explicit **scope-down statements** using `FieldToMatch` settings (e.g., limiting expensive body/payload inspection rules specifically to JSON API requests via `UriPath` and `Method` constraints) to prevent inspection overhead on safe static assets while retaining robust baseline protections for all other traffic.

---

## 2. Root Cause Analysis (RCA) - Load Test Bottleneck Summary

The table below summarizes the technical RCA findings for the system components before optimization:

| Impacted Component | Load / Peak AAS | Primary Bottleneck Metric | Root Cause Description | Remediation Implemented |
| :--- | :--- | :--- | :--- | :--- |
| **RDS MariaDB** | 2,500 VU / 8.0 AAS | `wait/io/table/sql/handler` | Full table scans and disk filesort operations on `summary` and `recons_2025` tables due to lack of composite indexes. | Created composite index `idx_summary_agg (status, tenant_id, total)` and `idx_recons_lookup (reference_id, is_reconciled)`. |
| **RDS PostgreSQL** | 2,500 VU / Spiked | `I/O:walSync` | GP3 write IOPS exhaustion under concurrent UPDATE transactions on the `parking` table, stalling processes waiting for WAL flush. | Upgraded storage tier to Provisioned IOPS (io2) with 5,000+ IOPS, and created composite index `idx_parking_lookup`. |
| **ALB WAFv2** | 10,000 VU / High | L7 Inspection Delay | Heavy rule evaluation (OWASP rules + deep packet inspection) on API paths introducing up to 20ms of overhead. | Optimized rule nesting, streamlined regex matches, and implemented WAF scope-down statements using FieldToMatch constraints to restrict payload inspection to target paths while retaining full baseline protection. |
| **Nginx & PHP-FPM** | 10,000 VU / Max | Socket Exhaustion | Standard connection limits and maximum children pools (`pm.max_children`) exceeded by extreme concurrency. | Tuned Nginx `worker_connections` to 20,480, configured static process manager (`pm = static`) with `pm.max_children` scaled to 120+, and shortened keep-alive to 15s. |

---

## 3. Financial and Performance Optimization Alignment

This load-testing audit demonstrates the critical relationship between performance stability and cloud architecture pricing. Deploying a high-availability, high-performance database tier is mandatory to support production traffic spikes, but introduces higher monthly costs.

To maintain maximum financial and operational efficiency under scale:

1. **Purchase Reserved Instances (RIs):** Commit to a 1-year or 3-year contract (Standard or Convertible, No Upfront or Partial Upfront, targeting the ap-southeast-5 region based on August 2026 pricing models) for the primary `db.m7g` database engines to achieve an illustrative estimate of **30% - 35%** savings on database compute compared to on-demand rates.

2. **Commit to Compute Savings Plans:** Secure a 1-year or 3-year Compute Savings Plan (No Upfront, targeting the ap-southeast-5 region based on August 2026 pricing models) for the application tier (`t4g` and `c7g` families) to unlock an illustrative estimate of **25% - 43%** discounts on the dynamic Auto Scaling Group EC2 nodes.

3. **Use Amazon S3 Sizing Optimization:** Set up automated lifecycle policies to move older logs and analytical backups from S3 Standard ($0.023/GB-month) to S3 Glacier Flexible Archive ($0.0036/GB-month), yielding an illustrative estimate of **80% - 84%** savings on long-term storage costs (based on ap-southeast-5 pricing as of August 2026).

4. **Implement VPC S3 Gateway Endpoints:** Associate an Amazon S3 VPC Gateway Endpoint with the VPC route tables used by the private subnets (rather than configuring it directly inside the subnets). This allows the application servers to bypass the NAT Gateway, eliminating NAT Gateway data-processing charges (such as the standard rate of $0.045/GB in the `ap-southeast-5` region as of August 6, 2026) for application/EC2-originated S3 exports or other customer-managed file transfer paths. Note that default automated RDS snapshot backups are managed by AWS on isolated internal backup networks and do not incur NAT Gateway data-processing charges.
