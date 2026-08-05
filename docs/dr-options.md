---
layout: default
title: "Disaster Recovery Playbook & National Sovereignty Compliance"
---

# Disaster Recovery Playbook & National Sovereignty Compliance (Malaysia)


This document establishes the production disaster recovery (DR) protocols, recovery metrics, and data sovereignty compliance frameworks tailored for our **AWS 3-Tier CodeIgniter PHP Application** deployed in the **AWS Asia Pacific (Malaysia) Region (`ap-southeast-5`)**.

---


## 1. Compliance, Governance, and Data Sovereignty (Malaysia)


Deploying enterprise workloads in the Malaysia region introduces specific regulatory requirements under local laws that must be designed into the infrastructure rather than assumed.

### Personal Data Protection Act (PDPA) 2010 & Personal Data Protection (Amendment) Act 2024 (Act A1727)

The Malaysian **Personal Data Protection Act (PDPA) 2010** regulates the processing of personal data in commercial transactions. In July 2024, the Malaysian Parliament passed the **Personal Data Protection (Amendment) Act 2024 (Act A1727)**, initiating a staged commencement timeline. This amendment significantly modernizes compliance standards:

- **Data Protection Officer (DPO) Mandate:** Under the staged 2024/2025 guidelines, the designation of a formal DPO is scoped to organizations whose processing exceeds 20,000 data subjects, or processes sensitive personal data or financial data exceeding 10,000 data subjects, or involves regular and systematic monitoring of data subjects' behavior.
- **Mandatory Data Breach Notification (DBN):** Data subject and regulatory breach notifications are strictly required when a security incident causes, or is likely to cause, significant harm to data subjects. This requires real-time centralized logging and auditable system trails.
- **Section 129 Transfer Bases & Compliance:** Section 129 of the PDPA regulates the transfer of personal data outside Malaysia. While whitelisting of countries by the Minister remains a core mechanism, transfers are fully permitted under alternative bases including:
  1. **Substantially Similar Law:** Transferring to jurisdictions with laws matching PDPA's protections.
  2. **Adeuate Protection:** Enforcing contractual clauses, binding corporate rules, or organizational data transfers ensuring adequate protection.
  3. **Performance of Contract:** Necessary for the performance of a contract between the data subject and data user.
  4. **Exceptions & Consent:** Reasonable steps taken to protect the data, vital interests of the data subject, or explicit consent from the data subject.
  - **Required Notice & TIA:** Standard compliance requires data users to conduct a formal **Transfer-Impact Assessment (TIA)** and provide clear notice to data subjects outlining the purpose, destination, and security measures of cross-border transfers.

### Data Residency Scope for ap-southeast-5 (Malaysia)

Selecting the **AWS Asia Pacific (Malaysia) Region (`ap-southeast-5`)** supports data residency compliance, but it is **not an absolute compliance guarantee**. Real-world data residency depends on the proper end-to-end configuration of all services, backups, logs, and replication settings:
- **Local Service Mapping:** Application nodes, Amazon RDS databases, and ElastiCache Valkey instances must be pinned strictly to `ap-southeast-5` subnets.
- **Backup Configuration:** AWS Backup vaults and RDS backup settings must restrict copy targets to the local region. Cross-Region backups must be explicitly disabled or routed only to regions with equivalent legal bases and validated TIAs.
- **Logging & Auxiliary Systems:** CloudWatch Logs, Nginx logs, and PHP application log targets must not route data to external regional log collectors or international SaaS APM tools without anonymizing personally identifiable information (PII).

---


## 2. Disaster Recovery Strategy Modeling


This playbook models disaster recovery scenarios into three distinct recovery metrics:
1. **RTO (Recovery Time Objective):** The maximum tolerable duration of downtime before the application is restored.
2. **RPO (Recovery Point Objective):** The maximum tolerable volume of data loss, measured in time.
3. **MTPD (Maximum Tolerable Period of Disruption):** The absolute maximum time the business can survive without application access.

We present four standard AWS-aligned DR options mapped directly to our PHP 3-tier layout:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        AWS Disaster Recovery Options                   │
│                                                                        │
│  [ Active-Passive / Backup-Restore ] ─────────────────► RTO: Hours      │
│  - Snapshots, Daily Backups, Cold DB Instance          RPO: 24 Hours   │
│                                                                        │
│  [ Pilot Light (AZ or Cross-Region Standby) ] ────────► RTO: 15-30 Mins │
│  - Active RDS Replica, Standby ASG Sized at 0          RPO: Minutes    │
│                                                                        │
│  [ Warm Standby (Scaled-down Active-Active) ] ────────► RTO: 5 Mins     │
│  - Minimal Active ASG, Live Synchronous Replica        RPO: Seconds    │
│                                                                        │
│  [ Multi-Region Active-Active ] ──────────────────────► RTO: Near-Zero │
│  - Route 53 DNS Routing, Aurora Global DB              RPO: Non-Zero   │
└────────────────────────────────────────────────────────────────────────┘
```

---


## 3. Playbook Execution: Pilot Light & Warm Standby


For standard enterprise CodeIgniter applications, **Pilot Light** or **Warm Standby** balances cost and recovery metrics.

### Strategy A: Pilot Light Setup (RDS Multi-AZ and Standby ASG)

To qualify as a valid **Availability Zone Pilot Light**, the infrastructure is designed as follows:
- **Database Status:** RDS PostgreSQL/MySQL is deployed as Multi-AZ with synchronous block-level replication to the standby zone.
- **Compute Status:** The Auto Scaling Group in the secondary AZ is set to `desired_capacity = 0` to minimize running costs.
- **Failover Trigger (RTO ~ 15-30 Minutes, RPO ~ Seconds):**
  1. The primary AZ experiences a structural facility failure.
  2. Managed RDS automatically promotes the standby replica to master. This failover target is typically **60 to 120 seconds**, which includes application reconnect times, client connection pool timeouts, and internal DNS propagation behavior (Route 53 resolver caches).
  3. CloudWatch triggers an alarm on ALB health check failure, scaling the standby ASG from `0` to `2`.
  4. Newly booted EC2 instances pull CodeIgniter assets from S3 during bootstrap, establish DB connections, and resume traffic.

To scale this to a **Cross-Region Pilot Light (Off-site Standby Core)**:
- **Database:** Deploy an RDS Cross-Region Read Replica in a secondary region (e.g. `ap-southeast-1` Singapore) with asynchronous replication.
- **Storage:** Enable S3 Cross-Region Replication (CRR) to sync user uploads.
- **Compute:** Define duplicate ASG launch templates in the secondary region with `desired_capacity = 0`.
- **DNS:** Configure Route 53 active-passive DNS failover routing.

### Strategy B: Warm Standby Setup (Active-Active Multi-AZ)

- **Database Status:** Active Multi-AZ RDS.
- **Compute Status:** ASG actively maintains instances across both AZs (e.g., `desired_capacity = 2`, spanning `ap-southeast-5a` and `ap-southeast-5b`).
- **Failover Trigger (RTO ~ Under 5 Minutes, RPO ~ Seconds):**
  1. Primary AZ goes offline.
  2. The Application Load Balancer (ALB) detects degraded health checks on instances in the failing AZ and immediately stops routing traffic to them.
  3. 100% of user traffic is instantly served by the remaining healthy instances in the secondary AZ.
  4. The ASG automatically triggers a scale-out policy to spawn replacement instances in the healthy AZ to restore full capacity.

### Strategy C: Multi-Region Active-Active with Aurora Global Database

For mission-critical applications requiring near-zero regional failover times:
- **Database Status:** AWS Aurora Global Database is deployed with a single-writer primary region (`ap-southeast-5`) and a read-only secondary Region (`ap-southeast-1`). Data is replicated asynchronously with a **non-zero replication lag expectation** (typically under 1 second under normal load).
- **DNS Status:** Route 53 Latency-based or Failover-based DNS routing maps users dynamically to the nearest healthy regional ALB.
- **Failover Protocol:** If `ap-southeast-5` goes offline, the Aurora read-only secondary database is promoted to a full write-capable master, while Route 53 routes 100% of traffic to the standby region.

---


## 4. Disaster Recovery Costs & Resource Estimations


This section breaks down the operating cost profile of maintaining DR-ready environments, focusing on regional structures in Malaysia.

### Monthly Backup & Replication Cost Estimations

| DR Strategy | Required Extra Resources | Estimated Monthly Cost (USD) | Estimated Monthly Cost (MYR) | Expected RTO / RPO |
| :--- | :--- | :--- | :--- | :--- |
| **Option 1: Backup & Restore** | Daily AWS Backup snapshots (100 GB S3 + EBS backups) | $8.00 | RM 36.00 | RTO: 2 - 4 Hours<br>RPO: 24 Hours |
| **Option 2: AZ Pilot Light** | Multi-AZ RDS Database Instance + 1 Cold Standalone Instance | $35.00 | RM 157.50 | RTO: 15 - 30 Mins<br>RPO: Seconds |
| **Option 3: Warm Standby** | Full Multi-AZ active ASG instances + active ALB + active ElastiCache Valkey | $110.00 | RM 495.00 | RTO: < 5 Minutes<br>RPO: Seconds |
