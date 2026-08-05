---
layout: default
title: "Disaster Recovery Playbook & National Sovereignty Compliance"
---

# Disaster Recovery Playbook & National Sovereignty Compliance (Malaysia)

This document establishes the production disaster recovery (DR) protocols, recovery metrics, and data sovereignty compliance frameworks tailored for our **AWS 3-Tier CodeIgniter PHP Application** deployed in the **AWS Asia Pacific (Malaysia) Region (`ap-southeast-5`)**.

---

## 1. Compliance, Governance, and Data Sovereignty (Malaysia)

Deploying enterprise workloads in the Malaysia region (`ap-southeast-5`) introduces specific regulatory requirements under local laws.

### Personal Data Protection Act (PDPA) 2010 & 2025 Amendments
The Malaysian **Personal Data Protection Act (PDPA) 2010** regulates the processing of personal data in commercial transactions.
- **Data Residency and Sovereignty:** Under Principle 3 (Disclosure Principle) and Section 129 of the PDPA, personal data of Malaysian citizens must not be transferred outside Malaysia unless the destination country has been officially whitelisted or explicit consent is obtained.
- **Why ap-southeast-5 Matters:** By utilizing AWS Malaysia, all user sessions (stored in Valkey), uploads (stored in S3), and customer transaction databases (RDS) reside physically within Malaysian borders (Cyberjaya and Kuala Lumpur edge zones). This guarantees absolute compliance with local residency mandates without complex legal waivers.
- **2025 Amendments Impact:** The PDPA amendments mandate the designation of a **Data Protection Officer (DPO)** and introduce mandatory **Data Breach Notification (DBN)** requirements. Security-focused infrastructure (AWS WAFv2, SSM logging, encrypted databases) is critical to prove "due diligence" during compliance reviews.

---

## 2. Disaster Recovery Strategy Modeling

This playbook models disaster recovery scenarios into three distinct recovery metrics:
1. **RTO (Recovery Time Objective):** The maximum tolerable duration of downtime before the application is restored.
2. **RPO (Recovery Point Objective):** The maximum tolerable volume of data loss, measured in time.
3. **MTPD (Maximum Tolerable Period of Disruption):** The absolute maximum time the business can survive without application access.

We present four standard AWS-aligned DR options mapped directly to our PHP 3-tier layout:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AWS Disaster Recovery Options                   │
│                                                                        │
│  [ Active-Passive / Backup-Restore ] ─────────────────► RTO: Hours      │
│  - Snapshots, Daily Backups, Cold DB Instance          RPO: 24 Hours   │
│                                                                        │
│  [ Pilot Light (Off-site Standby Core) ] ─────────────► RTO: 30 Mins    │
│  - Active RDS Replica, Standby ASG Sized at 0          RPO: Minutes    │
│                                                                        │
│  [ Warm Standby (Scaled-down Active-Active) ] ────────► RTO: 5 Mins     │
│  - Minimal Active ASG, Live Synchronous Replica        RPO: Seconds    │
│                                                                        │
│  [ Multi-Region Active-Active ] ──────────────────────► RTO: Near-Zero │
│  - Dynamic DNS Failover, Global RDS DB, Multi-ALB      RPO: Near-Zero  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Playbook Execution: Pilot Light & Warm Standby

For standard enterprise CodeIgniter applications, **Pilot Light** or **Warm Standby** balances cost and recovery metrics.

### Strategy A: Pilot Light Setup (RDS Multi-AZ + Standby ASG)
- **Database Status:** RDS PostgreSQL/MySQL is deployed as Multi-AZ. AWS continuously performs synchronous block-level replication to the standby zone.
- **Compute Status:** The Auto Scaling Group in the secondary AZ is set to `desired_capacity = 0`.
- **Failover Trigger (RTO ~ 15-30 Minutes, RPO ~ Seconds):**
  1. The primary AZ experiences a structural facility failure.
  2. Managed RDS automatically promotes the standby replica to master and updates internal DNS records (takes under 60 seconds).
  3. CloudWatch triggers an alarm on ALB health check failure, invoking a Lambda function or auto-scaling modification to scale the standby ASG from `0` to `2`.
  4. Newly booted EC2 instances pull CodeIgniter assets from S3 during bootstrap, establish DB connections, and resume traffic.

### Strategy B: Warm Standby Setup (Active-Active Multi-AZ)
- **Database Status:** Active Multi-AZ RDS.
- **Compute Status:** ASG actively maintains instances across both AZs (e.g., `desired_capacity = 2`, spanning `ap-southeast-5a` and `ap-southeast-5b`).
- **Failover Trigger (RTO ~ Under 5 Minutes, RPO ~ Seconds):**
  1. Primary AZ goes offline.
  2. The Application Load Balancer (ALB) detects degraded health checks on instances in the failing AZ and immediately stops routing traffic to them.
  3. 100% of user traffic is instantly served by the remaining healthy instances in the secondary AZ.
  4. The ASG automatically triggers a scale-out policy to spawn replacement instances in the healthy AZ to restore full capacity.

---

## 4. Disaster Recovery Costs & Resource Estimations

This section breaks down the operating cost profile of maintaining DR-ready environments, focusing on regional structures in Malaysia.

### Monthly Backup & Replication Cost Estimations

| DR Strategy | Required Extra Resources | Estimated Monthly Cost (USD) | Estimated Monthly Cost (MYR) | Expected RTO / RPO |
| :--- | :--- | :--- | :--- | :--- |
| **Option 1: Backup & Restore** | Daily AWS Backup snapshots (100 GB S3 + EBS backups) | $8.00 | RM 36.00 | RTO: 2 - 4 Hours<br>RPO: 24 Hours |
| **Option 2: Pilot Light** | Multi-AZ RDS Database Instance + 1 Cold Standalone Instance | $35.00 | RM 157.50 | RTO: 15 - 30 Mins<br>RPO: Seconds |
| **Option 3: Warm Standby** | Full Multi-AZ active ASG instances + active ALB + active ElastiCache Valkey | $110.00 | RM 495.00 | RTO: < 5 Minutes<br>RPO: Seconds |
