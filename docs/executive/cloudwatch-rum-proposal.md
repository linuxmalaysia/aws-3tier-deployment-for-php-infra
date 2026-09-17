---
layout: default
okf_version: "0.1"
type: "Technical Proposal & Financial Justification"
title: "CloudWatch RUM Integration & Observability Consolidation Proposal"
timestamp: "2026-08-12T00:00:00+08:00"
topics: ["aws", "cloudwatch", "rum", "finops", "apm"]
---

**[STRATEGIC FINANCIAL]**

# Technical Proposal & Justification: CloudWatch RUM Integration & Observability Consolidation

```text
Document Reference : PROP-OBS-2026-RUM-01
Classification     : Technical Proposal & Financial Justification
Region             : AWS Malaysia (ap-southeast-5)
Target Audience    : Executive Management & Technical Architecture Board
Subject            : CloudWatch RUM Adoption & Decommissioning of AWS-hosted Dynatrace Agents
Status             : Draft / For Architectural Review
```

---

## Executive Summary

To eliminate operational toil and recurring third-party software licensing overheads, this proposal outlines the architectural consolidation of client-side and application-level monitoring under **Amazon CloudWatch Real User Monitoring (RUM)** and the unified **Amazon CloudWatch Agent**.

Currently, our hybrid environment relies on an on-premise Dynatrace deployment extending proprietary OneAgents into AWS workloads. This setup incurs substantial dual-observability expenditure, agent-level CPU/memory footprints on EC2 compute tiers, and cross-boundary network egress charges back to the on-premise monitoring core.

By activating native **CloudWatch RUM**, we capture real-world client performance, Core Web Vitals (CWV), client-side JavaScript errors, and end-to-end tracing seamlessly within the **AWS Malaysia (`ap-southeast-5`)** sovereign boundary at a predictable consumption-based rate of **$1.00 USD per 100,000 RUM events**. This transition permits the formal decommissioning of Dynatrace agents within AWS, yielding immediate licensing savings and consolidating monitoring into a single pane of glass alongside existing CloudWatch metrics and alarms.

---

## 1. Problem Statement: The Cost & Overhead of AWS-Hosted Dynatrace

Maintaining third-party enterprise APM agents (Dynatrace OneAgent) inside AWS infrastructure introduces three major operational and financial liabilities:

1. **Dual Licensing & Commercial Redundancy:**
Our AWS estate already incurs baseline CloudWatch costs (~$80 to $90 USD/month in the `ap-southeast-5` baseline audit). Running Dynatrace agents on AWS EC2 instances consumes additional Dynatrace Host Units (HUs) and Digital Experience Monitoring (DEM) units for user sessions, resulting in redundant expenditure across two operational stacks.
2. **Compute Resource Tax & Runtime Friction:**
Dynatrace OneAgents inject deep bytecode instrumentation and native monitoring hooks at the OS and container level. In containerised or right-sized Graviton fleets (`c8g`, `c6g`), this introduces a 2% to 5% continuous memory and CPU tax, artificially inflating compute instance requirements.
3. **Operational Fragmentation & MTTD/MTTR Drag:**
When client-facing incidents occur, engineers currently cross-examine Dynatrace for front-end issues and pivot to AWS CloudWatch for infrastructure, load balancer, and RDS telemetry. Eliminating this context switching directly reduces Mean Time to Detect (MTTD) and Mean Time to Remediate (MTTR).

---

## 2. Technical Architecture: Amazon CloudWatch RUM

CloudWatch RUM provides client-side observability by embedding a lightweight, asynchronous, open-source JavaScript web client (`aws-rum-web`) into our front-end application templates.

```text
[ End-User Browser ]
         │
         ▼  (Lightweight snippet: ~10-20 events/session)
[ CloudWatch RUM App Monitor Endpoint ]
         │
         ├──► CloudWatch Metrics (CWV, Page Load, Latency, Errors)
         ├──► CloudWatch Logs (/aws/vendedlogs/RUMService...)
         └──► AWS X-Ray (End-to-End Distributed Trace linking ALB -> ECS/EC2 -> RDS)
```

With this deployment model:

* **Core Web Vitals Telemetry:** Directly records Largest Contentful Paint (LCP), Cumulative Layout Shift (CLS), and Interaction to Next Paint (INP) across end-user devices, browsers, and local ISPs within Malaysia.
* **JavaScript & HTTP Error Tracking:** Automatically aggregates unhandled exceptions, stack traces, and 4xx/5xx asynchronous API payload failures.
* **Distributed Trace Correlation:** Injects standard W3C trace context headers into client HTTP calls. This links client transactions directly into server-side **AWS X-Ray** traces across the Application Load Balancer and application backend, establishing full-stack root-cause correlation without proprietary host agents.

---

## 3. Financial Modeling & Sizing Estimation

### 3.1 CloudWatch RUM Cost Model

CloudWatch RUM uses purely consumption-based billing with no minimum commitments, fixed host fees, or base subscription floors:

* **Unit Pricing:** **$1.00 USD per 100,000 data events** ($0.00001 per event).
* **Free Tier Allocation:** First **1,000,000 events/month** free (introductory evaluation window).
* **Event Composition:** Standard page navigation produces approximately **10 to 20 events** per complete user session (Page Load, Navigation Timing, Web Vitals, API calls, and Errors).
* **Effective Session Unit Cost:** ~$0.10 to $0.20 USD per 1,000 user sessions.

### 3.2 Monthly Workload Projections (AWS Malaysia `ap-southeast-5`)

The financial impact across three workload profiles demonstrates the low marginal cost of adding RUM:

| Operational Scenario | Estimated Monthly Sessions | Monthly Events Captured | CloudWatch RUM Cost (USD) | Equivalent Cost (MYR @ 4.50) |
| --- | --- | --- | --- | --- |
| **Baseline Profile** | 250,000 sessions | 2,500,000 events | **$25.00** | **RM 112.50** |
| **Moderate Production** | 1,000,000 sessions | 10,000,000 events | **$100.00** | **RM 450.00** |
| **Peak Campaign Load** | 3,500,000 sessions | 35,000,000 events | **$350.00** | **RM 1,575.00** |

*Note: In high-volume environments, CloudWatch RUM supports a native **telemetry sampling rate** (e.g., 25% or 50%), allowing linear expenditure control without sacrificing statistical anomaly detection.*

### 3.3 Comparative TCO: CloudWatch RUM vs. Dynatrace AWS Agent Footprint

| Evaluation Dimension | Dynatrace OneAgent (on AWS) | Amazon CloudWatch RUM | Architectural Advantage |
| --- | --- | --- | --- |
| **Licensing Framework** | Commercial per-Host-Unit / DEM session pack | Pure utility metering ($1.00 per 100k events) | No prepaid licensing commitments or shelf-ware |
| **Estimated Monthly Run-Rate** | ~$600 – $1,800 USD (Host licenses + DEM units) | **~$25 – $100 USD** (Based on 250k–1M sessions) | **85% to 92% cost reduction on front-end monitoring** |
| **Host Resource Impact** | 2–5% CPU, 200–400 MB RAM per instance | **0% Host Overhead** (Runs entirely in browser) | Unlocks compute density on EC2/Graviton |
| **Agent Maintenance Toil** | Requires OS patching, agent upgrades, kernel module checks | **Zero Maintenance** (Static CDN JS client script) | Eliminates Day 2 operational toil and pipeline patching |
| **Data Residency & Sovereignty** | Telemetry exported to on-premise cluster or third-party SaaS | Retained natively inside **AWS Malaysia (`ap-southeast-5`)** | Compliant with sovereign data governance mandates |

---

## 4. Architectural Justification & Strategic Benefits

1. **Elimination of Third-Party Agent Fragility:**
Dynatrace OneAgent updates often lag modern Linux kernel builds or introduce glibc compatibility hurdles on lean container baselines. Transitioning client monitoring to CloudWatch RUM decouples host maintenance from application observability.
2. **Unified Incident Remediation (Single Pane of Glass):**
Front-end error anomalies trigger standard CloudWatch Composite Alarms. Operators observe real user impact alongside infrastructure telemetry (ALB response times, RDS CPU, Target Response Times) inside unified CloudWatch Operational Dashboards.
3. **Data Sovereignty Compliance:**
For public sector and enterprise workloads operating under regulatory frameworks in Malaysia, CloudWatch RUM keeps all telemetry, client IP masking, and session diagnostic traces within the local AWS `ap-southeast-5` region, avoiding cross-border data transfers.

---

## 5. Implementation Roadmap & Migration Plan

```text
Phase 1: App Monitor Provisioning (Week 1)
  └── Create CloudWatch RUM App Monitor via AWS CLI / Terraform in ap-southeast-5.
  └── Enable Amazon Cognito Identity Pool for guest telemetry authorisation.
  └── Configure Telemetry Data: Core Web Vitals, JS Errors, HTTP 4xx/5xx requests.

Phase 2: Client Web Integration & Canary Test (Week 2)
  └── Embed aws-rum-web snippet into staging application templates.
  └── Validate X-Ray header propagation across the Application Load Balancer.
  └── Verify CloudWatch RUM dashboard data ingestion and session metrics.

Phase 3: Production Rollout & Dynatrace Decommissioning (Week 3 - 4)
  └── Deploy RUM snippet to production with a 25% initial sampling rate.
  └── Calibrate sampling to steady-state (e.g., 50% or 100% depending on volume).
  └── Decommission Dynatrace OneAgent packages from EC2 launch templates and AMIs.
  └── Reclaim Dynatrace Host Unit / DEM licenses for core on-premise workloads.
```

---

## 6. Operational Delivery: EC2 Unified CloudWatch Agent

Hypervisors cannot inspect the guest operating system's internal RAM allocations or partitioned file systems due to memory virtualization boundaries. Deploying the open-source **unified CloudWatch agent** (`amazon-cloudwatch-agent`) bridges this gap without the heavy CPU/RAM overhead of third-party monitoring daemons.

### 6.1 Capability & Telemetry Matrix

| Infrastructure Tier | CPU | Memory | Network I/O | Disk Space / IOPS | Implementation Mechanism | Metric Billing Category |
| --- | --- | --- | --- | --- | --- | --- |
| **EC2 Instances** | `CPUUtilization` | `mem_used_percent` | `NetworkIn` / `NetworkOut` | `disk_used_percent` | Unified CloudWatch Agent (RPM/DEB package) | Basic metrics **Free**; OS memory/disk are **Custom Metrics** (~$0.30/metric) |
| **Amazon RDS** | `CPUUtilization` | `FreeableMemory` | `NetworkReceiveThroughput` | `FreeStorageSpace` / `ReadIOPS` | Native Hypervisor Telemetry (Enhanced Monitoring) | **100% Free** (Standard 1-min / 5-min intervals) |
| **ElastiCache (Valkey / Redis)** | `CPUUtilization` / `EngineCPUUtilization` | `BytesUsedForCache` / `DatabaseMemoryUsagePercentage` | `NetworkBytesIn` / `NetworkBytesOut` | In-memory eviction tracking / swap usage | Native Engine Telemetry | **100% Free** (Emitted natively into CloudWatch) |
| **Amazon EFS** | N/A (Serverless) | N/A (Serverless) | `DataReadIOBytes` / `DataWriteIOBytes` | `StorageBytes` / `PercentIOLimit` | Native EFS Storage Controller | **100% Free** (Standard metrics) |
| **Application Load Balancers** | N/A (L7 Layer) | N/A (L7 Layer) | `ProcessedBytes` / `ActiveConnectionCount` | N/A (HTTP target metrics) | Native Load Balancing Ingress | **100% Free** (Standard metrics) |

### 6.2 Configuration Profile (`/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json`)

{% raw %}
```json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "metrics": {
    "namespace": "CWAgent",
    "append_dimensions": {
      "AutoScalingGroupName": "${aws:AutoScalingGroupName}",
      "InstanceId": "${aws:InstanceId}"
    },
    "metrics_collected": {
      "mem": {
        "measurement": [
          "mem_used_percent",
          "mem_available"
        ]
      },
      "disk": {
        "measurement": [
          "disk_used_percent",
          "disk_free"
        ],
        "resources": [
          "/"
        ]
      },
      "net": {
        "measurement": [
          "bytes_sent",
          "bytes_recv",
          "drop_in",
          "drop_out"
        ],
        "resources": [
          "eth0"
        ]
      }
    }
  }
}
```
{% endraw %}

### 6.3 Financial Estimation: Custom Infrastructure Metrics

Because native AWS services (RDS, Valkey, EFS, ALB) emit performance metrics free of charge, billing applies strictly to the **custom OS metrics** collected by the CloudWatch agent on EC2 instances:

* **AWS Pricing:** First 10 custom metrics are **Free Tier**; thereafter, **$0.30 USD per metric/month** (for the first 10,000 metrics).
* **Standard Fleet Baseline:** 4 custom metrics per EC2 node (`mem_used_percent`, `mem_available`, `disk_used_percent`, `disk_free`) = **$1.20 USD / instance / month**.

| Active Fleet Scope | Monitored Custom Metrics | Monthly Cost (USD) | Equivalent Cost (MYR @ 4.50) |
| --- | --- | --- | --- |
| **Small Cluster (5 Instances)** | 20 metrics (10 billed) | **$3.00** | **RM 13.50** |
| **Target Fleet (15 Instances)** | 60 metrics (50 billed) | **$15.00** | **RM 67.50** |
| **Expanded Production (30 Instances)** | 120 metrics (110 billed) | **$33.00** | **RM 148.50** |

---

## 7. Consolidated Observability Sizing Summary

Combining client-side RUM telemetry and host-level CloudWatch Agent custom metrics yields a complete observability footprint inside AWS Malaysia (`ap-southeast-5`):

* **CloudWatch RUM (Client / End-User):** ~$25.00 to $100.00 USD/month (250k–1M web sessions).
* **CloudWatch Agent (EC2 RAM & Disk):** ~$15.00 USD/month (15-node production cluster).
* **Managed Services (RDS PostgreSQL, Valkey, EFS, ALB):** **$0.00 USD** (included in AWS baseline).
* **Standard Operational Alarms (10–20 alarms):** ~$1.00 to $2.00 USD/month ($0.10/alarm).

**Total Observability Envelope:** **~$40.00 to $117.00 USD/month** (~**RM 180.00 to RM 526.50 MYR**), compared against Dynatrace AWS OneAgent licensing, which typically exceeds **$600.00 to $1,800.00 USD/month**.

---

## 8. Estimation Context & Reference Data Disclaimer

> **Estimation & Reference Data Notice:** The Cost Explorer telemetry datasets, regional pricing models, and instance sizing profiles cited in this proposal represent empirical reference data from another project operating in the AWS Malaysia (`ap-southeast-5`) region. This reference data is utilized strictly for price, workload, and capacity estimation to align our project's architectural design and budget parameters, rather than representing actual historical spend of this repository.
