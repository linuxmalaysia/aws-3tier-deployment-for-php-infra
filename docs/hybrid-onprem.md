---
layout: default
title: "Hybrid Cloud Network Connections"
---

# Hybrid Cloud Network Connections

This document evaluates the architectural designs and secure, cost-effective connection methodologies for establishing communication paths between our **AWS 3-Tier CodeIgniter PHP Application** (running in the AWS Malaysia region `ap-southeast-5`) and on-premises enterprise resources (such as legacy corporate offices or regional datacenters in Cyberjaya and Kuala Lumpur).

---

## 1. Architectural Options Matrix

To establish hybrid connections, organizations can choose between four standard AWS network configurations based on budget, bandwidth, and security guidelines:

| Connection Option | Encryption Protocol | Typical Throughput | Target Use Case | Relative Cost (Monthly) |
| :--- | :--- | :--- | :--- | :--- |
| **AWS Site-to-Site VPN** | IPSec (AES-256) | Up to 1.25 Gbps per tunnel | Encrypted administration, secure staging database syncs | **Low** (~$36.50 USD / tunnel + data transfer) |
| **AWS Direct Connect (DX)** | MACsec (Optional) | 1 Gbps to 100 Gbps | High-performance, low-latency bulk database replication | **High** (~$150 USD + dedicated port charges) |
| **AWS Transit Gateway** | Chained VPN / DX | Scalable up to 50 Gbps | Multi-VPC complex network topology routing | **Moderate** (~$36.50 USD + processing fees) |
| **API-Based Gateway (Secure HTTPS)** | TLS 1.3 with mTLS | Variable (internet-bound) | Lightweight REST API calls, public callbacks, webhooks | **Zero Infrastructure Cost** (Pay-per-request) |

---

## 2. Low-Cost Option: Secure API-Based Connections

For agile teams looking to connect on-premises corporate systems with AWS without procuring expensive dedicated hardware or paying high monthly VPN costs, we recommend **Secure API-Based Connections** over HTTPS.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Secure API Integration Architecture             │
│                                                                        │
│   AWS Cloud (ap-southeast-5)                                           │
│  ┌──────────────────────┐            ┌────────────────────────────┐    │
│  │   CodeIgniter App    │ ──────────►│     Amazon API Gateway     │    │
│  │    (ASG Compute)     │            │ (mTLS / Token Auth Proxy)  │    │
│  └──────────────────────┘            └─────────────┬──────────────┘    │
└────────────────────────────────────────────────────┼───────────────────┘
                                                     │ Secure HTTPS / WebSockets
                                                     │ (Outbound Only)
                                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│   On-Premises Datacenter                                               │
│  ┌──────────────────────┐            ┌────────────────────────────┐    │
│  │   Corporate Firewall │ ──────────►│      On-Premises API       │    │
│  │ (Outbound Only Open) │            │ (Processes Legacy Requests)│    │
│  └──────────────────────┘            └────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
```

### Technical Workflow
1. **Lightweight Routing:** Instead of stretching a physical network tunnel, the CodeIgniter application triggers standard secure HTTPS calls to local on-premises servers.
2. **Mutual TLS (mTLS):** To guarantee that only verified AWS resources can query on-premises resources, the connection enforces mTLS, where both client and server present cryptographic certificates.
3. **Firewall Integrity:** The local corporate datacenter only needs to allow **outbound** HTTPS connections. No inbound ports need to be exposed on the corporate firewall, dramatically reducing the threat vector.
4. **Data Masking:** Any sensitive data is filtered, sanitized, and tokenized before it leaves the local network.

---

## 3. Financial Cost Projections (ap-southeast-5)

To support technical decision-making, we present a comparison of estimated monthly operating costs for hybrid connections in both **USD** and **MYR** (assuming 1 USD = 4.50 MYR).

### Line-Item Cost Projections

1. **AWS Site-to-Site VPN:**
   - AWS Connection Charge: $0.05 / hour ($36.50 USD / month)
   - On-Premises hardware setup/maintenance allocation: ~$20.00 USD / month
   - **VPN Total: ~$56.50 USD / month (RM 254.25 MYR / month)**

2. **Secure API-Based Gateway:**
   - Amazon API Gateway regional call charges: $1.00 per Million requests
   - Data transfer outbound: $0.09 / GB (assuming 20 GB data transferred)
   - **API Gateway Total: ~$3.00 USD / month (RM 13.50 MYR / month)**
