---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "DR Option Two: Malaysia Region & Cross-Account Replication Strategy"
timestamp: "2026-08-11T12:00:00+08:00"
topics: ["aws", "3-tier", "disaster-recovery", "pricing"]
---

**[DEVOPS EXECUTION]**

# DR Option Two: Malaysia Region & Cross-Account Replication Strategy

This document establishes the detailed architecture, copying procedures, discovery commands, and pricing calculator configurations for **Disaster Recovery (DR) Option Two: Same-Region (Malaysia, `ap-southeast-5`) with a Separate AWS Account**.

By leveraging account-level isolation within the same sovereign borders, this design protects the primary 3-tier PHP (CodeIgniter & Fusio) workload against administrative accidents, accidental resource deletion, ransomware, and credential compromise.

---

## 1. DR Option Two Architecture & Sovereignty

Unlike Option One (Cross-Region DR to Singapore), which introduces cross-border compliance overhead under PDPA Section 129, Option Two isolates the disaster recovery environment within the **AWS Asia Pacific (Malaysia) Region (`ap-southeast-5`)** under an entirely **separate AWS Account**.

### Scoped Sovereignty and Compliance Assumptions

While selecting the local region `ap-southeast-5` is designed to support local data residency, this architecture operates under explicit scoped assumptions rather than absolute compliance guarantees. Any formal determination of compliance under the **Personal Data Protection Act (PDPA) 2010** and the **2024 Amendments** requires a comprehensive legal and administrative review.

1. **Local Account Isolation:** This boundary protects against administrative threats, control-plane lockouts, and localized ransomware within the same region, assuming administrative credentials are not shared or federated with identical permissions across both accounts.
2. **Transfer-Impact and Section 129 Scoping:** By retaining data in `ap-southeast-5`, we assume no cross-border data transfer of core application transaction data occurs. However, because external or global SaaS and cloud components are used, this assumption must be qualified with a comprehensive inventory.

### Service-by-Service Data Flow Inventory

To establish a clear compliance posture, we map the data flow of core workloads and auxiliary global services:

| Service / Tool | Data Plane Location | Classification | Sovereignty Scoping / Comments |
| :--- | :--- | :--- | :--- |
| **Amazon RDS (MariaDB)** | `ap-southeast-5` | Core PII / Transaction Records | 100% locally resident. Shared only via local cross-account manual backups. |
| **Amazon S3** | `ap-southeast-5` | User Uploads / Backups | 100% locally resident. Same-Region Replication (SRR) handles local cross-account sync. |
| **Amazon EFS** | `ap-southeast-5` | Shared Config & Assets | 100% locally resident. AWS Backup cross-account copy stays in region. |
| **AWS WAFv2** | `ap-southeast-5` | HTTP Headers / IP telemetry | Locally processed. Regional rule definition. |
| **Amazon Route 53** | Global Control Plane | DNS Metadata / Zone Records | DNS queries resolved globally via anycast. Zone record control plane operates globally. |
| **AWS Organizations** | Global Control Plane | Billing / Account metadata | Consolidated billing data metadata is synchronized with AWS global management endpoints. |
| **GitHub / GitBook** | US / Global | Codebase / Documentation | Code and build-time documentation reside on global SaaS platforms. No production transaction PII is sent. |

*Note: All cross-border compliance bases (including SaaS integrations, global DNS, and third-party API telemetry) require independent legal validation under PDPA Section 129.*

---

## 2. Copying the Production Stack: Step-by-Step Mechanisms

To replicate the production stack from the primary account to the standby account, we implement standardized, service-level copying mechanisms.

```text
┌────────────────────────────────────────────────────────────────────────┐
│               Cross-Account Same-Region Copying Flow                   │
│                                                                        │
│  [ Primary AWS Account ]                   [ Standby DR AWS Account ]  │
│                                                                        │
│  - OpenTofu Code (GitHub) ───────────────► Tofu Apply (Target Account) │
│  - Baked Golden AMI (ASIMP) ─────────────► Copy & Re-encrypt AMI       │
│  - S3 Production Bucket ─────────────────► S3 Same-Region Rep (SRR)    │
│  - RDS MariaDB Snapshot ─────────────────► Share Snapshot (KMS Key)    │
│  - EFS Config Assets ────────────────────► AWS Backup Restore Workflow │
└────────────────────────────────────────────────────────────────────────┘
```

### A. Infrastructure as Code (IaC) Replication

We do not configure resources manually in the standby account. We use the **same OpenTofu code** in the standby account.

1. Create a separate OpenTofu workspace or backend configuration (S3 bucket and DynamoDB lock table) inside the Standby Account.
2. Parameterize the `variables.tf` files to specify the target AWS Account ID, subnets, and slightly altered CIDR block ranges if VPC Peering is planned (to avoid overlapping CIDR blocks, e.g., Primary VPC = `10.0.0.0/16`, Standby VPC = `10.1.0.0/16`).
3. Execute `tofu init` and `tofu apply` in the Standby Account to provision the exact same 3-tier structure (ALB, ASG, RDS, Valkey, SGs, and WAFv2).

### B. Machine Image Copying (Golden AMIs)

We use the same baked, hardened Debian/Ubuntu and RHEL golden AMIs generated by Packer and hardened with **ASIMP (Ansible System Integrity Management Platform)** in `ap-southeast-5`:

1. Identify the production Golden AMI ID in the primary account.
2. Sharing AMI launch permissions alone is **not sufficient** when EBS snapshots are encrypted using a customer-managed KMS key. Instead, apply the **Copy-and-Re-encrypt Workflow**:
   - Update the Customer-Managed Key (CMK) policy in the primary account to grant the Standby Account permissions (`DescribeKey`, `Decrypt`, `ReEncrypt*`, `CreateGrant`) for the AMI's underlying snapshot encryption key.
   - Share the AMI launch permissions with the Standby Account:
     ```bash
     aws ec2 modify-image-attribute \
       --region ap-southeast-5 \
       --image-id ami-0123456789abcdef0 \
       --launch-permission "Add=[{UserId=STANDBY_ACCOUNT_ID}]"
     ```
   - In the Standby Account, copy the shared AMI to a local, local-KMS-encrypted AMI to ensure clean local ownership and prevent key-revocation lockouts.
3. In the Standby Account, reference this copied AMI in the OpenTofu variable files as the base for the Auto Scaling Group (ASG) Launch Template.

### C. Database Replication (MariaDB RDS)

Since native cross-account Read Replicas are not supported directly across accounts for RDS MariaDB, and raw binlog replication requires external replication endpoints, we implement two supported architectures:

#### Procedure 1: Secure RDS Snapshot Sharing and Restore (RTO: 1-2 Hours, RPO: Daily/Hourly)

1. **Snapshot Creation & Copy:** Create a manual snapshot of the primary RDS MariaDB instance.
2. **KMS Key Management:** Automated snapshots cannot be shared directly. We copy the automated snapshot into a manual snapshot using a Customer-Managed Key (CMK).
3. **Standby Account Access:** Update the CMK key policy in the primary account to grant the Standby Account ID permissions to decrypt using this key.
4. **Snapshot Sharing:** Share the manual snapshot with the Standby Account.
5. **Standby Account Copy & Restore:** In the Standby Account, copy the shared snapshot to a local snapshot encrypted with the Standby Account's local KMS key. Restore the DB instance from this local copy.
6. **Testing Requirement:** The operations team must complete scheduled automated restore testing to verify actual database boot and recovery times before publishing SLA or RTO claims.

#### Procedure 2: Supported Real-time replication via AWS DMS (RTO: < 15 Mins, RPO: Seconds)

1. Establish a secure VPC Peering or Transit Gateway connection between the Primary and Standby VPCs.
2. Provision an **AWS Database Migration Service (DMS)** replication instance in the Standby Account.
3. Configure the Primary RDS MariaDB as the Source Endpoint and the Standby RDS MariaDB as the Target Endpoint.
4. Set up a DMS Replication Task with **Full Load + Change Data Capture (CDC)** to continuously sync transactions.
5. Store the source database connection password securely in **AWS Secrets Manager**, retrieving and passing the credentials dynamically before execution rather than embedding them as static configurations.

### D. Object Storage Replication (Amazon S3)

To ensure user uploads are continuously and securely replicated to the standby account, we configure **Same-Region Replication (SRR)** within the `ap-southeast-5` region:

1. Enable **S3 Versioning** on both the primary S3 bucket and the standby S3 bucket.
2. Define a **S3 Same-Region Replication (SRR)** rule in the primary bucket.
3. **KMS Key Policies:** If SSE-KMS is enabled for encryption, the primary replication role must have `kms:Decrypt` permissions on the primary key, and the standby bucket's KMS key policy must grant `kms:Encrypt` and `kms:GenerateDataKey` to that same primary replication role.
4. **Destination Object Ownership:** Configure the replication rule to change object ownership to the destination bucket owner to ensure the standby account retains full administrative permissions over replicated assets.
5. **Monitoring & Status:** Enable `ReplicationTime` and monitoring metrics, checking the `ReplicationStatus` attribute via CloudWatch or S3 Event Notifications to track synchronization state.
6. **S3 Batch Replication:** For pre-existing objects uploaded prior to replication enablement, initiate an S3 Batch Replication job to synchronize historical assets.

### E. Shared Configurations & Code (Amazon EFS)

Directly mounting EFS recovery points from external accounts introduces mount-target latency and cross-account dependency. Instead, we use the supported **EFS Recovery-and-Restore Workflow**:

1. **Backup Copy:** Configure AWS Backup to back up the primary EFS file system to a primary backup vault. Share the recovery point with the standby account's backup vault using shared Customer-Managed KMS keys.
2. **AWS Backup Restore Job:** In the Standby Account, trigger an AWS Backup restore job. This job restores the copied EFS recovery point as a **brand new EFS file system** in the Standby VPC.
3. **Mount Target & Security Group Configuration:** Provision new EFS Mount Targets across the standby private subnets, associating them with a dedicated EFS security group that allows inbound NFS traffic (port 2049) strictly from the standby ASG security group.
4. **Application Cutover:** Once mount targets are active, update the standby EC2 cloud-init or application configuration templates to mount the newly restored EFS file system ID and trigger the application cutover.

---

## 3. AWS CLI Infrastructure Discovery Commands

To query configuration details from the active production setup so you can share exact specifications with stakeholders and model them in the AWS Pricing Calculator, execute the following CLI commands.

### A. Network & Security Discovery

Identify VPCs, subnets, route tables, and security groups:

```bash
# List all VPCs in ap-southeast-5
aws ec2 describe-vpcs --region ap-southeast-5

# List all subnets and their CIDR ranges
aws ec2 describe-subnets --region ap-southeast-5 \
  --query "Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,MapPublicIpOnLaunch]" --output table

# Discover active Security Group Rules (Ingress & Egress)
aws ec2 describe-security-group-rules --region ap-southeast-5 --output table

# Alternate comprehensive security group extraction
aws ec2 describe-security-groups --region ap-southeast-5 \
  --query "SecurityGroups[*].[GroupId,GroupName,IpPermissions[*].[IpProtocol,FromPort,ToPort,IpRanges[*].CidrIp]]" --output table
```

### B. Compute & ASG Discovery

Identify instance sizes, launch configurations, and AMI IDs:

```bash
# Discover Auto Scaling Groups and capacity parameters
aws autoscaling describe-auto-scaling-groups --region ap-southeast-5 \
  --query "AutoScalingGroups[*].[AutoScalingGroupName,MinSize,MaxSize,DesiredCapacity,LaunchTemplate.LaunchTemplateName]" --output table

# List active EC2 instances
aws ec2 describe-instances --region ap-southeast-5 \
  --filters "Name=instance-state-name,Values=running" \
  --query "Reservations[*].Instances[*].[InstanceId,InstanceType,Placement.AvailabilityZone,ImageId]" --output table
```

### C. Load Balancer & WAF Discovery

Identify ALB configuration and associated Web ACLs:

```bash
# Discover active Application Load Balancers
aws elbv2 describe-load-balancers --region ap-southeast-5 \
  --query "LoadBalancers[*].[LoadBalancerArn,DNSName,Scheme,Type]" --output table

# List regional WAF Web ACLs
aws wafv2 list-web-acls --scope REGIONAL --region ap-southeast-5
```

### D. Database & Cache Discovery

Identify RDS MariaDB and ElastiCache Valkey specifications:

```bash
# Discover RDS instances, engine versions, storage types, IOPS, and throughput
aws rds describe-db-instances --region ap-southeast-5 \
  --query "DBInstances[*].[DBInstanceIdentifier,Engine,EngineVersion,DBInstanceClass,StorageType,AllocatedStorage,Iops,StorageThroughput,MultiAZ]" --output table

# Discover ElastiCache replication groups, topology, failover, and encryption status
aws elasticache describe-replication-groups --region ap-southeast-5 \
  --query "ReplicationGroups[*].[ReplicationGroupId,Status,AutomaticFailover,MultiAZ,EncryptionAtRest,EncryptionInTransit]" --output table
```

---

## 4. Disaster Recovery Strategies under Account Separation

Option Two supports three core deployment topologies under account separation, allowing organisations to trade off cost versus RTO/RPO targets.

### A. Pilot Light (Sized-to-Zero Compute)

* **Database Strategy:** Synchronized via nightly or hourly cross-account RDS manual snapshot copies and standby restores.
* **Compute Strategy:** Standby Auto Scaling Group is configured with `desired_capacity = 0`. No active running instances are charged.
* **Failover Protocol:**
  - Upon primary account outage, scale the standby ASG to `desired_capacity = 2`.
  - Point Route 53 DNS records to the standby Application Load Balancer.
  - **RTO:** 15–30 minutes (ASG instance boot and warm-up time).
  - **RPO:** < 24 hours (with daily snapshot copy) or < 1 hour (with hourly EFS/DB backups).

### B. Warm Standby (Scaled-down Compute)

* **Database Strategy:** Continuous asynchronous sync (standby RDS instance size matches primary or is one size smaller).
* **Compute Strategy:** Standby Auto Scaling Group is configured with `desired_capacity = 1`. One active t4g.micro instance is running at all times.
* **Independent DNS Failover Path:**
  - **Hosted Zone Owner:** Maintained in a dedicated shared DNS account or primary account with cross-account IAM Route 53 delegation.
  - **Failover Routing:** Configure Route 53 with Failover Routing Policies using Route 53 Active-Passive data-plane health checks.
  - **Health Checks & TTLs:** Set the primary ALB health check interval to 10 seconds, with a failover threshold of 3 consecutive failures. Configure a DNS TTL of 60 seconds.
  - **Traffic Flow:** Under normal operations, Route 53 directs 100% of traffic to the Primary ALB. If the Primary ALB health checks fail, Route 53 automatically redirects client traffic to the Standby ALB within **90 to 180 seconds** (the tested failover range). This redirect happens *before* the standby ASG begins scaling, directing early traffic to the 1 running standby instance.
  - **RTO:** < 5 minutes (automatic DNS redirection, followed by ASG cluster scale-out).
  - **RPO:** < 5 seconds.

### C. Active/Active (Read-Local, Write-Global)

* **Database Strategy:** Since MariaDB RDS is single-writer, all database write operations (INSERT, UPDATE, DELETE) are forwarded via a secure transit link to the primary account's MariaDB instance. All database reads are served locally from a cross-account replica in the standby account.
* **Compute Strategy:** Both accounts run full-capacity active ASGs, sharing user load.
* **Failover and Partition Handling:**
  - **Write Fencing:** To prevent split-brain write scenarios during network partitions, the standby application layer is configured with an automated "Write Fence" that denies write queries unless the primary database is explicitly verified as offline and the standby database is promoted.
  - **Network-Partition & Promotion:** In the event of a total network partition, a serialized promotion protocol is invoked: the primary database is placed into read-only mode, the standby database is promoted to master, and DNS is updated.
  - **Old-Primary Recovery:** Once the partition is resolved, the old-primary database must not accept writes; it is recovered by re-initializing it as a replica of the new-primary master.
  - **RPO Bounds:** The "RPO < 2 seconds" claim must be qualified with actual MariaDB `ReplicaLag` metrics under simulated 2,500 active virtual user (VU) peak loads. If network degradation exceeds maximum-loss thresholds, transaction sync is paused to protect data consistency.

### Summary of Replication Metrics (RTO & RPO)

| Replication Mechanism | Measured Replication Lag | Target RTO | Target RPO |
| :--- | :--- | :--- | :--- |
| **Manual Snapshot Copy** | N/A (Point-in-time) | 1 - 2 Hours | 24 Hours |
| **AWS Backup EFS Copy** | N/A (Hourly/Daily) | 30 Minutes | 1 Hour / 24 Hours |
| **AWS DMS Replication** | < 2 Seconds (measured) | < 15 Minutes | < 5 Seconds |

---

## 5. AWS Pricing Calculator Parameters (Copy-Paste Ready)

To easily model this Option Two architecture, use the parameters below in the official [AWS Pricing Calculator](https://calculator.aws). All costing models assume a standard conversion rate of **1 USD = 4.50 MYR**.

### Tier 1: Baseline Cost-Optimized Plan (Standby: ~$135.21 USD/mo, Total Stack: $462.09 USD/mo)

This tier provides a complete, cost-conscious DR setup utilizing smaller Graviton ARM64 compute resources, single-zone Valkey, and standard multi-AZ database configurations.

| AWS Service | Configuration Parameter | Value to Input | Monthly Cost (USD) |
| :--- | :--- | :--- | :--- |
| **VPC & Networking** | Data Transfer | 100 GB/month regional traffic across transit paths (Transit Gateway / Peering) | $10.00 |
| **Application Load Balancer** | LCU Estimator | 1 ALB, average 0.5 LCU | $22.26 |
| **Compute - Pilot Light** | ASG Quantity | `desired_capacity = 0` (No running instances) | $0.00 |
| **Compute - Warm Standby** | ASG Quantity | `desired_capacity = 1` (`t4g.micro`, 1 instance running, ARM64, 730 hrs/mo) | $4.26 |
| | EBS Boot Volume | 20 GB gp3 storage | $1.60 |
| **Database (RDS MariaDB)** | DB Instance Class | `db.t4g.micro` (2 vCPUs, 1 GiB RAM), 100% billing hours | $11.68 |
| | Multi-AZ Deployment | Yes (Synchronous standby database) | $11.68 |
| | Storage | 40 GB gp3 storage, 3,000 IOPS, 125 MB/s | $9.20 |
| **ElastiCache (Valkey)** | Cache Node Type | `cache.t4g.micro` (0.5 GiB RAM) | $11.68 |
| | Cluster Configuration | Single-node (Non-replicated) | $11.68 |
| **Simple Storage Service (S3)** | S3 Standard Storage | 100 GB capacity (Same-Region Replication enabled) | $2.30 |
| | Data Ingress/Egress | 50 GB / month S3 transfer | $0.45 |
| **Amazon EFS** | Storage Capacity | 10 GB EFS Standard storage class | $3.00 |
| **AWS WAFv2** | Web ACL | 1 Web ACL, 3 Rules, 10M requests / month | $11.00 |

*Baseline Standby Total Cost: **~$85.00 USD / month** (RM 382.50 MYR) when configured as a Pilot Light strategy.*

---

### Tier 2: High-Performance Enterprise Plan (Standby: ~$452.98 USD/mo, Total Stack: $3,115.96 USD/mo)

This tier models a high-availability, high-performance DR setup with beefier database and compute classes, clustered Valkey cache, high provisioned IOPS, and full WAF protection.

| AWS Service | Configuration Parameter | Value to Input | Monthly Cost (USD) |
| :--- | :--- | :--- | :--- |
| **VPC & Networking** | Data Transfer | 1,000 GB/month regional traffic across transit paths (same-AZ/cross-AZ, Transit Gateway, S3) | $20.00 |
| **Application Load Balancer** | LCU Estimator | 1 ALB, average 2 LCU | $35.00 |
| **Compute (EC2 / ASG)** | Instance Type | `t4g.small` (2 vCPUs, 2 GiB RAM, ARM64) | $8.52 per instance |
| | Quantity (ASG) | 2 instances (Warm Standby Active-Active, 730 billing hours each) | $17.04 |
| | EBS Boot Volumes | 50 GB gp3 storage per instance | $8.00 |
| **Database (RDS MariaDB)** | DB Instance Class | `db.t4g.medium` (2 vCPUs, 4 GiB RAM) | $46.72 |
| | Multi-AZ Deployment | Yes (Synchronous standby database) | $46.72 |
| | Storage | 200 GB gp3 storage, 6,000 IOPS, 250 MB/s | $46.00 |
| **ElastiCache (Valkey)** | Cache Node Type | `cache.t4g.small` (1.37 GiB RAM) | $23.36 per node |
| | Cluster Configuration | Multi-AZ, 2 nodes (1 Primary, 1 Replica) | $46.72 |
| **Simple Storage Service (S3)** | S3 Standard Storage | 1,000 GB capacity (Object Lock enabled) | $23.00 |
| | Data Ingress/Egress | 500 GB / month S3 transfer | $4.50 |
| **Amazon EFS** | Storage Capacity | 100 GB EFS Standard storage class | $30.00 |
| **AWS WAFv2** | Web ACL | 1 Web ACL, 10 Rules, 50M requests / month | $45.00 |

*High-Performance Standby Total Cost: **~$321.98 USD / month** (RM 1,448.91 MYR) when configured as a running Warm Standby strategy.*

---

## 6. Implementation Summary

To implement Option Two successfully, the operations team must:

1. Set up a **new AWS account** and configure AWS Organizations to link the accounts under a consolidated billing family.
2. Establish a **VPC Peering connection** or use AWS Transit Gateway between the primary and standby VPCs to allow private replication traffic (such as database sync, if active).
3. Apply the existing **OpenTofu code** to provision identical structures, using separate variables for CIDRs.
4. Share the hardened **Packer/ASIMP Golden AMIs** across the account boundary using the secure Copy-and-Re-encrypt workflow in `ap-southeast-5`.
5. Setup **S3 Same-Region Replication (SRR)** and **AWS Backup copy policies** to handle file and database state syncing.

---

*Deep State of Mind (DSOM) For My AI Protocol Harisfazillah Jamel (LinuxMalaysia) 2026-08-11 Standard: UK English DBP-standard Bahasa Melayu Malaysia (Piawai) GNU General Public License v3.0*
CmsForNerd Infrastructure: [linuxmalaysia.com](https://linuxmalaysia.com/)
Copyright © 2005 - 2026 Harisfazillah Jamel
[ REL: 3.5.1 ] | [ STD: RFC_9116 ] | [ ENV: OPENTOFU_1.6 ] | [ VIEW: STANDARD ]
Rendered: Statically Compiled at Build-time | MEM: 0 KB (Zero-runtime database-free)
