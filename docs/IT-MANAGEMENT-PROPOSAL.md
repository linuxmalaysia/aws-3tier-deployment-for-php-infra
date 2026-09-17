---
layout: default
okf_version: "0.1"
type: "Executive Proposal"
title: "IT Management Proposal: Enterprise Data & Infrastructure Modernisation (Historical to AI-Ready)"
timestamp: "2026-08-11T12:00:00+08:00"
topics: ["it-proposal", "aws", "mcp-ready", "podman", "ai-infrastructure"]
---

**[EXECUTIVE STRATEGIC]** **[DEVOPS EXECUTION]** **[AI INFRASTRUCTURE]**

# Executive Proposal: Enterprise Data & Infrastructure Modernisation

📄 **[Download Full Proposal PDF (A4 Document)](assets/IT-MANAGEMENT-PROPOSAL.pdf)**

**Document Version:** 2.0
**Author:** Lead Systems Architect & AI Infrastructure Working Group
**Target Audience:** IT Management, Executive Steering Committee & Enterprise Architects
**Infrastructure Scope:** `aws-3tier-deployment-for-php-infra` & `bda-ai-infra`

---

## Executive Summary & Vision

This proposal outlines the comprehensive, end-to-end modernisation roadmap for our enterprise IT data and cloud infrastructure. It presents the historical evolution, current cloud-native baseline, and strategic future-proof target state for the organisation's core applications and Big Data Analytics & AI Infrastructure (`bda-ai-infra`).

We are transitioning from legacy monolithic virtual machines and static, proprietary visualization tools (Tableau) to an **API-First, Open-Source, and Model Context Protocol (MCP)-Ready** ecosystem running on AWS Graviton (`ap-southeast-5`) and containerised rootless Podman pods.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      EVOLUTION OF IT INFRASTRUCTURE                    │
├───────────────────┬───────────────────────────┬────────────────────────┤
│ Historical State  │ Current Baseline          │ Future-Proof Target    │
│ (Legacy Monolith) │ (AWS 3-Tier OpenTofu)     │ (API & MCP AI Ecosystem)│
├───────────────────┼───────────────────────────┼────────────────────────┤
│ Single-node VM    │ Multi-AZ OpenTofu IaC     │ Rootless Podman Pods   │
│ Monolithic PHP    │ CodeIgniter 4 + PHP-FPM   │ Microservices + Fusio  │
│ Tableau Reports   │ AWS RDS Multi-AZ          │ Patroni PG18 + pgvector│
│ Manual Ops        │ ASIMP, Wazuh & CloudWatch │ Native LLM & MCP Tools │
└───────────────────┴───────────────────────────┴────────────────────────┘
```

---

## 1. Comprehensive Historical Context & Operational Evolution

### 1.1 Phase 0: Historical Legacy Architecture
Historically, operations relied on standalone virtual machines running monolithic web applications alongside local database instances and proprietary BI dashboards (Tableau).

* **Operational Bottlenecks:** Single points of failure (SPOF), manual operating system upgrades, unencrypted local session storage, and lack of automated disaster recovery.
* **Licensing Liabilities:** High recurring per-user and per-core Tableau licensing fees, locking critical business calculations inside binary `.twb`/`.twbx` workbooks.
* **Data Silos:** Reporting was unidirectional. External systems, IoT sensors, and automated pipelines could not interact programmatically with enterprise business data without manual exports.

### 1.2 Phase 1: Current Production Baseline (AWS 3-Tier OpenTofu Stack)
To eliminate legacy single-node risks, the engineering team successfully migrated core web workloads to a hardened, cloud-native **AWS 3-Tier Architecture in the Asia Pacific (Malaysia) region (`ap-southeast-5`)**.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                 CURRENT AWS 3-TIER PRODUCTION BASELINE                 │
│                                                                        │
│   PUBLIC INGRESS TIER                                                  │
│   [ Route 53 DNS ] ──► [ AWS WAFv2 ] ──► [ Application Load Balancer ]│
│                                                     │                  │
│   PRIVATE APPLICATION TIER                          ▼                  │
│   [ Cyberjaya Jumphost ] ──► [ Auto Scaling Group (ARM64 Graviton) ]   │
│                               │ (CodeIgniter 4 + Nginx + PHP-FPM)      │
│                               │                                        │
│   ISOLATED DATA TIER          ▼                                        │
│   ┌──────────────────────────────────┬─────────────────────────────┐   │
│   │ Amazon RDS Multi-AZ (MariaDB/PG) │ ElastiCache Valkey (Session)│   │
│   └──────────────────────────────────┴─────────────────────────────┘   │
│                                                                        │
│   TELEMETRY & SECURITY                                                 │
│   [ Wazuh SIEM & XDR ]  [ CloudWatch APM & RUM ]  [ ASIMP Audit Suite ]│
└────────────────────────────────────────────────────────────────────────┘
```

Key accomplishments of the current baseline include:
1. **Infrastructure as Code (IaC):** Fully modular OpenTofu/Terraform code (`vpc`, `alb`, `asg`, `rds`, `elasticache`, `waf`, `jumphost`, `fusio`, `standalone_ec2`).
2. **Zero-Trust Network Isolation:** Public ALB ingress, isolated private application subnets, and database engines in non-routable private subnets.
3. **Security & Telemetry Consolidation:** Integration of ASIMP (Ansible System Integrity Management Platform), Lynis, OpenSCAP CIS Level 2 audits, Wazuh SIEM/XDR, and Amazon CloudWatch APM/RUM observability.
4. **Disaster Recovery (DR) Readiness:** Evaluated 3+1 DR strategies with regional same-account and cross-account (`ap-southeast-5`) isolation playbooks under Malaysian PDPA Section 129 compliance.

---

## 2. Core Strategic Pillars: API-Ready & MCP-Ready AI Modernisation

Building upon our current AWS 3-Tier baseline, the next strategic phase modernises the enterprise data layer into an **API-Ready and Model Context Protocol (MCP)-Ready** Big Data Analytics & AI Infrastructure (`bda-ai-infra`).

```text
flowchart TD
    subgraph Ingestion ["Bidirectional Ingestion & Quarantine Layer"]
        Ext["External Systems / IoT / Partner APIs / User Feeds"]
        Laravel["Laravel Web Portal (Human Verification Gate)"]
    end

    subgraph Core ["Central Data & Vector Engine (Tier 0 Golden SSoT)"]
        NiFi["Apache NiFi 2.0 (Single Authoritative DB Writer)"]
        Postgres[("Percona Patroni PostgreSQL 18 + pgvector\n(Tier 0 Golden SSoT & AI Provenance Tagging)")]
    end

    subgraph Integration ["Integration & API Layer (Fine-Grained Access Control)"]
        REST["Open REST / gRPC APIs\n(Fusio API Server - Port 8080/443)"]
        MCP["MCP Server Gateway\n(Model Context Protocol - Port 8443)"]
    end

    subgraph Consumers ["Consumers & Autonomous AI Systems"]
        BI["Open BI (Apache Superset / Metabase)"]
        AI["LLMs & Autonomous AI Agents\n(Google Jules & Antigravity)"]
    end

    Ext -->|"Ingress Payload"| Laravel
    Laravel -->|"Verified Human Sign-off"| NiFi
    NiFi -->|"Cryptographic Persistence"| Postgres
    Postgres -->|"FGAC SQL Views"| REST
    Postgres -->|"FGAC Vector & Tool Context"| MCP
    REST -->|"Programmatic Inquiries"| BI
    MCP -->|"Native Tool Execution"| AI
```

### 2.1 API-Ready: Universal Data Exchange
* **Bidirectional Data Flow:** Enterprise applications, IoT edge devices, and partner systems inject structured telemetry directly via REST (Fusio API) or gRPC endpoints, as well as extract real-time operational streams.
* **Zero-Friction Interoperability:** Replaces proprietary connectors with standard JSON/REST interfaces accessible across web apps, mobile clients, and backend services.

### 2.2 MCP-Ready: Native AI & LLM Integration
* **Direct AI Agent Integration:** Implements the open standard **Model Context Protocol (MCP)**. Large Language Models (LLMs) and autonomous agents (such as Google Jules and Antigravity) directly query database metrics, trigger background transformations, and retrieve vector embeddings as native "Tools".
* **Contextual Grounding:** Replaces manual static PDF/Excel exports with conversational, context-aware AI interactions connected directly to live database state.

### 2.3 Fine-Grained Access Control (FGAC) & Data Governance
* **Row & Column Level Security:** Permissions are strictly enforced at the API gateway and database layer using session context injection (`SET LOCAL`). External applications or AI agents access only the precise data slices authorised for their authenticated identity.
* **Human SSoT & AI Provenance Tagging (`bda_provenance`):** Human-generated data remains the sole authoritative **Single Source of Truth (SSoT)** validated through the human-in-the-loop verification gate. Any dataset created, modified, or enriched by AI processes is explicitly tagged using `bda_provenance` metadata.

```json
{
  "bda_provenance": {
    "signature": "e2a9b418...",
    "key_id": "key-ed25519-prod-01",
    "verification_status": "VERIFIED_AI_ENRICHED",
    "verification_timestamp": "2026-08-11T12:00:00+08:00",
    "signature_algorithm": "Ed25519",
    "signature_encoding": "HEX_RAW_64_BYTE"
  }
}
```

---

## 3. Summary Routing & Data Ingress Table

| Source Component | Target Component | Protocol / Port | Ingress Security Boundary | Operational Significance & Flow |
| :--- | :--- | :--- | :--- | :--- |
| **External Systems / Users** | Laravel Verification Gate | HTTPS (443) / REST | Keycloak OAuth2 / Session Auth | Ingests non-IT user feeds and telemetry into quarantine staging directory. |
| **Laravel Verification Gate** | Apache NiFi 2.0 Ingest Gate | Internal Event Spool | Human Signature / Audit Log | Triggers approval workflow upon explicit human verification. |
| **Apache NiFi 2.0 Ingest Gate** | PostgreSQL 18 SSoT Store | TCP 5432 / Native PG | `nifi_ingest_writer` DB Role | Sole authoritative writer committing Tier 0 Golden SSoT data and `bda_provenance` tags. |
| **PostgreSQL 18 SSoT Store** | Fusio REST / gRPC Gateway | TCP 5432 / Read Views | PostgreSQL Row-Level Security | Exposes fine-grained SQL views and endpoints to web apps and BI dashboards. |
| **PostgreSQL 18 SSoT Store** | MCP Tool Gateway | TCP 5432 / Vector Search | MCP Tool Scope & Ed25519 Token | Serves vector context and structured database tool capabilities to autonomous AI agents. |

---

## 4. Tableau Migration & Modernisation Strategy

Legacy Tableau workbooks will be systematically decommissioned using a four-phase migration roadmap to ensure zero downtime and manage operational risk:

```text
[ Phase 1: Audit ] ──► [ Phase 2: Logic Transfer ] ──► [ Phase 3: Open BI ] ──► [ Phase 4: MCP/API ]
```

1. **Phase 1: Workbook Audit & Inventory:** Catalogue all active Tableau workbooks (`.twb`/`.twbx`), calculated fields, custom SQL queries, and user permission matrices. Identify redundant reports and mark high-value dashboards for migration.
2. **Phase 2: Data & Logic Consolidation:** Migrate complex Tableau calculations and data blending rules directly into PostgreSQL Materialised Views and stored functions. Ensure Apache NiFi orchestrates clean data pipelines into normalized schemas.
3. **Phase 3: Open-Source BI Deployment:** Deploy containerised Apache Superset (or Metabase) on Podman to replicate executive dashboards with zero user-license fees.
4. **Phase 4: API & MCP Enablement:** Expose business metrics as REST/gRPC API endpoints and wrap vector searches into standardised MCP Tools for internal AI agent workflows.

---

## 5. Podman Infrastructure & Container Blueprint

The target infrastructure relies on rootless Podman pods to enforce high availability, zero vendor lock-in, and full Kubernetes compatibility.

```yaml
# Conceptual Architecture Blueprint: podman-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: bda-ai-infra-pod
spec:
  containers:
    - name: postgres-engine
      image: docker.io/pgvector/pgvector:pg18
      description: "Central database store equipped with vector search capabilities."

    - name: nifi-orchestrator
      image: docker.io/apache/nifi:latest
      description: "Low-latency data ingestion, batch processing, and ETL orchestrator."

    - name: mcp-api-gateway
      image: localhost/bda-mcp-server:v1
      description: "Custom Python/Node.js gateway delivering Open APIs, MCP Tools, and FGAC enforcement."

    - name: open-bi-superset
      image: docker.io/apache/superset:latest
      description: "Open-source business intelligence platform replacing Tableau."
```

---

## 6. Financial & Operational ROI (3-Year TCO Comparison)

To evaluate Total Cost of Ownership (TCO) in the Malaysia region (`ap-southeast-5`), we compare the legacy setup, self-hosted EC2 stacks, and the proposed API/MCP Podman stack over a 36-month timeline (1 USD ≈ 4.50 MYR).

| Area | Legacy Architecture (Tableau-based) | Self-Hosted Custom Stack (EC2) | Proposed AWS + Podman Stack |
| :--- | :--- | :--- | :--- |
| **Licensing Costs** | High recurring per-user ($42/user/mo) and core fees. | $0.00 proprietary software fees. | **$0.00 proprietary software fees (100% Open Source).** |
| **Data Accessibility** | Locked inside proprietary `.twb` workbooks. | Direct SQL queries requiring DB access. | **Universal API & MCP endpoints accessible by any tool/agent.** |
| **Engineering OpEx** | High manual maintenance & export labor. | High ($1,500/mo DBRE labor for Patroni/etcd). | **Optimised ($150/mo automated OpenTofu management).** |
| **AI Integration** | None (Manual Excel exports required). | Custom custom-built agent scripts. | **Native MCP support for autonomous AI workflows.** |
| **3-Year Total TCO** | **~$110,000.00 USD (MYR 495,000)** | **$78,016.68 USD (MYR 351,075)** | **$39,430.80 USD (MYR 177,438)** |

### Financial Impact Summary
Transitioning to the proposed AWS + Podman API/MCP Architecture saves **$38,585.88 USD (~RM 173,636.46 MYR)** over 36 months compared to self-managed EC2 stacks, and over **$70,500.00 USD (~RM 317,250.00 MYR)** compared to legacy Tableau setups—representing a **49.5% to 64.1% net savings**.

---

## 7. Next Steps & Execution Roadmap

Upon approval of this proposal, execution will proceed as follows via automated code and configuration updates:

1. **Commit Proposal Document:** Save `docs/IT-MANAGEMENT-PROPOSAL.md` into the main repository branch.
2. **Deploy Podman Pod Spec:** Commit container definitions for PostgreSQL 18 pgvector, NiFi, and Superset in rootless Podman configurations.
3. **Build MCP Gateway Skeleton:** Deploy the Python/Node.js MCP gateway with PostgreSQL tool connections and FGAC middleware.
4. **Initiate Phase 1 Migration:** Begin Tableau workbook audit and SQL logic extraction.

---

*Deep State of Mind (DSOM) For My AI Protocol Harisfazillah Jamel (LinuxMalaysia) 2026-08-11 Standard: UK English DBP-standard Bahasa Melayu Malaysia (Piawai) GNU General Public License v3.0*
CmsForNerd Infrastructure: [linuxmalaysia.com](https://linuxmalaysia.com/)
Copyright © 2005 - 2026 Harisfazillah Jamel
[ REL: 3.5.1 ] | [ STD: RFC_9116 ] | [ ENV: OPENTOFU_1.6 ] | [ VIEW: STANDARD ]
Rendered: Statically Compiled at Build-time | MEM: 0 KB (Zero-runtime database-free)
