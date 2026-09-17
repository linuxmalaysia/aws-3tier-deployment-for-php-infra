---
layout: default
okf_version: "0.1"
type: "Technical Justification & Engineering Guide"
title: "Amazon CloudWatch APM, RUM & Infrastructure Telemetry Architecture Guide"
timestamp: "2026-08-12T00:00:00+08:00"
topics: ["aws", "cloudwatch", "apm", "rum", "telemetry"]
---

**[OBSERVABILITY & FINOPS]**

# Technical & Financial Justification: CloudWatch APM, RUM & Infrastructure Telemetry

```text
Document Reference : PAP-APM-2026-CW-02 (Revision 1 — figures verified against AWS official pricing, Sept 2026)
Classification     : Technical Architecture & Financial Justification
Region             : AWS Malaysia (ap-southeast-5)
Target Audience    : Executive Management & Technical Architecture Board
Prepared by        : Infrastructure Engineering
Status             : Ready for Board Review
```

---

## Executive Summary

To complete the decommissioning of on-premise Dynatrace agents within our AWS environment, this document establishes the adoption of **Amazon CloudWatch Application Performance Monitoring (APM)**, driven natively by **CloudWatch Application Signals**, operating alongside **CloudWatch Real User Monitoring (RUM)** and the **Unified CloudWatch Agent**. All figures in this guide are verified against official AWS regional pricing rates for **AWS Malaysia (`ap-southeast-5`)** (published September 2026).

Operating natively within the **AWS Malaysia (`ap-southeast-5`)** data boundary, this consolidated stack closes the final functional gap versus Dynatrace—distributed tracing, service topology mapping, end-user experience monitoring, and Service Level Objectives (SLOs)—using an open-standard, OpenTelemetry (OTel)-based architecture with no per-host agent licensing.

For a representative 15-node production cluster, the fully consolidated steady-state CloudWatch observability stack (RUM, APM, host metrics with 4 to 8 custom metrics/node, native service metrics, alarms/dashboards) is estimated at **$81.00 – $282.00 USD per month (~RM 364.50 – RM 1,269.00 MYR)** post-trial, against a current Dynatrace Full-Stack Monitoring spend estimated at **$870.00 – $1,110.00+ USD per month (~RM 3,915.00 – RM 4,995.00+ MYR)** based on published 2026 list pricing for 15 host units ($58–$74/host unit/month). This migration yields a potential recurring operational savings of **~$588.00 – $1,029.00 USD per month (~RM 2,646.00 – RM 4,630.50 MYR per month)** while keeping all telemetry local and reclaiming host compute capacity.

---

## 1. Why Change: Limitations of the Current Dynatrace Model

Maintaining third-party enterprise APM agents (Dynatrace OneAgent) inside AWS infrastructure introduces four major operational and financial liabilities:

1. **Proprietary OneAgent Lock-In:** Kernel-level bytecode instrumentation and deep OS hooks are a recurring source of compatibility issues during OS patching (glibc/kernel version drift) on Linux baselines.
2. **Fixed Host-Unit Licensing:** Dynatrace Full-Stack Monitoring is billed per 8 GiB RAM "host unit," so cost scales strictly with host RAM even when utilization remains low.
3. **Compute Agent Overhead:** Third-party agents typically carry materially higher RAM (~200–400 MB) and CPU overhead (~2–5%) than lightweight OpenTelemetry auto-instrumentation (~15–30 MB RAM, <0.2% CPU), creating a continuous resource tax across every monitored EC2 instance.
4. **Data Sovereignty & Egress:** Exporting telemetry outside the local AWS region creates unnecessary egress and external dependencies. Native CloudWatch tools retain all metrics, traces, and logs inside **AWS Malaysia (`ap-southeast-5`)**.

---

## 2. Architectural Comparison Matrix

With CloudWatch Application Signals, RUM, and Unified Agent, AWS provides direct feature parity with Dynatrace APM while adopting open standards:

| APM & Observability Capability | Legacy Dynatrace OneAgent | CloudWatch APM & Observability Suite | Architectural Advantage |
| :---: | :---: | :---: | :---: |
| **Instrumentation Engine** | Proprietary Bytecode Agent | OpenTelemetry (AWS Distro for OTel / ADOT) | Vendor-neutral, zero lock-in, patch-safe |
| **Host Memory/CPU Footprint** | ~200–400 MB RAM, 2–5% CPU | ~15–30 MB RAM, <0.2% CPU | Reclaims compute density on EC2 Graviton |
| **Distributed Tracing** | PurePath (Proprietary) | AWS X-Ray / W3C Trace Context | Standardized trace context headers |
| **Golden Metrics & SLOs** | Davis AI Baselines | Native Golden Signals & Burn-Rate SLO Alarms | Declarative latency (P95/P99) & fault tracking |
| **Service Dependency Map** | Smartscape Topology | CloudWatch Application Map | Auto-synthesized live microservice topology |
| **End-User Monitoring (EUM)** | Dynatrace DEM Sessions | CloudWatch RUM (Client-side Web Vitals) | Lightweight open-source JS snippet |
| **Host Telemetry (RAM/Disk/Net)** | Host Units (RAM-based) | Unified CloudWatch Agent (`amazon-cloudwatch-agent`) | Decoupled utility metering ($0.30/custom metric) |
| **Billing Architecture** | Fixed Annual / Host Units | Metered Consumption (Pay-per-signal / event / GB) | Pay strictly for ingested telemetry volume |

---

## 3. How CloudWatch Application Signals (APM) Is Priced

CloudWatch Application Signals measures application health through two metered, tiered billing dimensions (rates verified against official AWS CloudWatch pricing for `ap-southeast-5`, Sept 2026):

* **Golden Metrics (Signals):** **$1.50 USD per 1 million signals** for the first 100 million signals/month; $0.75 per 1M up to 1B; $0.30 per 1M beyond 1B. Signals include inbound HTTP request counts, outbound dependency calls (RDS, ElastiCache, HTTP APIs), error counts, latency histograms, and SLO-generated evaluation signals.
* **Transaction Search / Trace Ingestion:** **$0.35 USD per GB** for the first 10 TB/month; $0.20 per GB up to 30 TB; $0.15 per GB beyond 30 TB.
* **Evaluation Trial Window:** New accounts receive a one-time 3-month free trial (up to 100 GB trace ingestion or 100 million signals, whichever comes first), providing a zero-cost pilot window.

### Monthly Workload Projections (Application Signals — Post-Trial Steady State)

| Workload Profile | Signals / Month | Trace Ingestion | Monthly Cost (USD) | Monthly Cost (MYR @ 4.50) |
| :---: | :---: | :---: | :---: | :---: |
| **Baseline Profile** | 5,000,000 | 10 GB | **$11.00** | **RM 49.50** |
| **Moderate Production** | 20,000,000 | 40 GB | **$44.00** | **RM 198.00** |
| **High-Volume Tier** | 80,000,000 | 150 GB | **$172.50** | **RM 776.25** |

*(Calculation: $20\text{M signals} \times \frac{\$1.50}{1\text{M}} = \$30.00$; $40\text{ GB} \times \$0.35/\text{GB} = \$14.00$; Total = **$44.00 USD/month** steady state).*

---

## 4. CloudWatch Real User Monitoring (RUM) Client-Side Architecture

CloudWatch RUM provides end-user experience monitoring by embedding a lightweight, open-source JavaScript web client (`aws-rum-web`) into front-end web templates.

### 4.1 RUM Capabilities & Trace Integration

* **Core Web Vitals Telemetry:** Directly records Largest Contentful Paint (LCP), Cumulative Layout Shift (CLS), and Interaction to Next Paint (INP) across end-user devices in Malaysia.
* **JavaScript & HTTP Error Tracking:** Automatically aggregates unhandled client exceptions, stack traces, and 4xx/5xx API failures.
* **Distributed Trace Correlation:** Injects standard W3C / AWS X-Ray trace headers (`X-Amzn-Trace-Id`) into client HTTP calls by configuring `enableXRay: true` and `addXRayTraceIdHeader: true` in `aws-rum-web`. Downstream Application Load Balancers and web application frameworks must explicitly allow the `X-Amzn-Trace-Id` CORS header. Backend instrumentation (e.g., AWS X-Ray SDK or AWS Distro for OpenTelemetry / ADOT agent) running on compute nodes is required to record backend trace segments and link them to the client trace ID; client header propagation alone does not create server-side trace segments.
* **Client Privacy & Data Controls:** `aws-rum-web` privacy is managed via SDK configuration parameters such as `recordResourceUrl: false` (or regex patterns to strip sensitive URL query params), `allowCookies: false`, session sample rate tuning (`sessionSampleRate`), and event payload filtering prior to dispatch. Native IP masking is not supported in stock `aws-rum-web` without a custom proxy or wrapper; client IP data is handled at the CloudWatch RUM service boundary.

### 4.2 RUM Cost Model

* **Unit Pricing:** **$1.00 USD per 100,000 data events** ($0.00001 per event, verified against AWS pricing, Sept 2026).
* **Trial Allocation:** Includes a one-time, first-time per-account evaluation trial of **1,000,000 events** (for the first active month); thereafter, standard metering ($1.00 / 100k events) applies across steady-state workloads.
* **Event Volume:** Standard page navigation produces approximately **10 to 20 events** per complete user session (Page Load, Navigation Timing, Web Vitals, Errors). Cost tables below reflect post-trial steady-state pricing.

| Monthly Sessions | Est. Events (@20/session) | Steady-State Monthly Cost (USD) | Steady-State Monthly Cost (MYR @ 4.50) |
| :---: | :---: | :---: | :---: |
| **250,000 sessions** | 5,000,000 events | **$50.00** ($40.00 in 1st trial mo) | **RM 225.00** (RM 180.00 in trial mo) |
| **1,000,000 sessions** | 20,000,000 events | **$200.00** ($190.00 in 1st trial mo) | **RM 900.00** (RM 855.00 in trial mo) |

---

## 5. Capability & Infrastructure Telemetry Matrix

CloudWatch natively captures **CPU, Memory, Network I/O, and Disk Space** telemetry across all application tiers. Managed database and caching engines emit these streams natively at zero extra cost, whereas EC2 guest instances utilize the open-source **Unified CloudWatch Agent (`amazon-cloudwatch-agent`)** for internal guest OS memory, disk, and network metrics.

| Infrastructure Tier | CPU Telemetry | Memory Telemetry | Network I/O Telemetry | Disk Space / IOPS | Implementation Mechanism | Metric Billing Category |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EC2 Instances** | `CPUUtilization` | `mem_used_percent` | `NetworkIn` / `NetworkOut` | `disk_used_percent` | Unified CloudWatch Agent (RPM/DEB) | Basic metrics **Free**; OS memory/disk/net are **Custom Metrics** (~$0.30/metric) |
| **Amazon RDS PostgreSQL** | `CPUUtilization` | `FreeableMemory` | `NetworkReceiveThroughput` | `FreeStorageSpace` / `ReadIOPS` | Native Hypervisor Telemetry | **100% Free** (Standard 1-min / 5-min intervals) |
| **ElastiCache (Valkey / Redis)** | `CPUUtilization` / `EngineCPU` | `BytesUsedForCache` | `NetworkBytesIn` / `NetworkBytesOut` | In-memory eviction tracking | Native Engine Telemetry | **100% Free** (Emitted natively into CloudWatch) |
| **Amazon EFS File System** | N/A (Serverless) | N/A (Serverless) | `DataReadIOBytes` / `DataWriteIOBytes` | `StorageBytes` / `PercentIOLimit` | Native EFS Controller | **100% Free** (Standard metrics) |
| **Application Load Balancers** | N/A (L7 Layer) | N/A (L7 Layer) | `ProcessedBytes` / `ActiveConnectionCount` | N/A (HTTP target metrics) | Native Ingress Telemetry | **100% Free** (Standard metrics) |

---

## 6. Unified CloudWatch Agent Configuration

Deploying `/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json` enables guest OS memory, disk, and network collection without proprietary agent taxation:

{% raw %}
```json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "cwagent"
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
          "*"
        ]
      }
    }
  }
}
```
{% endraw %}

### Financial Sizing: Custom Infrastructure Metrics

* **AWS Pricing:** First 10 custom metrics per account are **Free Tier**; thereafter, **$0.30 USD per metric/month** (verified against AWS pricing for `ap-southeast-5`).
* **Standard Memory/Disk Baseline (4 custom metrics/node):** `mem_used_percent`, `mem_available`, `disk_used_percent`, `disk_free`. For a 15-node cluster = 60 time series (50 billed after 10 free) = **$15.00 USD / month (~RM 67.50 MYR)**.
* **Full Memory/Disk/Network Baseline (8 custom metrics/node):** Includes all 8 enabled measurements in the JSON profile above (`mem_used_percent`, `mem_available`, `disk_used_percent`, `disk_free`, `bytes_sent`, `bytes_recv`, `drop_in`, `drop_out`). For a 15-node cluster = 120 time series (110 billed after 10 free) = **$33.00 USD / month (~RM 148.50 MYR)**.

---

## 7. High-Volume / Payment-Critical Cost Risk & TPS Crossover Analysis

For high-throughput, payment-critical microservices, sustained transaction rates and audit requirements impact APM consumption costs. Because CloudWatch APM scales with signal and trace volume while Dynatrace scales with host RAM, high-throughput endpoints require explicit trace sampling controls.

| Sustained Throughput | Monthly Signals | Trace Ingestion | APM Monthly Cost (USD) | APM Monthly Cost (MYR @ 4.50) |
| :---: | :---: | :---: | :---: | :---: |
| **1,000 req/min (~17 TPS)** | 131,000,000 | ~246 GB | **$259.79** | **RM 1,169.06** |
| **5,000 req/min (~83 TPS)** | 657,000,000 | ~1.23 TB | **$998.92** | **RM 4,495.14** |
| **10,000 req/min (~166 TPS)** | 1,314,000,000 | ~2.46 TB | **$1,781.51** | **RM 8,016.80** |
| **25,000 req/min (~416 TPS)** | 3,285,000,000 | ~6.16 TB | **$3,666.29** | **RM 16,498.31** |

### Key Finding & Mitigation Strategy

At roughly **10,000 req/min sustained**, CloudWatch APM trace ingestion alone exceeds the fixed host-unit Dynatrace cost for a small cluster. To prevent cost inversion:

1. **Intelligent Trace Sampling:** Do not run payment services at 100% trace sampling. Use low steady-state sampling (e.g., 5%), with 100% capture reserved strictly for errors and HTTP 5xx responses.
2. **Audit Trail Offloading:** Satisfy audit and compliance mandates by writing structured access records to Amazon S3 or CloudWatch Logs ($0.50/GB ingestion), keeping Application Signals in "golden metrics only" mode for routine transactions.
3. **Pilot Validation:** Leverage the 3-month free trial (up to 100 GB trace ingestion / 100M signals) to measure exact span volumes prior to production commit.

---

## 8. Total Consolidated Observability Stack (15-Node Cluster)

Combining client-side RUM, Application Signals APM, host metrics, and operational alarms yields a complete, unified post-trial steady-state AWS Observability budget:

| Observability Layer | Scope / Function | Monthly Cost (USD) | Monthly Cost (MYR @ 4.50) |
| :--- | :--- | :---: | :---: |
| **CloudWatch RUM** | Client-side Web Vitals & JS errors (250k–1M sessions) | $50.00 – $200.00 | RM 225.00 – RM 900.00 |
| **Application Signals (APM)** | OTel traces, Application Map, SLO tracking | $11.00 – $44.00 | RM 49.50 – RM 198.00 |
| **Host Metrics (Agent)** | EC2 OS Memory, Disk & Net metrics (15 instances @ 4–8 metrics = 60–120 series) | $15.00 – $33.00 | RM 67.50 – RM 148.50 |
| **Native AWS Metrics** | RDS PostgreSQL, ElastiCache Valkey, EFS, ALB | **$0.00** (Free) | **RM 0.00** |
| **Alarms & Dashboards** | Operational alerts & composite status screens | $5.00 | RM 22.50 |
| **Total CloudWatch Suite** | **Full-Stack AWS-Native Observability Envelope** | **~$81.00 – $282.00** | **~RM 364.50 – RM 1,269.00** |
| **Legacy Dynatrace OneAgent** | **Proprietary Host Units + DEM Packs (15 hosts @ $58–$74/HU/mo)** | **~$870.00 – $1,110.00+** | **~RM 3,915.00 – RM 4,995.00+** |

**Net Strategic Impact:** Transitioning to native CloudWatch observability delivers full APM and end-user visibility inside **AWS Malaysia (`ap-southeast-5`)** with an immediate recurring operational saving of **~$588.00 to $1,029.00 USD per month (~RM 2,646.00 to RM 4,630.50 MYR per month)**.

---

## 9. Implementation Roadmap & Migration Plan

```text
Phase 1: Agent, RUM & Trace Correlation Provisioning (Week 1)
  ├── Deploy Unified CloudWatch Agent via Ansible / EC2 User Data across 15 nodes.
  ├── Provision CloudWatch RUM App Monitor in ap-southeast-5 with enableXRay: true and addXRayTraceIdHeader: true.
  ├── Configure HTTP telemetry and downstream CORS headers allowing X-Amzn-Trace-Id.
  ├── Enable AWS Distro for OpenTelemetry (ADOT) / AWS X-Ray SDK instrumentation on backend compute nodes.
  └── Execute trace verification test to confirm front-end to backend end-to-end trace correlation.

Phase 2: Golden Signals & Service Map Validation (Week 2)
  ├── Verify Application Map generation and trace context propagation across ALB.
  ├── Establish Service Level Objectives (SLOs) and burn-rate composite alarms.
  └── Conduct 3-month free trial pilot on canary workloads to validate trace sampling.

Phase 3: Dynatrace Decommissioning & Sign-Off (Week 3 - 4)
  ├── Remove Dynatrace OneAgent packages from EC2 launch templates and golden AMIs.
  ├── Terminate Dynatrace host unit subscriptions and reclaim licensing fees.
  └── Present verified CloudWatch dashboard telemetry to the Board.
```

---

## 10. Public Information & Data Anonymization Statement

> **Public Information & Educational Notice:** All IP addresses, hostnames, domain names, account identifiers, and financial figures referenced in this document are public, anonymized, or illustrative reference data. This document is authored strictly for public educational purposes, open-source architectural learning, and demonstration of AWS-native FinOps observability migration.
