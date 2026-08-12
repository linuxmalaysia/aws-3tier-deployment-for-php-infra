---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "Hybrid Cloud Network Connections"
timestamp: "2026-08-05T22:20:36+08:00"
topics: ["aws", "3-tier"]
---

**[STRATEGIC FINANCIAL]**

# Hybrid Cloud Network Connections


This document evaluates the architectural designs and secure, cost-effective connection methodologies for establishing communication paths between our **AWS 3-Tier CodeIgniter PHP Application** (running in the AWS Malaysia region `ap-southeast-5`) and on-premises enterprise resources (such as legacy corporate offices or regional datacenters in Cyberjaya and Kuala Lumpur).

---


## 1. Architectural Options Matrix


To establish hybrid connections, organizations can choose between four standard AWS network configurations based on budget, bandwidth, and security guidelines:

| Connection Option | Encryption Protocol | Typical Throughput | Target Use Case | Relative Cost (Monthly) |
| :--- | :--- | :--- | :--- | :--- |
| **AWS Site-to-Site VPN** | IPSec (AES-256) | Up to 1.25 Gbps per standard tunnel (supports up to 5 Gbps with Transit Gateway) | Encrypted administration, secure staging database syncs. Billing is per VPN connection (includes 2 tunnels for HA). | **Low** ($36.50 USD per VPN connection + data transfer) |
| **AWS Direct Connect (DX)** | MACsec (Optional) | 1 Gbps to 100 Gbps | High-performance, low-latency bulk database replication | **High** (~$150 USD + dedicated port charges) |
| **AWS Transit Gateway** | Chained VPN / DX | Scalable up to 50 Gbps | Multi-VPC complex network topology routing | **Moderate** (~$36.50 USD + processing fees) |
| **API-Based Gateway (Secure HTTPS)** | TLS 1.2 (for mTLS custom domains) / TLS 1.3 | Variable (internet-bound) | Lightweight REST API calls, public callbacks, webhooks | **Zero Infrastructure Cost** (Pay-per-request) |

---


## 2. Low-Cost Option: Secure API-Based Connections


For agile teams looking to connect on-premises corporate systems with AWS without procuring expensive dedicated hardware or paying high monthly connection costs, we recommend **Secure API-Based Connections** over HTTPS.

To align with outbound-only on-premises firewall policies, the connection is designed as a **reverse-persistent WebSocket connection** initiated and maintained entirely by the on-premises API runner.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        Secure API Integration Architecture             │
│                                                                        │
│   AWS Cloud (ap-southeast-5)                                           │
│  ┌──────────────────────┐            ┌────────────────────────────┐    │
│  │   CodeIgniter App    │ ──────────►│  Amazon API Gateway        │    │
│  │    (ASG Compute)     │            │  (mTLS Custom Domain /     │    │
│  │                      │            │   WebSocket API Gateway)   │    │
│  └──────────────────────┘            └─────────────▲──────────────┘    │
└────────────────────────────────────────────────────│───────────────────┘
                                                     │ Secure Outbound Connection
                                                     │ (Persistent WebSocket on Port 443)
                                                     │ (mTLS TLS 1.2 Handshake)
┌────────────────────────────────────────────────────│───────────────────┐
│   On-Premises Datacenter                           │                   │
│  ┌──────────────────────┐            ┌─────────────┴──────────────┐    │
│  │   Corporate Firewall │ ──────────►│   On-Premises API Agent    │    │
│  │ (Outbound Only Open) │            │ (Initiates & maintains     │    │
│  │                      │            │  the reverse websocket)    │    │
│  └──────────────────────┘            └────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
```


### Technical Workflow


1. **Reverse Tunnel Initiation:** The on-premises API agent initiates and maintains a persistent outbound-only HTTPS WebSocket connection to the Amazon API Gateway endpoint on Port 443. This maintains a persistent duplex communication channel without opening any inbound ports on the corporate firewall.
2. **Duplex Request Routing:** When the CodeIgniter application needs to query on-premises legacy resources, it publishes a request payload to the active API Gateway WebSocket channel, which routes it down to the pre-established persistent connection on-premises.
3. **mTLS Protection Scope & Certificate Handshake:**
   - **mTLS Enforced custom domain:** Mutual TLS (mTLS) is enforced strictly on the API Gateway Regional Custom Domain. Amazon API Gateway currently terminates mTLS using **TLS 1.2** for custom domains.
   - **S3 PEM Truststore:** Client certificates are validated against a designated truststore bucket (S3 PEM file containing the CA certificate).
   - **Disable Default Endpoint:** The default execute-api endpoint (`https://{api-id}.execute-api.{region}.amazonaws.com`) **must be explicitly disabled** (`DisableExecuteApiEndpoint = true`) because mTLS does not protect or apply to the default endpoint. This prevents any bypass of the truststore.
   - **Validation & Rotation:** Enforces backend server certificate validation, hostname validation, and regular cryptographic certificate rotation.
4. **Data Masking:** Any sensitive data is filtered, sanitized, and tokenized before it leaves the local network.

---


## 3. Financial Cost Projections (ap-southeast-5)


To support technical decision-making, we present a comparison of estimated monthly operating costs for hybrid connections in both **USD** and **MYR** (assuming 1 USD = 4.50 MYR).

### Line-Item Cost Projections

1. **AWS Site-to-Site VPN (Per Connection):**
   - AWS Connection Charge: $0.05 / hour ($36.50 USD / month per VPN connection which includes two active tunnels for HA)
   - On-Premises hardware setup/maintenance allocation: ~$20.00 USD / month
   - **VPN Total: ~$56.50 USD / month (RM 254.25 MYR / month)**

2. **Secure API-Based Gateway (API Gateway WebSocket API & REST API):**
   - **Assumptions:**
     - Split request volumes: 500,000 Regional REST API requests and 500,000 WebSocket messages per month (totaling 1 Million requests/messages).
     - WebSocket payload size: Average payload size is 5 KB (maximum 128 KB limit), well within the 32-KB billable unit frame size.
     - Billable units: 500,000 is the total count of 32-KB billable units (accounting for both sent and received messages).
     - WebSocket connection minutes: 20,000 connection minutes per month.
     - Outbound internet egress: 15 GB of outbound data transfer.
     - Routing & Regional Rates: Because API Gateway WebSockets are routed via the neighboring Singapore (`ap-southeast-1`) regional endpoint to support integration with Malaysia (`ap-southeast-5`), Singapore regional rates are applied.
     - Free Tier Allowance: Standard AWS Free Tier allowances are excluded to reflect actual baseline on-demand operational run-rates.
     - **Pricing Source:** AWS API Gateway Pricing Guide (accessed August 2026).
   - **Calculations (Singapore ap-southeast-1 Rates):**
     - Regional REST API Requests: 0.5 Million requests * $3.50 / Million = $1.75 USD.
     - WebSocket Message Processing: 0.5 Million billable 32-KB units * $1.00 / Million = $0.50 USD.
     - WebSocket Connection Charge: 20,000 connection minutes * ($0.25 / Million minutes) = $0.005 USD.
     - Outbound Data Transfer: 15 GB * $0.09 / GB = $1.35 USD.
   - **API Gateway Total: ~$3.61 USD / month (RM 16.25 MYR / month)**
