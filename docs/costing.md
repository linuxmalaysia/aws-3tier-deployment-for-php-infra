---
layout: default
okf_version: "0.1"
type: Technical Reference Guide
title: "AWS Costing Optimization Guide"
timestamp: 2026-08-05T22:20:36+08:00
topics: [aws, 3-tier, finops, costing]
---

# AWS Secure 3-Tier Architecture Cost Analysis

This document provides a highly granular, transparent, and comprehensive breakdown of the monthly operating costs associated with deploying our **PHP CodeIgniter secure 3-Tier Web Application** on AWS in the **Asia Pacific (Malaysia) Region (`ap-southeast-5`)**.

All estimates are calculated in **USD** and converted to **Malaysian Ringgit (MYR)** assuming a stable reference conversion rate of **1 USD = 4.50 MYR**.

---

## The Economics of Graviton (ARM64) in ap-southeast-5

A core driver of cost optimization in this architecture is the comprehensive utilization of **AWS Graviton (ARM64)** processors for all EC2 compute nodes and RDS databases:
1. **Compute Cost Reductions:** Graviton-based instances (e.g., `t4g.*` and `db.t4g.*`) are priced up to **20% lower** per hour than their Intel/AMD x86_64 equivalents on AWS in Malaysia.
2. **Performance Improvements:** Graviton instances deliver up to **40% better performance** per dollar for PHP-FPM, memory operations, and database engines.

---

## 1. Cost Scenario A: Baseline Cost-Optimized Plan

Designed specifically for staging, testing, development environments, or low-traffic public web services. This plan utilizes smaller Graviton instances and a single NAT gateway to minimize baseline spend while maintaining the secure 3-Tier network topology.

### Monthly Line-Item Breakdown (Baseline)

| Component / Layer | AWS Service Details | Sizing Spec | Hourly / Unit Rate | Monthly Cost (USD) | Monthly Cost (MYR) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Compute Tier (ASG)** | **Amazon EC2** (Nginx + PHP-FPM)<br><br>• 2x Auto Scaling Group instances spanning AZs `ap-southeast-5a/5b` | `t4g.micro` (ARM64)<br>2 vCPU, 1GB RAM | $0.0084 / hr / inst | $12.26 | RM 55.17 |
| **Compute SSD Storage** | **Amazon Elastic Block Store (EBS)**<br><br>• 2x 15GB gp3 Root Volumes for ASG nodes (30GB total) | gp3 storage volume | $0.08 / GB-month | $2.40 | RM 10.80 |
| **Database Tier (RDS)** | **Amazon Relational Database Service** (Multi-AZ)<br><br>• 1x Managed SQL Instance | `db.t4g.micro` (ARM64)<br>2 vCPU, 1GB RAM | $0.032 / hr (Multi-AZ) | $23.36 | RM 105.12 |
| **Database SSD Storage** | **Amazon RDS GP3 Volume** (Multi-AZ)<br><br>• Includes both primary and standby 20 GB volumes (40 GB total capacity)<br><br>• 100% backup storage included free | gp3 multi-AZ | $0.23 / GB-month | $9.20 | RM 41.40 |
| **Cache Store Tier** | **Amazon ElastiCache for Valkey**<br><br>• 1x Session Cache Node | `cache.t4g.micro` (ARM64)<br>2 vCPU, 0.5GB RAM | $0.0125 / hr | $9.13 | RM 41.09 |
| **Network Entrypoint** | **AWS WAFv2 Web ACL**<br><br>• 1x Web ACL + 3 Basic Core Rules<br><br>• ~1 Million Inbound Requests per month | Regional WAF Rules | $5.00 / ACL / mo<br><br>$1.00 / Rule / mo<br><br>$0.60 / M requests | $8.60 | RM 38.70 |
| **Load Balancing** | **Application Load Balancer (ALB)**<br><br>• 1x Public ALB routing to private compute ASG<br><br>• Assumes standard baseline connections and < 1 LCU processing charge | 1 ALB Instance | $0.0225 / hr base + LCU | $22.26 | RM 100.17 |
| **Bastion / Staging** | **Amazon EC2 Standalone Instances**<br><br>• 1x SSH Jumphost (Bastion)<br><br>• 1x PHP Standalone (AMI Baker / Staging) | 2x `t4g.micro`<br>15GB gp3 SSD each | $0.0084 / hr / inst<br><br>$0.08 / GB-mo | $12.26<br><br>$2.40 | RM 55.17<br><br>RM 10.80 |
| **Secure Egress** | **AWS NAT Gateway** (Single NAT Gateway)<br><br>• 1x NAT Gateway for private instances updates/egress<br><br>• 50 GB Data Transferred through NAT | AWS NAT Gateway | $0.045 / hr<br><br>$0.045 / GB | $32.85<br><br>$2.25 | RM 147.83<br><br>RM 10.13 |
| **Network Transit** | **AWS Egress Data Transfer**<br><br>• ~150 GB Outbound Internet Egress | Internet Egress | $0.09 / GB (after 100GB) | $4.50 | RM 20.25 |

### Scenario A Combined Total

* **Monthly Combined Total (USD):** **$141.47 USD / month**
* **Monthly Combined Total (MYR):** **RM 636.62 MYR / month**

---

## 2. Cost Scenario B: High-Performance Enterprise Plan

Spec'd specifically to fulfill the resource requirements of a highly available, robust production environment serving high traffic. This plan leverages multi-NAT redundancy, larger compute instances, and substantial storage options.

### Monthly Line-Item Breakdown (Enterprise Plan)

| Component / Layer | AWS Service Details | Sizing Spec | Hourly / Unit Rate | Monthly Cost (USD) | Monthly Cost (MYR) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Compute Tier (ASG)** | **Amazon EC2** (Nginx + PHP-FPM)<br><br>• 2x Auto Scaling Group instances spanning AZs `ap-southeast-5a/5b` | `t4g.medium` (ARM64)<br>2 vCPU, 4GB RAM | $0.0336 / hr / inst | $49.06 | RM 220.77 |
| **Compute SSD Storage** | **Amazon Elastic Block Store (EBS)**<br><br>• 2x 30GB gp3 Root Volumes for ASG nodes (60GB total) | gp3 storage volume | $0.08 / GB-month | $4.80 | RM 21.60 |
| **Database Tier (RDS)** | **Amazon Relational Database Service** (Multi-AZ)<br><br>• 1x Managed SQL Instance | `db.m6g.xlarge` (ARM64)<br>4 vCPU, 16GB RAM | $0.608 / hr (Multi-AZ) | $443.84 | RM 1,997.28 |
| **Database SSD Storage** | **Amazon RDS GP3 Volume** (Multi-AZ)<br><br>• Includes both primary and standby 100 GB volumes (200 GB total capacity)<br><br>• 100% backup storage included free | gp3 multi-AZ | $0.23 / GB-month | $46.00 | RM 207.00 |
| **Cache Store Tier** | **Amazon ElastiCache for Valkey**<br><br>• Valkey Replication Group (2x cache.t4g.medium nodes for Multi-AZ High Availability) | `cache.t4g.medium` (ARM64)<br>2 vCPU, 3.09GB RAM | $0.062 / hr / node | $90.52 | RM 407.34 |
| **Network Entrypoint** | **AWS WAFv2 Web ACL**<br><br>• 1x Web ACL + 3 Basic Core Rules<br><br>• ~5 Million Inbound Requests per month | Regional WAF Rules | $5.00 / ACL / mo<br><br>$1.00 / Rule / mo<br><br>$0.60 / M requests | $11.00 | RM 49.50 |
| **Load Balancing** | **Application Load Balancer (ALB)**<br><br>• 1x Public ALB routing to private compute ASG<br><br>• Assumes 2 LCU processing charge under typical production active connections | 1 ALB Instance | $0.0225 / hr base + LCU | $28.10 | RM 126.45 |
| **Bastion / Staging** | **Amazon EC2 Standalone Instances**<br><br>• 1x SSH Jumphost (Bastion)<br><br>• 1x PHP Standalone (AMI Baker / Staging) | 2x `t4g.medium`<br>30GB gp3 SSD each | $0.0336 / hr / inst<br><br>$0.08 / GB-mo | $49.06<br><br>$4.80 | RM 220.77<br><br>RM 21.60 |
| **Secure Egress** | **AWS NAT Gateway** (Multi-NAT Configuration)<br><br>• 2x NAT Gateways (one per AZ)<br><br>• ~500 GB Data Transferred through NAT | AWS NAT Gateway | 2x $0.045 / hr<br><br>$0.045 / GB | $65.70<br><br>$22.50 | RM 295.65<br><br>RM 101.25 |
| **Network Transit** | **AWS Egress Data Transfer**<br><br>• ~1 TB Outbound Internet Egress | Internet Egress | $0.09 / GB (after 100GB) | $83.16 | RM 374.22 |

### Scenario B Combined Total

* **Monthly Combined Total (USD):** **$898.54 USD / month**
* **Monthly Combined Total (MYR):** **RM 4,043.43 MYR / month**

---

## 3. Cost-Optimization Recommendations

To reduce monthly costs further, technical leadership can implement several structural strategies:

1. **RDS Reserved Instances (RI):** Purchasing a 1-year or 3-year Reserved Instance for your managed RDS database can yield up to a **30%–35% discount** on hourly DB compute charges.
2. **EC2 Instance Savings Plans:** Commit to a baseline compute usage to unlock up to **25% savings** across your ASG and Standalone EC2 instances.
3. **S3 Storage Lifecycle Policies:** Configure automatic transitions from S3 Standard to S3 Intelligent-Tiering to ensure infrequently accessed media uploads are stored at lower-cost tiers.
