---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "Hybrid Integration: AWS Site-to-Site VPN vs. On-Premises Fusio API Gateway"
timestamp: "2026-08-12T00:00:00+08:00"
topics: ["aws", "3-tier", "vpn", "fusio", "hybrid"]
---

**[HYBRID ARCHITECTURE & FINANCIAL EVALUATION]**

# Hybrid Integration: AWS Site-to-Site VPN vs. On-Premises Fusio API Gateway

Connecting our **AWS 3-Tier CodeIgniter PHP Application** (deployed in the AWS Malaysia region `ap-southeast-5`) with on-premises corporate nodes, databases, and local datacenters (e.g., in Cyberjaya or Kuala Lumpur) requires a strategic trade-off between private IPsec network extensions and public-facing managed API endpoints.

This guide provides an architectural comparison, operational risk evaluation, AWS cost breakdown (in USD and MYR at 1 USD = 4.50 MYR), and technical recommendation for choosing between **AWS Site-to-Site VPN** and **On-Premises Fusio API Gateway**.

---

## Architectural Comparison

```text
Option 1: Site-to-Site VPN
[AWS App (Private Subnet)] ---> [VGW / IPsec Tunnel] ---> [Customer Gateway (On-Prem)] ---> [Internal API Node]

Option 2: Direct Public API (Fusio)
[AWS App (NAT / Public IP)] ---> [Internet (HTTPS/TLS)] ---> [On-Prem Firewall / Reverse Proxy] ---> [Fusio API]
```

### Option 1: AWS Site-to-Site VPN to On-Premises Gateway

With this topology, your AWS Virtual Private Cloud (VPC) extends its private routing domain directly to your on-premises subnet over an IPsec tunnel. The on-premises API node retains an entirely private IP (RFC 1918) without direct public exposure.

* **Security Posture:** Keeps on-premises database and API gateway endpoints off the public internet by routing traffic across an IPsec tunnel. Operators must explicitly configure and enforce AES-256-GCM-16 (or AES-256-GCM) in Phase 1 and Phase 2 proposals on both the AWS VPN connection and the customer gateway, verifying negotiated settings rather than relying on default proposals. Network ACLs and security groups restrict traffic strictly to designated CIDR blocks.
* **Operational Reality:** Demands route management (BGP or static routes), Dead Peer Detection (DPD), and cryptographic Phase 1/2 policy synchronisation between AWS and your on-premises edge router/firewall (e.g., strongSwan, pfSense, FortiGate, or Cisco).
* **Target Workload:** Highly regulated, sensitive operational data (PII, financial records, core database queries) where internal security policies mandate strict routing controls and zero public internet exposure, aligning with regulatory frameworks like the Malaysian Personal Data Protection Act (PDPA) that require robust technical safeguards against unauthorized access to personal data.

### Option 2: Public-Facing API via Fusio API Gateway

By placing Fusio on-premises as an API management gateway, calls from AWS traverse the public internet over TLS 1.3, authenticating via OAuth2 / JWT / API tokens and basic authentication.

* **Security Posture:** The API port (443) is exposed to the public internet. Mitigation relies entirely on application-layer defenses: strict source IP whitelisting on the on-premises firewall (permitting only your AWS NAT Gateway Elastic IP), mutual TLS (mTLS), and reverse-proxy rate limiting (e.g., via Nginx or BunkerWeb WAF).
* **Operational Reality:** Simpler network plumbing than IPsec routing. However, you absorb application-layer operational toil: certificate rotation, token expiry lifecycles, DDoS risk mitigation, and zero-day surface protection for the exposed PHP runtime.
* **Target Workload:** Discrete, read-heavy query endpoints with strong rate-limiting requirements, or where on-premises network administrators cannot configure IPsec tunnels.

---

## AWS Cost Breakdown

To support strategic decision-making for deployment in `ap-southeast-5`, cost estimates below are provided in **USD** and **MYR** (assuming 1 USD = 4.50 MYR and a standard 730-hour month).

### Option 1 Cost Profile (Site-to-Site VPN)

Assuming an AWS Virtual Private Gateway (VGW) connected directly to your VPC in `ap-southeast-5`:

| AWS Component | Pricing Metric | Estimated Monthly Cost (USD) | Estimated Monthly Cost (MYR) |
| --- | --- | --- | --- |
| **AWS Site-to-Site VPN Connection** | $0.05 / connection / hour | ~$36.50 | ~RM 164.25 |
| **Tunnel Public IPv4 Addresses (2 endpoints)** | $0.005 / address / hour ($0.010/hr total) | ~$7.30 | ~RM 32.85 |
| **Virtual Private Gateway (VGW)** | Included with VPC / VPN | $0.00 | RM 0.00 |
| **Data Transfer OUT (AWS to On-Prem)** | Standard Egress ($0.09 – $0.12/GB depending on region after the shared 100 GB/mo internet data transfer allowance across AWS services/regions is exhausted) | Variable (~$9.00 – $12.00 per 100 GB above shared allowance) | Variable (~RM 40.50 – RM 54.00 per 100 GB above shared allowance) |
| **Data Transfer IN (On-Prem to AWS)** | Ingress traffic to AWS | $0.00 (Free) | RM 0.00 (Free) |
| **Total Baseline (Excluding Bandwidth)** | Fixed tunnel + public IP charge | **~$43.80 / month** | **~RM 197.10 / month** |

*Note on FOSS Alternative:* If you deploy a self-hosted FOSS VPN gateway in AWS (e.g., strongSwan / WireGuard on an EC2 `t4g.small` Graviton instance) instead of managed AWS Site-to-Site VPN, the baseline compute cost is roughly **~$13.94 / month** (~RM 62.74 / month), plus $0.005/hour for an Elastic IP (~$3.65 / month or ~RM 16.43 / month), bringing the combined fixed baseline to roughly **~$17.59 / month** (~RM 79.17 / month) before data egress.

### Option 2 Cost Profile (Public API over Internet)

To establish reliable outbound connectivity from AWS private subnets to your on-premises public IP:

| AWS Component | Pricing Metric | Estimated Monthly Cost (USD) | Estimated Monthly Cost (MYR) |
| --- | --- | --- | --- |
| **AWS NAT Gateway** (1 AZ) | $0.045 / hour | ~$32.85 | ~RM 147.83 |
| **Public IPv4 Allocation (Elastic IP)** | $0.005 / hour | ~$3.65 | ~RM 16.43 |
| **NAT Data Processing** | $0.045 / GB | ~$4.50 per 100 GB | ~RM 20.25 per 100 GB |
| **Internet Egress (AWS to On-Prem)** | Standard Egress ($0.09 – $0.12/GB after the shared 100 GB/mo internet data transfer allowance across AWS services/regions is exhausted) | ~$9.00 – $12.00 per 100 GB above shared allowance | ~RM 40.50 – RM 54.00 per 100 GB above shared allowance |
| **Total Baseline (Excluding Bandwidth)** | Fixed gateway + IP charge | **~$36.50 / month** | **~RM 164.25 / month** |

*Note on Direct EC2 Egress:* If your AWS application already resides in a public subnet with its own public IPv4, you eliminate the NAT Gateway cost, incurring only the IPv4 hourly charge (~$3.65 / month or ~RM 16.43 / month) and egress bandwidth.

---

## Technical Recommendation

| Assessment Metric | Option 1: Site-to-Site VPN | Option 2: Public Fusio Gateway |
| --- | --- | --- |
| **Security Surface** | High (Private IP, removes direct public exposure of on-premises API) | Moderate (Public edge, relies on WAF & IP allowlists) |
| **Compliance Readiness** | Native fit for sovereign/restricted data requiring strict routing rules | Requires penetration testing & rigorous auditing |
| **AWS Fixed Baseline Cost** | ~$43.80 / month (~RM 197.10 / month) | ~$36.50 / month (~RM 164.25 / month, or ~$3.65 if no NAT GW) |
| **Implementation Complexity** | Medium (IPsec/routing configuration) | Low (Application level + HTTPS) |

### Verdict & Best Practice

Given that on-premises enterprise data is explicitly classified as **sensitive and restricted from direct public cloud exposure**, **Option 1 (Site-to-Site VPN)** is the technically superior architectural choice.

The fixed monthly baseline for managed AWS Site-to-Site VPN including its two public IPv4 tunnel endpoints is **~$43.80/month** (~RM 197.10/month), compared to an AWS NAT Gateway at **~$36.50/month** (~RM 164.25/month). While the VPN requires maintaining an internet-routable customer gateway endpoint and perimeter firewall rules for IPsec traffic, it removes direct public exposure of your internal on-premises API and database nodes.

### Recommended Hybrid Topology: Option 1 + Fusio in Tandem

If Fusio is preferred for API lifecycle governance, payload transformation, or rate limiting, deploy **Option 1 + Fusio in tandem**: place Fusio on your on-premises node, but route requests strictly across the private IPsec tunnel rather than exposing it over a public IP.

---

## Notice & Disclaimer

This technical guide and architectural comparison are based on baseline specifications and current AWS pricing models for the `ap-southeast-5` (Malaysia) region as of August 2026. Actual bandwidth and data processing charges will vary depending on operational request volumes and payload sizes. This document is provided for architectural planning, educational, and technical evaluation purposes.

---

Copyright © 2005 - 2026 Harisfazillah Jamel, GNU General Public License v3.0.
Dedicated to linuxmalaysia.com knowledge collection.
