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

**Resiliency Rule:** For maximum reliability, failover processes must rely primarily on **data plane operations** rather than control plane actions. For example, using Route 53 health checks and active-passive routing is a data plane activity that fails over traffic instantly. Conversely, depending on the Auto Scaling control plane to spin up instances from scratch during an outage introduces external dependencies and control plane latency, which increases RTO.

### The Four Classic Cloud DR Strategies

AWS categorises DR strategies into four main patterns, ranging from low cost and complexity to higher cost and near-zero recovery times:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        AWS Disaster Recovery Options                   │
│                                                                        │
│  [ Backup and Restore ] ──────────────────────────────► RTO: Hours     │
│  - Snapshots, Daily Backups, Re-build via IaC          RPO: 24 Hours   │
│                                                                        │
│  [ Pilot Light (Off-site Standby Core) ] ─────────────► RTO: 15-30 Mins│
│  - Active RDS Replica, Standby Compute at Size 0       RPO: Minutes    │
│                                                                        │
│  [ Warm Standby (Scaled-down Active-Active) ] ────────► RTO: < 5 Mins  │
│  - Active Minimal ASG, Live Synchronous Replica        RPO: Seconds    │
│                                                                        │
│  [ Multi-Site Active/Active ] ────────────────────────► RTO: Near-Zero │
│  - Multi-region routing, Global Database Sync          RPO: Non-Zero   │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Backup and Restore:** Point-in-time snapshots of EBS volumes, RDS, and S3 data. Highly cost-effective but has the longest RTO as the entire application compute must be redeployed from scratch using Infrastructure as Code (OpenTofu) and Golden AMIs.
2. **Pilot Light:** Continuous replication of databases (via RDS replicas or Global Databases) and storage (via S3 Cross-Region Replication), with a provisioned but "switched off" or scaled-to-zero compute tier. Under failover, the compute tier is rapidly provisioned and scaled out.
3. **Warm Standby:** A scaled-down but fully functional copy of the infrastructure running continuously. It can immediately handle a small amount of traffic and uses Auto Scaling to scale up to full capacity, minimising RTO with low overhead.
4. **Multi-Site Active/Active:** Code is deployed and actively serving traffic across multiple regions or accounts simultaneously. Users are dynamically routed to the nearest healthy endpoint. Near-zero RTO, but highly complex and costly.

---

## 2. Project-Specific DR Options Under Discussion

The technical committee has evaluated **3+1 disaster recovery options** for our AWS infrastructure, considering the ap-southeast-5 (Malaysia) region, account-level separation, and compliance with the Malaysian PDPA Section 129 transfer bases.

### Option 1: Region besides Malaysia and a Separate AWS Account

Under this option, the DR site is deployed in a completely different AWS geographic Region (recommended: **Singapore `ap-southeast-1`** as the closest low-latency region) and hosted under an entirely separate AWS account.

- **DR Strategy:** Multi-Site Active/Active, Active/Standby (Warm Standby), or Pilot Light.
- **Architectural Implementation:**
  - **Database:** Deploy an asynchronous RDS Cross-Region Read Replica from Malaysia (`ap-southeast-5`) to Singapore (`ap-southeast-1`).
  - **Caching:** Configure ElastiCache Valkey with global replication to synchronise cached metadata and session data.
  - **Compute:** Define duplicate Auto Scaling Groups (ASGs) in Singapore, configured to either size 0 (Pilot Light) or scaled down to 1 active instance (Warm Standby).
  - **Traffic Routing:** Leverage **AWS Global Accelerator** with custom traffic dials or **Route 53 Application Recovery Controller (ARC)** to orchestrate seamless cross-region routing using data-plane routing controls.
  - **Compliance & PDPA Section 129:** Under PDPA Section 129, transferring personal data outside Malaysia is fully permitted provided we satisfy one of the legal transfer bases (e.g. Contractual Necessity, Data Subject Consent, or by conducting a **Transfer Impact Assessment (TIA)** to ensure the destination region offers adequate protections).
- **Pros:**
  - Represents the gold standard for **full regional disaster recovery**, protecting against total physical, geographic, or power failure of the primary Malaysia region.
  - Separate AWS account boundaries mitigate risks from insider threats, accidental administrative deletion, or primary account compromise.
- **Cons:**
  - Highest operational complexity and overhead.
  - Slightly higher cost due to cross-region data transfer fees and active replication of RDS/Valkey instances.

### Option 2: Malaysia Region and a Separate AWS Account

If cross-region data transfers are prohibited by strict national sovereignty mandates or compliance barriers, the DR site can be built inside the **same Malaysia Region (`ap-southeast-5`)** but segregated inside a **separate AWS account**.

- **DR Strategy:** Active/Active, Warm Standby, or Pilot Light.
- **Architectural Implementation:**
  - **Database:** Deploy a cross-account RDS read replica (if supported) or automate periodic cross-account database snapshot sharing to copy backups securely.
  - **Storage:** Configure S3 Cross-Account Bucket Replication to securely copy user uploads across the account boundary.
  - **Compute & Networking:** Maintain a mirroring 3-tier VPC structure in the standby account with compute nodes (ASGs) kept in a scaled-down standby state.
- **Pros:**
  - Guarantees 100% **local data residency** inside the sovereign borders of Malaysia, satisfying local regulatory guidelines.
  - Isolates the production environment from complete account compromise, API key theft, or ransomware incidents affecting the primary account.
- **Cons:**
  - **Does not isolate against region-wide AWS outages** in the ap-southeast-5 region. If the entire region undergoes a structural disruption, both accounts will be impacted.
  - Replicating data across account boundaries within the same region requires careful IAM role configurations, KMS key sharing, and VPC peering or Transit Gateway connections.

### Option 3: Malaysia Region and the Same AWS Account (Different VPC)

This option maintains the primary and DR environments within the **same Malaysia Region (`ap-southeast-5`)** and within the **same AWS account**, separating them logically using a different VPC (Virtual Private Cloud).

- **DR Strategy:** Standby (Warm Standby) or Backup and Restore.
- **Architectural Implementation:**
  - **Database:** Deploy RDS as a Multi-AZ cluster (across Availability Zones `ap-southeast-5a` and `ap-southeast-5b`).
  - **Compute:** Build separate VPCs (e.g., `VPC-Primary` and `VPC-DR`) with separate IP CIDR blocks. Spin up a scaled-down standby cluster in the DR VPC.
  - **Replication:** Connect the two VPCs via local VPC Peering to replicate data-tier snapshots, or utilise AWS Backup to duplicate S3 and EFS contents across the VPC scope on demand.
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
  - **Database:** Daily automated RDS MariaDB snapshots stored in highly durable S3 buckets, with continuous write-ahead transaction log backups (Point-in-Time Recovery).
  - **Assets:** User-uploaded files stored on S3 are protected with Object Versioning and S3 Object Lock (for ransomware mitigation). EFS file systems are backed up daily using **AWS Backup** with a retention policy of 30 days.
  - **Recreation:** In the event of a disaster, OpenTofu templates are executed to rebuild the entire networking, security groups, ALB, Valkey, and compute layers. Golden AMIs are pulled from the AMI catalog, and the database is restored from the last RDS snapshot.
- **Pros:**
  - Lowest ongoing cost index, as only backup storage and snapshots are paid for.
  - Minimal architectural complexity during standard day-to-day operations.
- **Cons:**
  - **Highest Recovery Time Objective (RTO):** Rebuilding the entire infrastructure, provisioning databases, and downloading snapshot states can take hours or even days.
  - **Highest Recovery Point Objective (RPO):** Data loss can be up to 24 hours (depending on the last snapshot time), unless PITR is fully functional and logs are intact.
  - Relies heavily on the availability of control plane operations during a crisis.

---

## 3. Disaster Recovery Strategic Decision Matrix

The following matrix compares the evaluated DR options to assist senior leadership in balancing risk mitigation against financial investment:

| DR Option Evaluated | Account Boundary | Regional Boundary | Network Isolation | Target RTO | Target RPO | Relative Cost Index | PDPA Compliance Basis |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Option 1: Cross-Region & Separate Account** | Isolated (Different Account) | Isolated (`ap-southeast-1`) | High (Distinct VPCs) | < 15 Minutes | < 5 Seconds | ★★★★☆ (High) | Section 129 Transfer basis with formal TIA & SCCs |
| **Option 2: In-Region & Separate Account** | Isolated (Different Account) | Shared (`ap-southeast-5`) | High (Distinct VPCs) | < 30 Minutes | < 1 Minute | ★★★☆☆ (Medium) | 100% In-Region local residency guaranteed |
| **Option 3: In-Region & Same Account** | Shared (Same Account) | Shared (`ap-southeast-5`) | Medium (VPC Peering) | < 60 Minutes | < 5 Minutes | ★★☆☆☆ (Low) | 100% In-Region local residency guaranteed |
| **Option 4: Backup & Restore (On-Demand)** | Shared or Isolated | Shared or Isolated | Low (Rebuilt on need) | 2 - 4 Hours | < 24 Hours | ★☆☆☆☆ (Minimal) | Depends on backup storage vault residency |

---

## 4. Key Recommendations and Implementation Blueprint

To achieve the optimal balance of business continuity, fiscal responsibility, and regulatory compliance, the project prioritises a **phased implementation roadmap**:

1. **Phase 1 (Immediate - Active/Passive Backup & Restore):** Implement full Option 4 using OpenTofu IaC to ensure that the entire 3-tier PHP-FPM environment can be spun up deterministically within 2 hours. Enforce strict cross-account backup copies using AWS Backup Vaults.
2. **Phase 2 (Medium Term - In-Region Account Isolation):** Transition to Option 2 by provisioning a secondary staging/DR account within the Malaysia region. This protects the organisation against administrative errors and credential leaks, which represent over 80% of enterprise "disaster" events.
3. **Phase 3 (Enterprise Target - Cross-Region Pilot Light):** Where business-critical service level agreements (SLAs) require near-zero downtime, deploy Option 1 with an active RDS Read Replica in Singapore and a scaled-to-zero compute ASG tier, establishing a robust, legally-compliant cross-border failover framework under PDPA Section 129.
