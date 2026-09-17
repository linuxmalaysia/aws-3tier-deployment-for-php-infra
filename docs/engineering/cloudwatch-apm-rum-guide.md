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

Operating natively within the **AWS Malaysia (`ap-southeast-5`)** data boundary for explicitly configured telemetry resources, this consolidated stack closes the final functional gap versus Dynatrace—distributed tracing, service topology mapping, end-user experience monitoring, and Service Level Objectives (SLOs)—using an open-standard, OpenTelemetry (OTel)-based architecture with no per-host agent licensing.

For a representative 15-node production cluster, the fully consolidated steady-state CloudWatch observability stack (RUM, APM, host metrics with 4 to 8 custom metrics/node, native service metrics, alarms/dashboards) is estimated at **$81.00 – $282.00 USD per month (~RM 364.50 – RM 1,269.00 MYR)** post-trial, based on a reproducible model (250k–1M web sessions with 10–20 RUM events/session, 5M–20M Application Signals, 10–40 GB trace ingestion, 15 EC2 instances with 4–8 custom metrics/node, and composite operational alarms). Compared to legacy Dynatrace Full-Stack Monitoring estimated at **$870.00 – $1,110.00+ USD per month (~RM 3,915.00 – RM 4,995.00+ MYR)** for 15 host units ($58–$74/host unit/month), this migration yields potential recurring operational savings of **~$588.00 – $1,029.00 USD per month (~RM 2,646.00 – RM 4,630.50 MYR per month)** while maintaining local telemetry residency and reclaiming host compute capacity.

---

## 1. Why Change: Limitations of the Current Dynatrace Model

Maintaining third-party enterprise APM agents (Dynatrace OneAgent) inside AWS infrastructure introduces four major operational and financial liabilities:

1. **Proprietary OneAgent Lock-In:** Kernel-level bytecode instrumentation and deep OS hooks are a recurring source of compatibility issues during OS patching (glibc/kernel version drift) on Linux baselines.
2. **Fixed Host-Unit Licensing:** Dynatrace Full-Stack Monitoring is billed per 8 GiB RAM "host unit," so cost scales strictly with host RAM even when utilization remains low.
3. **Compute Agent Overhead:** Third-party agents typically carry materially higher RAM (~200–400 MB) and CPU overhead (~2–5%) than lightweight OpenTelemetry auto-instrumentation (~15–30 MB RAM, <0.2% CPU in standard Linux user-space benchmarking), creating a continuous resource tax across every monitored EC2 instance.
4. **Data Sovereignty & Egress:** Exporting telemetry outside the local AWS region creates unnecessary egress and external dependencies. Native CloudWatch tools retain explicitly configured metrics, traces, and logs inside **AWS Malaysia (`ap-southeast-5`)**.

---

## 2. Overview of CloudWatch, CloudWatch APM (Application Signals) & CloudWatch RUM

Amazon CloudWatch provides a native, unified telemetry platform spanning server-side infrastructure, application-level APM, and client-side end-user monitoring.

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             END-USER DEVICE (Browser)                            │
│  CloudWatch RUM (aws-rum-web) -> Core Web Vitals, JS Errors, Client Trace Header │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ W3C traceparent OR AWS X-Ray Header
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LOAD BALANCER (ALB)                          │
│  Native CloudWatch Metrics -> Request Counts, HTTP 4xx/5xx, Target Group Latency │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ Distributed HTTP Trace Context
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   COMPUTE LAYER (EC2 / Graviton / Container)                     │
│  - CloudWatch Application Signals (OTel PHP zero-code instrumentation)            │
│  - CloudWatch Agent / Collector -> Telemetry Export (Spans, Traces, SLOs, OS)    │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ AWS SDK / Service Telemetry
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     DATA & CACHE TIER (Amazon RDS & Valkey)                      │
│  Native CloudWatch Metrics -> Storage, Read/Write IOPS, Engine CPU, Memory       │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Amazon CloudWatch (Core Platform)
* **Description:** Amazon CloudWatch is AWS's native monitoring, logging, and observability service. It collects system metrics, application log files, and operational events across all AWS services.
* **Core Functionality:** Provides centralized alarm orchestration (CloudWatch Alarms), interactive operational dashboards, metric math, Log Insights querying, and automated event triggers via Amazon EventBridge.
* **Infrastructure Coverage:** Natively integrates with compute (EC2), load balancers (ALB/NLB), relational databases (Amazon RDS PostgreSQL/MariaDB), in-memory caching (ElastiCache Valkey/Redis), and serverless storage (Amazon EFS/S3) without requiring additional agent installation for standard metrics.

### 2.2 CloudWatch Application Signals (APM)
* **Description:** CloudWatch Application Signals is AWS's native, open-standard Application Performance Monitoring (APM) solution. Built on OpenTelemetry (OTel), it automatically discovers and monitors application performance, service topologies, and transaction dependencies.
* **Core Capabilities:**
  * **Automated Service Map:** Dynamically maps microservice calls, database queries, external API calls, and message queues.
  * **Golden Signals:** Automatically records request rates, latency histograms (P50, P90, P95, P99), fault rates, and error rates without manual code modification.
  * **Service Level Objectives (SLOs):** Allows teams to define latency and availability SLOs with automated error-budget burn-rate monitoring and alerting.
  * **Distributed Tracing Integration:** Supported via standard OpenTelemetry PHP zero-code instrumentation (with Transaction Search enabled), using the CloudWatch Agent / OTel Collector purely as the telemetry export mechanism (no ADOT PHP SDK is required or available).

### 2.3 CloudWatch Real User Monitoring (RUM)
* **Description:** CloudWatch RUM provides client-side Real User Monitoring by gathering real-time telemetry directly from end-user browsers and client devices.
* **Core Capabilities:**
  * **Core Web Vitals:** Tracks Google-standard web performance benchmarks including Largest Contentful Paint (LCP), Cumulative Layout Shift (CLS), and Interaction to Next Paint (INP).
  * **Client Error Tracking:** Captures unhandled JavaScript exceptions and HTTP network failure status codes (4xx/5xx) across web sessions.
  * **Session & Demographic Analytics:** Categorizes user experience by geographic region, browser version, operating system, and connection speed.
  * **Client-to-Backend Trace Correlation:** Supported in alternative propagation modes via `aws-rum-web`: setting `addXRayTraceIdHeader: true` injects `X-Amzn-Trace-Id`, whereas setting `enableW3CTraceId: true` injects the W3C `traceparent` header. Downstream Application Load Balancers and PHP frameworks must explicitly allow the selected header in CORS configuration.

---

## 3. Architectural Comparison Matrix: CloudWatch APM + RUM vs. Dynatrace

The following comparison tables evaluate CloudWatch (APM + RUM + Host Agent) against legacy Dynatrace OneAgent across technical, operational, architectural, and financial dimensions.

### Table 3.1: Architecture, Footprint, and Technical Standards

| Capability / Dimension | Legacy Dynatrace OneAgent | CloudWatch APM (Application Signals) + RUM Suite | Architectural Advantage |
| :--- | :--- | :--- | :--- |
| **Instrumentation Standard** | Proprietary Bytecode Injection / Custom Agent | OpenTelemetry (OTel) PHP Zero-Code Instrumentation & CloudWatch Agent | Vendor-neutral open standard; zero proprietary agent lock-in |
| **Host Memory Overhead** | ~200 MB – 400 MB RAM per instance | ~15 MB – 30 MB RAM (OTel user-space agent / CWAgent in 64-bit Linux baselines) | Reclaims host RAM for application compute capacity |
| **Host CPU Overhead** | 2.0% – 5.0% CPU continuous consumption | < 0.2% CPU utilization (measured in standard user-space daemon baseline tests) | Minimal CPU impact; increases instance target capacity |
| **Kernel / OS Compatibility** | Deep kernel hooks; sensitive to OS / glibc updates | User-space agent & native hypervisor metrics within supported OS platform matrix | Supported OS user-space execution reduces kernel version drift risks |
| **Distributed Tracing Protocol** | Dynatrace PurePath (Proprietary) | W3C `traceparent` (via `enableW3CTraceId`) or AWS X-Ray `X-Amzn-Trace-Id` | Standardized, configurable header propagation across microservices |
| **Client-Side JS SDK** | Dynatrace RUM Agent (`ruxitagentjs`) | Open-source `aws-rum-web` JS snippet | Lightweight, customizable, zero third-party domain reliance |

### Table 3.2: Observability Features, Capabilities, and Data Governance

| Observability Feature | Legacy Dynatrace OneAgent | CloudWatch APM + RUM Suite | Operational & Strategic Benefit |
| :--- | :--- | :--- | :--- |
| **Service Topology Mapping** | Smartscape Dependency Graph | CloudWatch Application Map | Auto-synthesizes microservice & database call graphs in real time |
| **SLO & Burn-Rate Alerting** | Service Level Objectives / Davis AI | Native Golden Signal SLOs & Burn-Rate Alarms | Declarative P95/P99 latency & fault budget tracking |
| **End-User Performance** | Dynatrace DEM (Digital Exp. Monitoring) | CloudWatch RUM (Core Web Vitals) | Real-time LCP, CLS, and INP tracking per client browser |
| **Client Exception Tracking** | Dynatrace JavaScript Error Analysis | CloudWatch RUM Error Stack Analytics | Grouped JS errors, HTTP 4xx/5xx failures, and client OS breakdown |
| **Data Boundary & Sovereignty** | Data exported to Dynatrace SaaS / External POPS | Explicitly configured resources stay in **AWS Malaysia (`ap-southeast-5`)** | Supports regional data residency; requires data classification & compliance verification |
| **Network Egress Cost** | Egress charges for telemetry sent outside AWS | Avoids external egress; regional AWS service endpoints route within AWS network | Eliminates third-party internet egress charges for telemetry transport |

### Table 3.3: Financial, Pricing & Commercial Models

| Commercial Dimension | Legacy Dynatrace OneAgent | CloudWatch APM + RUM Suite | Financial Impact |
| :--- | :--- | :--- | :--- |
| **Pricing Structure** | Fixed Host Unit (8 GiB RAM base unit) | Metered Usage (Signals @ $1.50/1M, Traces @ $0.35/GB, Custom Metrics @ $0.30) | Pay strictly for actual telemetry ingested; no host-RAM tax |
| **Host Unit Cost Baseline** | $58.00 – $74.00+ USD / Host Unit / Month | Billed by signals & traces (Host OS metrics @ $0.30/metric/month) | Decouples APM licensing from EC2 instance RAM sizing |
| **15-Host Cluster Monthly Cost** | **$870.00 – $1,110.00+ USD** (~RM 3,915 – RM 4,995 MYR) | **$81.00 – $282.00 USD** (~RM 364.50 – RM 1,269 MYR) | **70% to 90% direct monthly cost reduction** based on reproducible workload model |
| **Evaluation Trial Offer** | 15-day free trial | **Metrics-only:** 3-mo / 100M signals trial. **Tracing:** 100 GB & 1M span trial | Extended zero-cost validation window for production workloads |

---

## 4. Comprehensive Catalog of Available Reports & Strategic Benefits

Adopting the Amazon CloudWatch Observability Suite provides engineering, operations, and executive leadership with seven distinct operational and financial reports:

### Report 1: Service Health & Dependency Map Report
* **Telemetry Source:** CloudWatch Application Signals (APM) & OpenTelemetry trace spans.
* **Report Contents:**
  * Real-time topological graph mapping all microservices, API endpoints, Amazon RDS database instances, ElastiCache nodes, and external third-party HTTP endpoints.
  * Node-by-node health statuses, call rates (req/sec), fault percentages, and average latency overlays.
* **Benefits:** Reduces Mean Time to Identification (MTTI) for service degradation from hours to seconds by visually highlighting exact bottleneck nodes in distributed call chains.

### Report 2: Service Level Objective (SLO) & Error Budget Burn-Rate Report
* **Telemetry Source:** CloudWatch Application Signals SLO Engine.
* **Report Contents:**
  * P90, P95, and P99 latency target compliance reports against defined Service Level Targets (e.g., 99.5% requests < 200ms).
  * Error budget remaining percentages and burn-rate acceleration metrics over 1-hour, 6-hour, and 24-hour evaluation windows.
* **Benefits:** Prevents unexpected SLA breaches by triggering proactive automated burn-rate alerts before error budgets are fully exhausted.

### Report 3: Distributed Trace Waterfall & Transaction Latency Report
* **Telemetry Source:** AWS X-Ray & CloudWatch Application Signals Trace Index.
* **Report Contents:**
  * Detailed execution timeline (waterfall chart) showing segment duration across browser request, ALB, CodeIgniter application execution, database SQL execution, and external API calls.
  * SQL query statement breakdown and database connection wait-time analysis.
* **Benefits:** Identifies slow database queries, N+1 query patterns, and blocking downstream service calls without adding log overhead.

### Report 4: Real User Performance & Core Web Vitals Report
* **Telemetry Source:** CloudWatch Real User Monitoring (RUM) JS SDK.
* **Report Contents:**
  * Aggregate and distribution reports for Google Core Web Vitals: **Largest Contentful Paint (LCP)**, **Cumulative Layout Shift (CLS)**, and **Interaction to Next Paint (INP)**.
  * Performance breakdowns by end-user geographic region (e.g., Kuala Lumpur, Penang, Johor), browser family (Chrome, Safari, Firefox, Edge), and device type (Mobile vs. Desktop).
* **Benefits:** Directly correlates front-end user experience with conversion performance and ensures client-side web application responsiveness across Malaysia's mobile networks.

### Report 5: Client-Side Errors & JavaScript Exception Analytics Report
* **Telemetry Source:** CloudWatch RUM Error Ingestion Engine.
* **Report Contents:**
  * Grouped stack traces for unhandled JavaScript exceptions, HTTP 4xx client errors, and 5xx server gateway errors.
  * Impacted session percentages, affected URL path breakdown, and device/browser environment filters.
* **Benefits:** Enables front-end developers to isolate and patch client-side JavaScript bugs impacting specific user browser combinations in production.

### Report 6: Infrastructure Resource Utilization & Capacity Planning Report
* **Telemetry Source:** Unified CloudWatch Agent (`amazon-cloudwatch-agent`) & Native AWS Service Metrics.
* **Report Contents:**
  * Guest OS CPU utilization, memory usage (`mem_used_percent`), disk space consumed (`disk_used_percent`), and network throughput (`bytes_sent` / `bytes_recv`).
  * Database storage capacity, freeable memory, buffer cache hit ratios (Amazon RDS), and Valkey/Redis cache eviction rates.
* **Benefits:** Provides exact data for EC2 Graviton rightsizing, Auto Scaling group threshold tuning, and proactive storage expansion before disk saturation.

### Report 7: FinOps Observability Cost & Telemetry Usage Report
* **Telemetry Source:** AWS Billing & CloudWatch Cost Explorer Metrics.
* **Report Contents:**
  * Ingested signal volume, trace storage size (GB), RUM event counts, and custom metric time-series billing totals.
  * Per-service telemetry cost attribution and high-volume endpoint identification.
* **Benefits:** Gives FinOps teams granular visibility into observability spend, ensuring telemetry costs remain aligned with application throughput.

---

## 5. Supporting Tools, Instrumentation Frameworks & PDF Generation Workflow

To operationalize the CloudWatch observability platform and publish architecture artifacts across the enterprise, the following supporting tools and automation pipelines are integrated into the repository:

### 5.1 Supporting Tools & Agent Ecosystem

1. **Unified CloudWatch Agent (`amazon-cloudwatch-agent`):**
   * **Role:** Lightweight RPM/DEB system package deployed on EC2 instances via Ansible playbooks and EC2 User Data (`scripts/user_data.sh`).
   * **Function:** Collects guest OS-level memory utilization (`mem_used_percent`), disk space (`disk_used_percent`), and network interface statistics without requiring third-party kernel extensions.

2. **OpenTelemetry PHP Zero-Code Instrumentation & CloudWatch Agent / Collector:**
   * **Role:** Standard OpenTelemetry PHP zero-code extension using the CloudWatch Agent / Collector as the telemetry exporter (no ADOT PHP SDK is required or available).
   * **Function:** Intercepts inbound and outbound HTTP requests, database PDO queries, and Valkey cache commands to generate standard OTel spans and propagate standard trace headers (`traceparent` or `X-Amzn-Trace-Id`).

3. **CloudWatch RUM Web Client (`aws-rum-web`):**
   * **Role:** Lightweight, open-source JavaScript web client embedded into application layout headers (`docs/_layouts/default.html` or PHP views).
   * **Function:** Collects client-side Core Web Vitals, unhandled JavaScript exceptions, and HTTP status code errors, propagating trace IDs (`X-Amzn-Trace-Id` or `traceparent`) to backend load balancers.

4. **Sitemap & Document Generation Engine (`scripts/generate_sitemaps.py` & `scripts/prepare_docs.py`):**
   * **Role:** Python automation tools maintained in the repository.
   * **Function:** Prepares front-matter metadata, normalizes ISO timestamps, and builds XML/TXT sitemaps for documentation discovery.

### 5.2 Automated PDF Document Export Workflow

To produce standardized A4 executive PDF documentation for offline board review and archiving, the repository maintains an automated CI/CD workflow (`.github/workflows/pdf-generation.yml`):

* **Pipeline Automation:** Built on GitHub Actions running Node.js 22 LTS and Puppeteer (`misaelnieto/web_to_pdf_action@v0.3.1`).
* **Generation Process:** Connects to the published web page URL, renders the complete styling layout, and generates an A4 PDF document compiled at `./docs/assets/output.pdf`.
* **Artifact Upload:** Uploads the compiled PDF asset (`output.pdf`) as the `page-pdf` build artifact for review and distribution.

---

## 6. How CloudWatch Application Signals (APM) Is Priced

CloudWatch Application Signals measures application health through two metered, tiered billing dimensions (rates verified against official AWS CloudWatch pricing for `ap-southeast-5`, Sept 2026):

* **Golden Metrics (Signals):** **$1.50 USD per 1 million signals** for the first 100 million signals/month; $0.75 per 1M up to 1B; $0.30 per 1M beyond 1B. Signals include inbound HTTP request counts, outbound dependency calls (RDS, ElastiCache, HTTP APIs), error counts, latency histograms, and SLO-generated evaluation signals.
* **Transaction Search / Trace Ingestion:** **$0.35 USD per GB** for the first 10 TB/month; $0.20 per GB up to 30 TB; $0.15 per GB beyond 30 TB.
* **Evaluation Trial Window:** Billed separately for metrics-only vs. transaction tracing. New accounts receive a 3-month free trial for Golden Metrics (up to 100 million signals/month). Full transaction search tracing offers a 100 GB trace ingestion & 1 million indexed-span trial allocation.

### Monthly Workload Projections (Application Signals — Post-Trial Steady State)

| Workload Profile | Signals / Month | Trace Ingestion | Monthly Cost (USD) | Monthly Cost (MYR @ 4.50) |
| :---: | :---: | :---: | :---: | :---: |
| **Baseline Profile** | 5,000,000 | 10 GB | **$11.00** | **RM 49.50** |
| **Moderate Production** | 20,000,000 | 40 GB | **$44.00** | **RM 198.00** |
| **High-Volume Tier** | 80,000,000 | 150 GB | **$172.50** | **RM 776.25** |

*(Calculation: $20\text{M signals} \times \frac{\$1.50}{1\text{M}} = \$30.00$; $40\text{ GB} \times \$0.35/\text{GB} = \$14.00$; Total = **$44.00 USD/month** steady state).*

---

## 7. CloudWatch Real User Monitoring (RUM) Client-Side Architecture

CloudWatch RUM provides end-user experience monitoring by embedding a lightweight, open-source JavaScript web client (`aws-rum-web`) into front-end web templates.

### 7.1 RUM Capabilities & Trace Integration

* **Core Web Vitals Telemetry:** Directly records Largest Contentful Paint (LCP), Cumulative Layout Shift (CLS), and Interaction to Next Paint (INP) across end-user devices in Malaysia.
* **JavaScript & HTTP Error Tracking:** Automatically aggregates unhandled client JavaScript exceptions and HTTP network failure status codes (4xx/5xx).
* **Distributed Trace Correlation:** Injects standard trace headers into client HTTP requests by configuring either `addXRayTraceIdHeader: true` (which injects `X-Amzn-Trace-Id`) or `enableW3CTraceId: true` (which injects the W3C `traceparent` header). Downstream Application Load Balancers and PHP web frameworks must explicitly allow the selected header in CORS headers. Backend instrumentation (e.g., OpenTelemetry PHP zero-code instrumentation and CloudWatch Agent) running on compute nodes is required to record backend trace segments and link them to the client trace ID.
* **Client Privacy & Governance Controls:** Data residency in `ap-southeast-5` supports regional hosting requirements, but does not inherently guarantee regulatory or privacy compliance. Compliance requires data classification, data minimization, consent management (`allowCookies: false`), session sampling rate tuning (`sessionSampleRate`), payload filtering (`recordResourceUrl: false`), and formal privacy sign-off prior to deployment.

### 7.2 RUM Cost Model

* **Unit Pricing:** **$1.00 USD per 100,000 data events** ($0.00001 per event, verified against AWS pricing, Sept 2026).
* **Trial Allocation:** Includes a one-time, first-time per-account evaluation trial of **1,000,000 events** (for the first active month); thereafter, standard metering ($1.00 / 100k events) applies across steady-state workloads.
* **Event Volume:** Standard page navigation produces approximately **10 to 20 events** per complete user session (Page Load, Navigation Timing, Web Vitals, Errors). Cost tables below reflect post-trial steady-state pricing.

| Monthly Sessions | Est. Events (@20/session) | Steady-State Monthly Cost (USD) | Steady-State Monthly Cost (MYR @ 4.50) |
| :---: | :---: | :---: | :---: |
| **250,000 sessions** | 5,000,000 events | **$50.00** ($40.00 in 1st trial mo) | **RM 225.00** (RM 180.00 in trial mo) |
| **1,000,000 sessions** | 20,000,000 events | **$200.00** ($190.00 in 1st trial mo) | **RM 900.00** (RM 855.00 in trial mo) |

---

## 8. Capability & Infrastructure Telemetry Matrix

CloudWatch natively captures **CPU, Memory, Network I/O, and Disk Space** telemetry across all application tiers. Managed database and caching engines emit these streams natively at zero extra cost, whereas EC2 guest instances utilize the open-source **Unified CloudWatch Agent (`amazon-cloudwatch-agent`)** for internal guest OS memory, disk, and network metrics.

| Infrastructure Tier | CPU Telemetry | Memory Telemetry | Network I/O Telemetry | Disk Space / IOPS | Implementation Mechanism | Metric Billing Category |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EC2 Instances** | `CPUUtilization` | `mem_used_percent` | `NetworkIn` / `NetworkOut` | `disk_used_percent` | Unified CloudWatch Agent (RPM/DEB) | Basic metrics **Free**; OS memory/disk/net are **Custom Metrics** (~$0.30/metric) |
| **Amazon RDS PostgreSQL** | `CPUUtilization` | `FreeableMemory` | `NetworkReceiveThroughput` | `FreeStorageSpace` / `ReadIOPS` | Native Hypervisor Telemetry | **100% Free** (Standard 1-min / 5-min intervals) |
| **ElastiCache (Valkey / Redis)** | `CPUUtilization` / `EngineCPU` | `BytesUsedForCache` | `NetworkBytesIn` / `NetworkBytesOut` | In-memory eviction tracking | Native Engine Telemetry | **100% Free** (Emitted natively into CloudWatch) |
| **Amazon EFS File System** | N/A (Serverless) | N/A (Serverless) | `DataReadIOBytes` / `DataWriteIOBytes` | `StorageBytes` / `PercentIOLimit` | Native EFS Controller | **100% Free** (Standard metrics) |
| **Application Load Balancers** | N/A (L7 Layer) | N/A (L7 Layer) | `ProcessedBytes` / `ActiveConnectionCount` | N/A (HTTP target metrics) | Native Ingress Telemetry | **100% Free** (Standard metrics) |

---

## 9. Unified CloudWatch Agent Configuration

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

## 10. High-Volume / Payment-Critical Cost Risk & TPS Crossover Analysis

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
3. **Pilot Validation:** Leverage trial allocations (up to 100 GB trace ingestion / 100M signals) to measure exact span volumes prior to production commit.

---

## 11. Total Consolidated Observability Stack (15-Node Cluster Reproducible Model)

Combining client-side RUM, Application Signals APM, host metrics, and operational alarms yields a complete, unified post-trial steady-state AWS Observability budget based on the following input parameters:

* **Region & Rates:** AWS Malaysia (`ap-southeast-5`) list rates (RUM $1.00/100k events, Signals $1.50/1M, Traces $0.35/GB, Custom Metrics $0.30/metric, Alarms $0.10–$0.50/alarm).
* **Workload Drivers:** 250k–1M web sessions (10–20 RUM events/session = 5M–20M events = $50–$200); 5M–20M Application Signals ($7.50–$30) + 10–40 GB trace ingestion ($3.50–$14) = $11–$44; 15 EC2 hosts with 4–8 custom metrics/node (60–120 series, 10 free = 50–110 billed = $15–$33); 10 operational alarms = $5.00.

| Observability Layer | Workload Driver & Rate Inputs | Monthly Cost (USD) | Monthly Cost (MYR @ 4.50) |
| :--- | :--- | :---: | :---: |
| **CloudWatch RUM** | 250k–1M sessions (5M–20M events @ $1.00/100k) | $50.00 – $200.00 | RM 225.00 – RM 900.00 |
| **Application Signals (APM)** | 5M–20M signals ($1.50/1M) + 10–40 GB traces ($0.35/GB) | $11.00 – $44.00 | RM 49.50 – RM 198.00 |
| **Host Metrics (Agent)** | 15 EC2 hosts @ 4–8 metrics = 60–120 series (50–110 billed @ $0.30) | $15.00 – $33.00 | RM 67.50 – RM 148.50 |
| **Native AWS Metrics** | RDS PostgreSQL, ElastiCache Valkey, EFS, ALB | **$0.00** (Free) | **RM 0.00** |
| **Alarms & Dashboards** | Operational alerts & composite status screens | $5.00 | RM 22.50 |
| **Total CloudWatch Suite** | **Full-Stack AWS-Native Observability Envelope** | **~$81.00 – $282.00** | **~RM 364.50 – RM 1,269.00** |
| **Legacy Dynatrace OneAgent** | **15 Host Units @ $58–$74/HU/month** | **~$870.00 – $1,110.00+** | **~RM 3,915.00 – RM 4,995.00+** |

**Net Strategic Impact:** Transitioning to native CloudWatch observability delivers full APM and end-user visibility inside **AWS Malaysia (`ap-southeast-5`)** with an immediate recurring operational saving of **~$588.00 to $1,029.00 USD per month (~RM 2,646.00 to RM 4,630.50 MYR per month)**.

---

## 12. Implementation Roadmap & Migration Plan

```text
Phase 1: Agent, RUM & Trace Correlation Provisioning (Week 1)
  ├── Deploy Unified CloudWatch Agent via Ansible / EC2 User Data across 15 nodes.
  ├── Provision CloudWatch RUM App Monitor in ap-southeast-5 with enableW3CTraceId: true or addXRayTraceIdHeader: true.
  ├── Configure HTTP telemetry and downstream CORS headers allowing the selected header (traceparent or X-Amzn-Trace-Id).
  ├── Enable OpenTelemetry PHP zero-code instrumentation and CloudWatch Agent exporter on backend compute nodes.
  └── Execute trace verification test to confirm front-end to backend end-to-end trace correlation.

Phase 2: Golden Signals & Service Map Validation (Week 2)
  ├── Verify Application Map generation and trace context propagation across ALB.
  ├── Establish Service Level Objectives (SLOs) and burn-rate composite alarms.
  └── Conduct free trial pilot on canary workloads to validate trace sampling.

Phase 3: Dynatrace Decommissioning & Sign-Off (Week 3 - 4)
  ├── Remove Dynatrace OneAgent packages from EC2 launch templates and golden AMIs.
  ├── Terminate Dynatrace host unit subscriptions and reclaim licensing fees.
  └── Present verified CloudWatch dashboard telemetry to the Board.
```

---

## 13. Public Information & Data Anonymization Statement

> **Public Information & Educational Notice:** All IP addresses, hostnames, domain names, account identifiers, and financial figures referenced in this document are public, anonymized, or illustrative reference data. This document is authored strictly for public educational purposes, open-source architectural learning, and demonstration of AWS-native FinOps observability migration.
