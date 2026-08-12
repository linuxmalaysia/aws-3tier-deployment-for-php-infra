---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "AWS Services vs. On-Premises Open-Source Comparison Guide"
timestamp: "2026-08-11T12:00:00+08:00"
topics: ["aws", "3-tier", "on-premises", "comparison"]
---

**[DEVOPS EXECUTION]** **[STRATEGIC FINANCIAL]**

# AWS Services vs. On-Premises Open-Source Comparison Guide

## Notice & Disclaimer
**All costs, designs, unit amounts, and scenarios detailed within this document are based entirely on assumptions. This project and its accompanying documentation are compiled strictly for training, educational, and planning proposal purposes. Use at your own risk. The project contributors, authors, and organisations shall not be held liable or responsible for any decisions or actions taken based on these materials.**

---

This guide provides a comprehensive architectural and operational comparison between AWS Cloud Services and On-Premises Onsite Open-Source Software Solutions across all 12 critical infrastructure layers of our modern enterprise application.

To support organisations planning a cloud adoption roadmap or evaluating complete local data sovereignty, this document contrasts the managed, automated conveniences of AWS with the raw host control, license-compliant, and self-hosted cost efficiencies of an on-premises stack.

---

## The 12-Layer Enterprise Infrastructure Stack

The following diagram illustrates the 12 key layers that comprise our enterprise web and application infrastructure, from user interaction to runtime observability, following the exact structure of our system blueprint:

```
┌────────────────────────────────────────────────────────┐
│ 1. Frontend (Web & Mobile UI Assets)                   │
├────────────────────────────────────────────────────────┤
│ 2. APIs & Backend Logic (Business Engines)              │
├────────────────────────────────────────────────────────┤
│ 3. Database & Storage (Relational, Objects & Vectors)  │
├────────────────────────────────────────────────────────┤
│ 4. Auth & Permissions (Identity Providers)             │
├────────────────────────────────────────────────────────┤
│ 5. Hosting & Deployment (Orchestration & Runtimes)     │
├────────────────────────────────────────────────────────┤
│ 6. Cloud & Compute (Virtualisation & Hardware)         │
├────────────────────────────────────────────────────────┤
│ 7. CI/CD & Version Control (Delivery Pipelines)        │
├────────────────────────────────────────────────────────┤
│ 8. Security & RLS (Firewalls, IDS & Data Isolation)    │
├────────────────────────────────────────────────────────┤
│ 9. Rate Limiting (Traffic Protection & Throttling)     │
├────────────────────────────────────────────────────────┤
│ 10. Caching & CDN (Low-Latency Acceleration)           │
├────────────────────────────────────────────────────────┤
│ 11. Load Balancing & Scaling (High Availability)       │
├────────────────────────────────────────────────────────┤
│ 12. Error Tracking & Logs (Observability & Telemetry)   │
└────────────────────────────────────────────────────────┘
```

---

## Comprehensive 12-Layer Architectural Mapping

Below is a detailed, layer-by-layer strategic and technical breakdown comparing the AWS-Native Managed Stack against the Hardened On-Premises Open-Source Equivalent running on rootless containers or local virtual machine hypervisors.

---

### Layer 1: Frontend

Frontend static assets must be delivered with minimum latency and high security. In modern decoupled architectures, the presentation layer is entirely separated from backend transactional processing.

* **AWS Cloud-Native Option:**
  * **Services:** Amazon S3 (Static Website Hosting) combined with Amazon CloudFront (Global Content Delivery Network).
  * **Architectural Behaviour:** Compiled static web files (HTML, CSS, JavaScript) are stored securely inside an S3 bucket with public access disabled. CloudFront distributes these assets to Edge Locations globally.
  * **Advantages:** Scale is completely automated and virtually infinite; zero compute resources are wasted on serving static pages, and the origin bucket is protected from direct scanning or malicious manipulation.

* **On-Premises / Onsite Open-Source Option:**
  * **Solutions:** Nginx or BunkerWeb web-server serving pre-compiled web assets, or lightweight Node.js containers.
  * **Architectural Behaviour:** Static assets are served locally by Nginx or a BunkerWeb container inside a virtual machine.
  * **Advantages:** Absolute control over custom web headers, local caching profiles, and logging. Eliminates external CDN bandwidth charges, making it highly cost-effective for local workloads where WAN transit is constrained.

---

### Layer 2: APIs & Backend Logic

The core business engine, housing API routing, backend controllers, background task workers, and transactional integrations. Our application layer is a pure PHP application utilising the CodeIgniter framework and Fusio API Server, served via Nginx and PHP-FPM, completely free of any AI or RAG-related components.

* **AWS Cloud-Native Option:**
  * **Services:** Amazon ECS (Elastic Container Service) on AWS Fargate or stateless Auto Scaling Groups (ASG) of AWS Graviton (e.g. `t4g.xlarge` / `c7g.xlarge`) instances running PHP-FPM, Nginx, and Fusio API Server.
  * **Architectural Behaviour:** Automatically scales compute resources up and down based on target CPU or memory utilisation profiles.
  * **Advantages:** Fully managed, serverless, or auto-scaling environments reduce the burden of OS kernel tuning and ensure maximum resource utilisation efficiency.

* **On-Premises / Onsite Open-Source Option:**
  * **Solutions:** CodeIgniter and Fusio API Server running on PHP-FPM 8.2+ and Nginx inside rootless, unprivileged Podman 5+ containers managed by systemd Quadlets on local enterprise Linux hosts.
  * **Architectural Behaviour:** Containers run without administrative root privileges using systemd lingering and user namespace `keep-id` remapping.
  * **Advantages:** Removes public cloud hypervisor markup fees, locks runtime environments to strict local hardware boundaries, and allows deep customisation of the PHP-FPM process pool manager, socket queues, and host filesystem parameters.

---

### Layer 3: Database & Storage

The persistence layer, which must support high-performance ACID transactions, robust backup streaming, and shared object storage.

* **AWS Cloud-Native Option:**
  * **Services:** Amazon RDS PostgreSQL 17 (Multi-AZ) or Amazon RDS MariaDB, and Amazon S3 (Object Storage) or Amazon EFS (Elastic File System).
  * **Architectural Behaviour:** Managed synchronous block-level replication across multiple availability zones. RDS handles automated patching, daily backups, and point-in-time recovery (PITR) natively.
  * **Advantages:** Minimal operational risk; automated failover under 120 seconds with zero single-point-of-failure (SPOF) storage replication.

* **On-Premises / Onsite Open-Source Option:**
  * **Solutions:** Percona Server for PostgreSQL 17+ (with Patroni cluster orchestration, etcd consensus, and pg_backrest backups) or local Percona MariaDB, combined with MinIO (S3-compatible Object Storage).
  * **Architectural Behaviour:** High availability is engineered locally using a three-node cluster (two database engines and an etcd distributed consensus coordinator). HAProxy or PgBouncer handles primary/replica routing.
  * **Advantages:** Complete binary compatibility with upstream PostgreSQL, enterprise-grade Percona extensions like `pg_stat_monitor` out of the box, zero licensing fees, local processing on dedicated bare-metal NVMe drives, and zero cross-AZ data transfer surcharges.

---

### Layer 4: Auth & Permissions

Securing user identities, implementing Multi-Factor Authentication (MFA), issuing secure JSON Web Tokens (JWT), and enforcing Role-Based Access Control (RBAC).

* **AWS Cloud-Native Option:**
  * **Services:** Amazon Cognito User Pools & Identity Pools.
  * **Architectural Behaviour:** A fully managed, serverless identity directory that implements OAuth 2.0 and OpenID Connect (OIDC) patterns natively.
  * **Advantages:** Seamless integration with AWS WAFv2, offloads credentials security auditing from the local database, and supports automated token signing and rotation.

* **On-Premises / Onsite Open-Source Option:**
  * **Solutions:** Keycloak or Authentik integrated with PHP/CodeIgniter and local Percona PostgreSQL database tables.
  * **Architectural Behaviour:** Highly customisable, open-source identity providers deployed in local containers, supporting OAuth 2.0, SAML 2.0, and LDAP integrations.
  * **Advantages:** Eliminates external monthly active user (MAU) licensing charges, keeps user credentials physically isolated on-site, and allows customisation of login flow designs, session timeouts, and branding.

---

### Layer 5: Hosting & Deployment

Container orchestration and deployment execution. Decides how workload containers are structured, started, and managed.

* **AWS Cloud-Native Option:**
  * **Services:** Amazon ECS on AWS Fargate, AWS Launch Templates, or Auto Scaling Groups.
  * **Architectural Behaviour:** Abstracts container runtime interfaces entirely. Deployments are declared via CloudFormation, OpenTofu, or AWS Copilot.
  * **Advantages:** Zero infrastructure management. Eliminates the need to configure node networking, container registries, or control planes.

* **On-Premises / Onsite Open-Source Option:**
  * **Solutions:** Podman 5+ utilising systemd Quadlets, or a lightweight local container deployment.
  * **Architectural Behaviour:** Quadlets are declarative systemd configuration files that generate and run containers natively under systemd, treated exactly as standard OS services.
  * **Advantages:** Clean, configuration-driven deployments without the massive system overhead of a heavy Kubernetes control plane. Containers restart on host boot automatically without daemon dependencies.

---

### Layer 6: Cloud & Compute

The physical or virtualised hardware executing the instructions. Highly influential over overall performance and cost efficiency.

* **AWS Cloud-Native Option:**
  * **Services:** Amazon EC2 running AWS Graviton (ARM64) processors (such as `t4g`, `c7g`, or `r7g` instance families).
  * **Architectural Behaviour:** Instances are provisioned on demand in multiple independent physical locations (Availability Zones).
  * **Advantages:** Infinite, elastic hardware availability on-demand; easy access to high-performance enterprise hardware with zero capital expenditure (CapEx).

* **On-Premises / Onsite Open-Source Option:**
  * **Solutions:** Bare-metal rack servers running Proxmox VE, KVM (Kernel-based Virtual Machine), or XCP-ng hypervisors on AMD EPYC / Intel Xeon architectures.
  * **Architectural Behaviour:** Physical servers are carved into multiple virtual machines using local hypervisors, with dedicated storage configurations.
  * **Advantages:** High, sustained compute performance at flat costs. Avoids public cloud virtual machine hypervisor overhead, memory tax, and storage throughput throttling.

---

### Layer 7: CI/CD & Version Control

The automated pipelines that receive code commits, run testing suites, audit configurations, and compile production-ready assets.

* **AWS Cloud-Native Option:**
  * **Services:** AWS CodePipeline, AWS CodeBuild, and AWS CodeDeploy (integrated with GitHub Actions for deployment).
  * **Architectural Behaviour:** Serverless pipelines triggered directly by code events, running builds in secure, ephemeral container runtimes.
  * **Advantages:** Integrates natively with IAM permissions, secrets managers, and ECS/ASG deployment endpoints.

* **On-Premises / Onsite Open-Source Option:**
  * **Solutions:** Gitea (Private git repository hosting) integrated with Ansible Semaphore (Automated UI task runner) and Ansible ARA (Execution callbacks recorder), or GitLab CI/CD with local runners.
  * **Architectural Behaviour:** Developer pushes code to Gitea; a webhook triggers Ansible Semaphore playbooks to build, test, and deploy containers across the private network.
  * **Advantages:** 100% self-hosted, private version control; allows ultra-fast local build caching, and records detailed execution reports in local compliance databases.

---

### Layer 8: Security & RLS

Perimeter security, intrusion detection systems (IDS), Row-Level Security (RLS) in databases, and active host hardening.

* **AWS Cloud-Native Option:**
  * **Services:** AWS WAFv2 (Web Application Firewall), AWS Shield (DDoS Protection), and AWS Security Hub / Amazon GuardDuty.
  * **Architectural Behaviour:** Agentless, cloud-plane detection analysing VPC flow logs, DNS queries, and IAM API calls to spot threats instantly.
  * **Advantages:** Global threat intelligence databases, zero performance impact on application servers, and automated compliance auditing.

* **On-Premises / Onsite Open-Source Option:**
  * **Solutions:** BunkerWeb (Open-source WAF), Wazuh SIEM (Host Intrusion Detection), and PostgreSQL native Row-Level Security (RLS) policies.
  * **Architectural Behaviour:** Wazuh agents are installed on all local hosts to collect logs, check CIS compliance, and audit system integrity. BunkerWeb filters incoming web traffic using security-tuned Nginx rules.
  * **Advantages:** Comprehensive host-level intrusion detection and auditing; significantly cheaper than cloud-native alternatives. PostgreSQL RLS ensures strict tenant-level data isolation directly at the database engine level.

---

### Layer 9: Rate Limiting

Preventing API abuse, brute-force login attempts, and denial-of-service (DDoS) spikes from saturating application logic threads.

* **AWS Cloud-Native Option:**
  * **Services:** AWS WAFv2 Rate-Limiting Rules or Amazon API Gateway Throttling.
  * **Architectural Behaviour:** Traffic is inspected and throttled at the AWS edge network before it ever reaches backend EC2 or container instances.
  * **Advantages:** Eliminates backend compute saturation; traffic from abusive IPs is dropped at the nearest regional edge location.

* **On-Premises / Onsite Open-Source Option:**
  * **Solutions:** BunkerWeb / Nginx rate-limiting modules, combined with Valkey (for dynamic API usage counters).
  * **Architectural Behaviour:** BunkerWeb tracks requests per second per IP and rejects requests exceeding thresholds. For advanced application-level rate limiting, PHP-FPM/CodeIgniter checks and increments counters stored in Valkey.
  * **Advantages:** Fully customisable rulesets, zero external latency overhead for looking up rate limits, and zero public cloud billing surcharges for high traffic counts.

---

### Layer 10: Caching & CDN

Accelerating delivery of dynamic API responses and static assets while reducing read load on primary database systems.

* **AWS Cloud-Native Option:**
  * **Services:** Amazon ElastiCache for Valkey (In-Memory Key-Value Caching) and Amazon CloudFront.
  * **Architectural Behaviour:** Fully managed Multi-AZ in-memory database clusters configured in private subnets with automated node failovers.
  * **Advantages:** Full compatibility with Valkey/Redis API, and 20% lower instance pricing than legacy Redis engines.

* **On-Premises / Onsite Open-Source Option:**
  * **Solutions:** Self-hosted containerised Valkey running in containerised or standalone modes, combined with local Nginx proxy caching.
  * **Architectural Behaviour:** Valkey is deployed locally on physical hosts with transit and at-rest encryption enabled, serving as a shared session and API cache layer.
  * **Advantages:** Zero network latency penalty (sub-millisecond local network execution), complete open-source license compliance, and flat resource allocation with zero managed service markups.

---

### Layer 11: Load Balancing & Scaling

Distributing incoming user traffic uniformly across active backend instances to prevent single-instance saturation, combined with dynamic auto-healing.

* **AWS Cloud-Native Option:**
  * **Services:** AWS Application Load Balancer (ALB) and Auto Scaling Groups (ASG).
  * **Architectural Behaviour:** Health checks constantly monitor instances; if an instance becomes unhealthy or if CPU usage exceeds the threshold, the ASG terminates the node and launches a new one automatically.
  * **Advantages:** Highly available, multi-AZ by default, and seamlessly handles unexpected traffic spikes.

* **On-Premises / Onsite Open-Source Option:**
  * **Solutions:** HAProxy / Keepalived for high-availability load balancing, combined with local hypervisor auto-scaling pools.
  * **Architectural Behaviour:** Active-passive load balancers are configured using HAProxy and virtual IPs (Keepalived). Local hypervisor scripts monitor container loads and dynamically adjust resources.
  * **Advantages:** HAProxy is recognised as one of the world's fastest open-source load balancers, offering superior throughput, customisable balancing algorithms, and advanced TCP-level proxy configurations.

---

### Layer 12: Error Tracking & Logs

Monitoring system performance, logging errors, tracing distributed transactions, and collecting security event logs.

* **AWS Cloud-Native Option:**
  * **Services:** Amazon CloudWatch Logs, AWS X-Ray (Distributed Tracing), and Amazon CloudWatch Container Insights.
  * **Architectural Behaviour:** Ephemeral agents stream system logs and performance metrics to a centralised CloudWatch data lake.
  * **Advantages:** Zero configuration required; unified dashboarding and native integration with SNS alerts.

* **On-Premises / Onsite Open-Source Option:**
  * **Solutions:** Wazuh SIEM, Grafana Loki / Prometheus, and Signoz or Jaeger (Distributed Tracing).
  * **Architectural Behaviour:** Systemd logs are processed locally by Grafana Promtail and streamed to Loki. Prometheus scrapes application metrics, and Wazuh aggregates audit logs.
  * **Advantages:** Absolute control over logs retention policies (no data ingestion or retention charges), local storage compliance, and unified visualisation dashboards.

---

## Strategic Summary Matrix

The matrix below provides an executive-level summary of the architectural and financial trade-offs between the two environments across all 12 layers:

| Layer | AWS Cloud-Native Managed Stack | On-Premises Open-Source Solution | Key Decision Driver |
| :--- | :--- | :--- | :--- |
| **1. Frontend** | S3 Website + CloudFront CDN | Nginx / BunkerWeb Web Server | Latency at the edge vs. bandwidth cost. |
| **2. APIs & Backend** | AWS ASG / ECS on Graviton | PHP-FPM on Rootless Podman 5+ | Elastic auto-scaling vs. absolute host control. |
| **3. Database & Storage** | RDS PostgreSQL (Multi-AZ) + S3 | Percona PostgreSQL 17+ with Patroni | Zero operational database administration vs. no transfer fees. |
| **4. Auth & Permissions** | Amazon Cognito User Pools | Keycloak / Authentik | Managed identity lifecycle vs. zero licensing MAU charges. |
| **5. Hosting & Deployment**| AWS ECS on Fargate | systemd Quadlet Containers | Zero-infra container management vs. minimal system overhead. |
| **6. Cloud & Compute** | On-demand Multi-AZ EC2 instances | Bare-Metal Servers + Proxmox VE | Infinite elasticity vs. sustained heavy performance. |
| **7. CI/CD Pipeline** | AWS CodePipeline / CodeBuild | Gitea + Ansible Semaphore + ARA | Ephemeral cloud executors vs. secure local git compliance. |
| **8. Security & IDS** | AWS WAFv2 + GuardDuty | BunkerWeb + Wazuh SIEM | Cloud control-plane scanning vs. host compliance auditing. |
| **9. Rate Limiting** | AWS WAFv2 Edge Throttling | BunkerWeb + Nginx + Valkey | Edge blocking vs. zero execution latency. |
| **10. Caching & CDN** | ElastiCache Valkey + CloudFront | Containerised Valkey + Nginx | Managed Multi-AZ clusters vs. sub-millisecond local network times. |
| **11. Load Balancing** | AWS Application Load Balancer | HAProxy + Keepalived Virtual IPs | Auto-scaling integration vs. ultra-fast local throughput. |
| **12. Error Tracking** | CloudWatch Logs + AWS X-Ray | Grafana Loki + Prometheus + Wazuh | Unified zero-infra dashboards vs. free data ingestion and retention. |

---

*Deep State of Mind (DSOM) For My AI Protocol Harisfazillah Jamel (LinuxMalaysia) 2026-08-11 Standard: UK English DBP-standard Bahasa Melayu Malaysia (Piawai) GNU General Public License v3.0*
CmsForNerd Infrastructure: [linuxmalaysia.com](https://linuxmalaysia.com/)
Copyright © 2005 - 2026 Harisfazillah Jamel
[ REL: 3.5.1 ] | [ STD: RFC_9116 ] | [ ENV: OPENTOFU_1.6 ] | [ VIEW: STANDARD ]
Rendered: Statically Compiled at Build-time | MEM: 0 KB (Zero-runtime database-free)
