---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "Disaster Recovery Options & Regional Strategy Evaluation"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier", "disaster-recovery", "compliance"]
---

**[STRATEGIC FINANCIAL]**

# Disaster Recovery Options & Regional Strategy Evaluation

This document outlines a strategic evaluation of the disaster recovery (DR) architectures and deployment models for our secure **AWS 3-Tier CodeIgniter PHP Application** (serving via Nginx/PHP-FPM, utilising ElastiCache for Valkey session scaling, and a Multi-AZ MariaDB RDS database).

Following early team discussions, this evaluation incorporates the architectural principles defined in the AWS whitepaper on **Disaster Recovery of Workloads on AWS**, adapting them specifically to our project parameters, data sovereignty constraints under the Malaysian Personal Data Protection Act (PDPA) 2010 (and the 2024 amendments), and organisational structures.

---

## 1. Core Disaster Recovery Concepts & AWS Whitepaper Alignment

According to AWS best practices, cloud-based disaster recovery revolves around managing risks to ensure business continuity, evaluated via three key metrics:
- **Recovery Time Objective (RTO):** The maximum acceptable delay between the service interruption and its restoration.
- **Recovery Point Objective (RPO):** The maximum acceptable period of data loss, measured in time, representing the age of data that must be recovered.
- **Maximum Tolerable Period of Disruption (MTPD):** The absolute maximum time the business can survive without the application before incurring catastrophic damage.

### Data Plane vs Control Plane Resilience

When planning for high resiliency, it is critical to distinguish between **data plane** and **control plane** operations:
- **The Data Plane** is responsible for delivering real-time services (e.g., routing traffic, serving database reads/writes). Data planes have extremely high availability design goals (often 99.999% or higher).
- **The Control Plane** is used to configure or modify resources (e.g., launching new instances, modifying DNS records, scaling out Auto Scaling Groups, creating or promoting databases).

**Resiliency Rule:** For maximum reliability, failover processes must rely primarily on **data plane operations** rather than control plane actions. For example, using Route 53 health checks and active-passive routing is a data plane activity. Instead of an absolute, instant failover, traffic redirection observes a tested end-to-end convergence range of **90 to 180 seconds**. This is determined by the Route 53 health-check interval (30 seconds), the configured failure threshold (3 consecutive failures, totaling 90 seconds of detection delay), a DNS record TTL of 60 seconds, and downstream resolver/client caching behaviors. Conversely, depending on the Auto Scaling control plane to spin up instances from scratch during an outage introduces external dependencies and control plane latency, which increases RTO.

### The Four Classic Cloud DR Strategies

AWS categorises DR strategies into four main patterns, ranging from low cost and complexity to higher cost and near-zero recovery times:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        AWS Disaster Recovery Options                   │
│                                                                        │
│  [ Backup and Restore ] ──────────────────────────────► RTO: Hours     │
│  - Snapshots, Daily Backups, Re-build via IaC          RPO: Minutes    │
│                                                                        │
│  [ Pilot Light (Off-site Standby Core) ] ─────────────► RTO: 15-30 Mins│
│  - Cross-Region Replica, Standby Compute at Size 0     RPO: Minutes    │
│                                                                        │
│  [ Warm Standby (Scaled-down Active-Active) ] ────────► RTO: < 5 Mins  │
│  - Active Minimal ASG, In-Region Multi-AZ Standby      RPO: Seconds    │
│                                                                        │
│  [ Multi-Site Active/Active ] ────────────────────────► RTO: Near-Zero │
│  - Multi-region routing, Application-Level dual writes RPO: Non-Zero   │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Backup and Restore:** Point-in-time recovery (PITR) and daily backups of EBS volumes, RDS, and S3 data. Highly cost-effective but has the longest RTO as the entire application compute must be redeployed from scratch using Infrastructure as Code (OpenTofu) and Golden AMIs.
2. **Pilot Light:** Continuous replication of databases (via RDS asynchronous cross-Region read-replicas or cross-account replication tunnels) and storage (via S3 Cross-Region Replication), with a provisioned but "switched off" or scaled-to-zero compute tier. Under failover, the compute tier is rapidly provisioned and scaled out.
3. **Warm Standby:** A scaled-down but fully functional copy of the infrastructure running continuously. It can immediately handle a small amount of traffic and uses Auto Scaling to scale up to full capacity, minimising RTO with low overhead. It utilises an in-Region Multi-AZ DB instance standby for synchronous durability.
4. **Multi-Site Active/Active:** Code is deployed and actively serving traffic across multiple regions or accounts simultaneously. Users are dynamically routed to the nearest healthy endpoint. Near-zero RTO, but highly complex and costly. For databases, it utilises application-level write-routing or read-replica architectures.

---

## 2. Project-Specific DR Options Under Discussion

The technical committee has evaluated **3+1 disaster recovery options** for our AWS infrastructure, considering the ap-southeast-5 (Malaysia) region, account-level separation, and compliance with the Malaysian PDPA Section 129 transfer bases.

### Option 1: Region besides Malaysia and a Separate AWS Account

Under this option, the DR site is deployed in a completely different AWS geographic Region (recommended: **Singapore `ap-southeast-1`** as the closest low-latency region) and hosted under an entirely separate AWS account.

- **DR Strategy:** Active/Standby (Warm Standby) or Pilot Light.
- **Architectural Implementation:**
  - **Database:** Deploy a supported cross-account MariaDB replication design. Rather than native cross-Region read replicas (which are restricted across accounts), replication uses **GTID-based binlog replication** (using RDS external master APIs like `mysql.rds_set_external_master_gtid`) or **AWS Database Migration Service (DMS) with Change Data Capture (CDC)** over a secure VPC Peering link.
    - *Connectivity & Privileges:* Dedicated replication user with restricted `REPLICATION CLIENT` and `REPLICATION SLAVE` privileges.
    - *Binlog Retention:* Configured via `mysql.rds_set_configuration('binlog retention hours', 24)` on the primary instance to prevent replication failures during network lag.
    - *KMS/IAM Policies:* Customer-managed KMS keys are shared across accounts/Regions with specific IAM roles granting decrypt/encrypt permissions for the data transfer.
    - *Lag Monitoring:* Active replication lag is monitored via CloudWatch metric `OldestReplicationSlotLag` or DB heartbeat tables, establishing an acceptance criterion of replication lag under **2 seconds**.
    - *Promotion & Failback:* Manual database promotion is scripted using `mysql.rds_reset_external_master`. Failback is accomplished by reversing the replication direction once primary region stability is verified.
  - **Caching:** Configure ElastiCache Valkey with global replication to synchronise cached metadata and session data.
  - **Compute:** Define duplicate Auto Scaling Groups (ASGs) in Singapore, configured to either size 0 (Pilot Light) or scaled down to 1 active instance (Warm Standby).
  - **Traffic Routing:** Leverage **AWS Global Accelerator** with custom traffic dials or **Route 53 Application Recovery Controller (ARC)** to orchestrate seamless cross-region routing using data-plane routing controls.
  - **Compliance & PDPA Section 129:** Under Section 129 of the Malaysian PDPA, personal data transfer outside Malaysia is restricted unless a valid exception is satisfied:
    - *Section 129(2) Destination-Law Adequacy:* Transferring to jurisdictions with laws matching or exceeding the PDPA's protections. A formal **Transfer Impact Assessment (TIA)** is conducted to assess destination-law adequacy, analyzing local administrative, legal, and operational safeguards (with the Cross-Border Personal Data Transfer (CBPDT) Guidelines serving as conditions and technical safeguards rather than an automatic guarantee).
    - *Section 129(3)(a) Consent:* Express consent obtained from the data subject.
    - *Section 129(3)(b) Contractual Necessity:* Essential for performing a contract between the data subject and data user.
    - *Applicable Controls:* The transfer incorporates conditional wording, explicit data subject notice, robust end-to-end transport encryption, a detailed transfer-record log, and strict data processor contracts incorporating Standard Contractual Clauses (SCCs).
- **Multi-Site Active/Active Considerations:** If configured as a true Multi-Site Active/Active deployment, the database tier follows a **single-writer routing model** where all SQL write operations are forwarded to the primary MariaDB instance in `ap-southeast-5`, while reads are served locally from `ap-southeast-1` (read local, write global). Strict **write fencing** is enforced at the application layer to prevent split-brain write scenarios during network partitions. **Conflict resolution** relies on application-level last-write-wins (LWW) or transaction fencing, and session consistency is maintained by configuring Valkey with short-lived local sessions that fallback gracefully to database records during cross-region replication lag.
- **Pros:**
  - Represents the gold standard for **full regional disaster recovery**, protecting against total physical, geographic, or power failure of the primary Malaysia region.
  - Separate AWS account boundaries mitigate risks from insider threats, accidental administrative deletion, or primary account compromise.
- **Cons:**
  - Highest operational complexity and overhead.
  - Slightly higher cost due to cross-region data transfer fees and active replication of RDS/Valkey instances.

### Option 2: Malaysia Region and a Separate AWS Account

If cross-region data transfers are prohibited by strict national sovereignty mandates or compliance barriers, the DR site can be built inside the **same Malaysia Region (`ap-southeast-5`)** but segregated inside a **separate AWS account**.

- **DR Strategy:** Active/Standby (Warm Standby) or Pilot Light.
- **Architectural Implementation:**
  - **Database & Data Tier Replication:** Rather than relying on VPC peering or Transit Gateway as data-replication channels, data sync uses secure, service-level mechanisms. Database snapshots are shared or copied across accounts (using **RDS cross-account snapshot sharing** and copying to the destination account's local Backup vault). EFS files are replicated using **AWS Backup cross-account copy** or native **EFS Replication**, utilising customer-managed KMS keys with cross-account key policies and appropriate IAM permissions.
  - **Storage:** Configure **S3 Cross-Account Bucket Replication (CRR)** using customer-managed KMS keys and cross-account IAM roles to continuously copy user uploads across the account boundary.
  - **Compute & Network Isolation:** Maintain a mirroring 3-tier VPC structure in the standby account. We retain local VPC Peering or Transit Gateway exclusively to route standby application-level test and administration traffic, not as a core database or file replication mechanism.
- **Pros (Scoped Local Residency & Account Isolation):**
  - Rather than absolute guarantees, this setup provides high-durability compliance with the following scoped, testable conditions:
    - *In-Scope Data Protection:* Application transaction database records, S3 object backups, Nginx system logs, IAM metadata, KMS encryption keys, and administrative support records are strictly pinned to the `ap-southeast-5` region using region-locked IAM boundaries (`aws:RequestedRegion` condition keys).
    - *Enforcement Policies:* Verified via independent backup vaults, isolated log storage with S3 Object Lock, and isolated customer-managed KMS keys.
  - Isolates the production environment from complete account compromise, API key theft, or ransomware incidents affecting the primary account.
- **Cons:**
  - **Does not isolate against region-wide AWS outages** in the ap-southeast-5 region. If the entire region undergoes a structural disruption, both accounts will be impacted.
  - *Shared Administration Risks:* If identical administrative credentials (or federated SSO roles with equal access) are shared across both accounts, or if loose cross-account IAM trust relationships are defined, the account isolation boundary is bypassed.
  - Replicating data across account boundaries within the same region requires careful IAM role configurations, KMS key sharing, and VPC peering or Transit Gateway connections.

### Option 3: Malaysia Region and the Same AWS Account (Different VPC)

This option maintains the primary and DR environments within the **same Malaysia Region (`ap-southeast-5`)** and within the **same AWS account**, separating them logically using a different VPC (Virtual Private Cloud).

- **DR Strategy:** Standby (Warm Standby) or Backup and Restore.
- **Architectural Implementation:**
  - **Database:** Deploy RDS for MariaDB as a Multi-AZ DB instance (with synchronous replication across Availability Zones `ap-southeast-5a` and `ap-southeast-5b`).
  - **Compute:** Build separate VPCs (e.g., `VPC-Primary` and `VPC-DR`) with separate IP CIDR blocks. Spin up a standby cluster in the DR VPC.
  - **Replication:** Connect the two VPCs via local VPC Peering to route application-level data, while data backups are copied via AWS Backup across the VPC scope on demand.
- **Pros:**
  - Extremely cost-optimised and simple to manage.
  - Fully isolates the application from local network misconfigurations, subnet depletion, or VPC-level security group corruption.
- **Cons:**
  - No protection against region-wide outages.
  - No protection against account-level disasters (e.g., admin credential compromise, automated cleanup script error, or service quota exhaustion at the account level).
  - Subject to shared control plane limits of the single account.

### Option 4: Backup and Restore

A baseline recovery strategy involving periodic data archiving without active compute replication.

- **DR Strategy:** Classic Backup and Restore.
- **Architectural Implementation:**
  - **Database:** RDS for MariaDB automated backups are configured with a retention period of 30 days. Continuous write-ahead transaction log backups (binary logs) are archived to RDS-managed storage, allowing Point-in-Time Recovery (PITR) to any millisecond up to the latest restorable time (typically within **5 minutes** of the current time).
  - **Assets:** User-uploaded files stored on S3 are protected with Object Versioning and S3 Object Lock (for ransomware mitigation). EFS file systems are backed up daily using **AWS Backup** with a retention policy of 30 days.
  - **Recreation & Testing:** In the event of a disaster, OpenTofu templates are executed to rebuild the entire networking, security groups, ALB, Valkey, and compute layers. Golden AMIs are pulled from the AMI catalog; recoverable AMI copies are maintained continuously in the recovery account and Region with required cross-account KMS decryption permissions for the underlying EBS snapshots. Meanwhile, versioned OpenTofu source code and remote state files (stored in a separate, version-controlled S3 bucket with Object Lock enabled) remain independently accessible outside the failed failure boundary. All scheduled disaster-recovery testing must use these isolated, recovery-region artifacts to validate true out-of-boundary recovery.
- **Pros:**
  - Lowest ongoing cost index, as only backup storage and snapshots are paid for.
  - Minimal architectural complexity during standard day-to-day operations.
- **Cons:**
  - **Recovery Time Objective (RTO) vs. Point-in-Time Recovery (PITR):** Although PITR reduces the target RPO to less than 5 minutes (using RDS-managed automated backups and continuous transaction log archiving), the RTO remains high (2 to 4 hours) because the on-demand database restore must provision a completely new DB instance before applying transaction logs.
  - Relies heavily on the availability of control plane operations during a crisis.

---

## 3. Disaster Recovery Strategic Decision Matrix

The following matrix compares the evaluated DR options using **workload-specific tested targets** and specific simulated recovery parameters:

| DR Option Evaluated | Account Boundary | Regional Boundary | Network Isolation | Tested Target RTO | Tested Target RPO | Relative Cost Index | PDPA Compliance Basis |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Option 1: Cross-Region & Separate Account** | Isolated (Different Account) | Isolated (`ap-southeast-1`) | High (Distinct VPCs) | < 15 Minutes | < 5 Seconds | ★★★★☆ (High) | Section 129 Transfer basis with formal TIA & SCCs |
| **Option 2: In-Region & Separate Account** | Isolated (Different Account) | Shared (`ap-southeast-5`) | High (Distinct VPCs) | < 30 Minutes | < 1 Minute | ★★★☆☆ (Medium) | 100% In-Region local residency (Scoped conditions) |
| **Option 3: In-Region & Same Account** | Shared (Same Account) | Shared (`ap-southeast-5`) | Medium (VPC Peering) | < 60 Minutes | < 5 Minutes | ★★☆☆☆ (Low) | 100% In-Region local residency (Scoped conditions) |
| **Option 4: Backup & Restore (On-Demand)** | Shared or Isolated | Shared or Isolated | Low (Rebuilt on need) | 2 - 4 Hours | < 5 Minutes (PITR) | ★☆☆☆☆ (Minimal) | Depends on backup storage vault residency |

### 📋 Workload-Specific Acceptance Criteria
Any production-level declaration of these targets requires satisfying the following verified test thresholds:
1. **Database Restore Time:** Automated RDS-managed MariaDB restoration and binlog forward application must complete within **90 minutes** during simulated failover runs.
2. **Replication Lag:** Asynchronous cross-region replication lag must remain under **2 seconds** during peak-load testing (simulating 2,500 active virtual users).
3. **Application Cutover:** Network traffic redirection via Route 53 data-plane failover controls must complete in **90 to 180 seconds** under active client load.

---

## 4. Key Recommendations and Implementation Blueprint

To achieve the optimal balance of business continuity, fiscal responsibility, and regulatory compliance, the project prioritises a **phased implementation roadmap**:

1. **Phase 1 (Immediate - Active/Passive Backup & Restore):** Implement full Option 4 using OpenTofu IaC to ensure that the entire 3-tier PHP-FPM environment can be spun up deterministically within 2 hours. Enforce strict cross-account backup copies using AWS Backup Vaults.
2. **Phase 2 (Medium Term - In-Region Account Isolation):** Transition to Option 2 by provisioning a secondary staging/DR account within the Malaysia region. A project-specific risk assessment indicates that administrative credential leaks, misconfigured automated cleanup policies, and control-plane lockouts represent the highest probability risks to our system's availability. Separating accounts isolates the production environment, ensuring that a compromise of the primary account does not propagate to the backup infrastructure.
3. **Phase 3 (Enterprise Target - Cross-Region Pilot Light):** Deploy Option 1 with an active RDS Read Replica in Singapore and a scaled-to-zero compute ASG tier. Since a scaled-to-zero ASG represents a Pilot Light strategy, it requires compute scale-out and traffic redirection during failover, meaning recovery is not instantaneous. We reserve near-zero-downtime SLA claims exclusively for tested, continuously running Warm Standby or Multi-Site Active/Active designs where compute capacity is already online.
