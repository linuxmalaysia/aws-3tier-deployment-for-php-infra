---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "Auto Scaling Groups (ASGs) & Separation of Concerns"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier", "compute", "autoscaling"]
---

**[DEVOPS EXECUTION]**

# Auto Scaling Groups (ASGs) & Separation of Concerns

In a modern cloud-native architecture, managing complex applications requires balancing scalability, security, cost, and operational maintenance. This document explores the architectural rationale for using **Separation of Concerns (SoC)** via distinct Auto Scaling Groups (ASGs) and provides an exhaustive guide on how to handle shared storage (**Amazon S3**, **Amazon EFS**, or both) to enable seamless, stateless autoscaling for PHP CodeIgniter deployments.

---

## 1. Separation of Concerns (SoC) via Combined ASG Web & Application Tiers


Rather than deploying separate physical fleets of EC2 instances for Nginx and PHP-FPM (which introduces network latency, increases the NAT/ALB budget, and complicates configuration propagation), this architecture leverages a **single combined ASG and Target Group** where each instance hosts both Nginx and PHP-FPM.

By running both services locally on each auto-scaled instance, we maintain proper separation of concerns through independent configuration layers while maximizing efficiency:

### Architectural Advantages of the Combined ASG Model

1. **Zero-Latency FastCGI Sockets:**
   - Nginx communicates with PHP-FPM over high-speed local UNIX domain sockets (`unix:/run/php/php-fpm.sock` or `unix:/run/php-fpm/www.sock`). This bypasses the TCP network stack completely, avoiding network serialization and reducing transit latency to absolute zero.
2. **Coordinated Elastic Scaling:**
   - Web proxying and PHP execution scale out synchronously. As incoming HTTP traffic surges, the ASG boots instances where both the Nginx request buffering capacity and the PHP-FPM compute execution capabilities increase in a 1:1 ratio.
3. **Internal Process Isolation:**
   - If a memory leak or heavy processing script crashes an individual PHP-FPM worker process, Nginx's master process remains completely operational, serving static assets natively and returning a standard, graceful 502/503 page directly to the load balancer with zero delay.
4. **Unified Deployment and Rolling Updates:**
   - Updating the CodeIgniter codebase is simplified. Developers build a single golden AMI containing both the updated PHP scripts and the Nginx virtual host templates. Running an Instance Refresh on the combined ASG executes a seamless, rolling update across the entire cluster with zero downtime.

---

## 2. Statelessness: The Core Prerequisite of ASGs

The foundational rule of Auto Scaling is **statelessness**.
Because ASG instances are automatically launched, terminated, and replaced during scaling events (scale-out, scale-in, or health-check replacements), **no persistent state should ever reside directly on an instance's local root disk (EBS).**

If an application writes files (e.g., user profile pictures, uploaded documents, or session state) directly to the local filesystem of an EC2 instance, those files will be:
- **Inaccessible** to other instances in the ASG (causing HTTP 404 errors when a load balancer routes subsequent requests to a different instance).
- **Permanently lost** when the specific instance scales in or gets replaced due to a failed health check.

To solve this, you must decouple your compute tier (ASG) from your storage and session tier. This brings us to the core decision: **Amazon S3, Amazon EFS, or Valkey/Redis session storage?**

---

## 3. Storage Guide: Amazon S3 vs. Amazon EFS

To handle data across auto-scaling instances, AWS offers two primary shared storage options. Understanding when to use each—or combining them in a hybrid layout—is critical to a high-performing architecture.

### Option A: Amazon S3 (Simple Storage Service)
Amazon S3 is a highly durable, virtually infinite, secure, and cost-effective **object storage service** designed for cloud-native applications.

* **How it works:** Files (objects) are accessed and manipulated directly via HTTP/HTTPS REST API calls (typically using AWS SDKs or the AWS CLI) rather than traditional filesystem commands (like `open()`, `write()`, or `seek()`).
* **Best suited for:**
  - Modern, stateless, cloud-native applications.
  - User-facing uploads (e.g., images, PDFs, videos, user profiles).
  - Storing raw static assets, application logs, and database snapshots.
* **Pros:**
  - **Incredible Scalability:** Handles millions of concurrent requests effortlessly.
  - **Unmatched Durability:** Designed for 99.999999999% (11 9s) of durability.
  - **Low Cost:** Very inexpensive compared to standard filesystems ($0.023 per GB/month for standard).
  - **Global Delivery Integration:** Seamlessly integrates with Amazon CloudFront CDN for global low-latency asset delivery.
* **Cons:**
  - **Non-POSIX Compliant:** You cannot "mount" S3 as a traditional directory and perform standard file writes/appends in legacy code without utility layers (like Mountpoint for Amazon S3).



### Option B: Amazon EFS (Elastic File System)


Amazon EFS is a fully-managed, serverless, POSIX-compliant **network filesystem (NFSv4)** designed to be mounted concurrently by hundreds of EC2 instances across multiple Availability Zones.

* **How it works:** EFS is mounted over the network (port 2049) to a local directory on your EC2 instances. To the operating system, it looks and behaves exactly like a standard local directory.
* **Best suited for:**
  - CodeIgniter applications requiring a shared write/read directory across auto-scaled servers (e.g., sharing a static legacy document store or cache folder).
  - Shared directories requiring low-latency read-write concurrency across multiple compute instances simultaneously.
* **Pros:**
  - **POSIX Compliant:** Supports full directory structures, file locking, permissions (UID/GID), and standard file system tools.
  - **Elastic Capacity:** Scales automatically up to petabytes without manual provisioning; you only pay for what you use.
  - **Multi-AZ Availability:** Built-in replication across multiple AZs.
* **Cons:**
  - **Higher Cost:** Significantly more expensive than S3 ($0.30 per GB/month for standard SSD storage).

---

## 4. Architectural Comparison Table

| Feature | Amazon S3 (Object Storage) | Amazon EFS (Network File System) |
| :--- | :--- | :--- |
| **Primary Protocol** | HTTP / HTTPS (REST API) | NFSv4 (TCP Port 2049) |
| **POSIX Support** | No (requires custom SDK or client) | Yes (standard directory, file permissions, file locking) |
| **Scalability** | Virtually infinite; high concurrent request throughput | Automatic capacity scaling; scales throughput with size |
| **Typical Ingress Cost** | Free inbound; $0.023/GB/month (Standard) | $0.30/GB/month (Standard Storage) |
| **Access Latency** | Tens of milliseconds | Single-digit milliseconds |
| **Direct Web Serving** | Yes (via CloudFront / S3 Public endpoints) | No (must traverse an EC2 instance/web server) |
| **Mounting on EC2** | Direct SDK integration preferred | Standard Linux `mount` command via `amazon-efs-utils` |
| **Best AWS ASG Case** | Storing user uploads, large datasets, and logs | Shared assets and media folders, shared legacy configurations |

---


## 5. Session Statelessness: Amazon ElastiCache for Valkey


While file storage is resolved using S3 or EFS, a PHP application like CodeIgniter must also store **user session states** (login sessions, carts, transient flash variables) statelessly.

### Why Valkey/Redis for Sessions?
By default, PHP and CodeIgniter write sessions to local files on the server (e.g., `/var/lib/php/sessions`). In an ASG, if a user's next HTTP request gets routed to a different instance by the ALB, their session file will be missing, forcing them to log in again.

By changing CodeIgniter's session handler to use **Valkey** (via Amazon ElastiCache):
1. **Centralized Store:** All EC2 instances connect to the same Valkey endpoint over the private subnet on port `6379`.
2. **Sub-millisecond Latency:** Valkey is an in-memory database, meaning session reads and writes are faster than filesystem-based lookups.
3. **No Local State:** If an EC2 instance is terminated and replaced, the user's session is completely unaffected.

---

## 6. Implementation and Cost-Optimization Best Practices

When leveraging S3, EFS, and Valkey alongside ASGs, implement these practices to minimize operational costs:

1. **EFS Lifecycle Management:** Set EFS Lifecycle policies to automatically move files that haven't been accessed in 14 or 30 days to **EFS Infrequent Access (IA)**.
2. **S3 Intelligent-Tiering:** Enable S3 Intelligent-Tiering on your buckets. This automatically moves files between frequent and infrequent access tiers based on real-time usage patterns.
3. **Valkey Caching:** Use Valkey not only for sessions but also for CodeIgniter 4 database query caching, significantly reducing the query load and sizing requirement of your RDS instance.
   - **Cache Driver:** Configure the CI4 cache handler to use the `Redis` driver pointing directly to the Valkey cluster endpoint.
   - **Key Strategy:** Cache keys are generated deterministically using MD5 hashes of the normalized SQL query string with a prefix (e.g., `ci4_db_query_`). To make invalidation implementable, write operations maintain a Redis Set for each database table (e.g., `table_keys:users`), mapping tables to all associated query cache keys.
   - **Time-to-Live (TTL):** Enforce a default TTL of `300` seconds on all cached database queries to prevent stale data.
   - **Invalidation Behavior:** Any write operations (`INSERT`, `UPDATE`, `DELETE`) on a target table retrieve the list of associated cache keys from the table-to-key index Set, pipeline the deletion of those specific keys, and then clear the Set. This prevents stale results without implying that the MD5-only key itself can identify affected tables. If table-to-key tracking is disabled, a full-namespace invalidation (flushing all keys with the `ci4_db_query_*` prefix) is performed, which requires performance testing under load to measure the CPU/network scan and delete cost.
   - **RDS Failover & Sizing Resiliency:** To avoid cascading failures, the primary RDS database sizing must be provisioned to safely absorb peak transaction volume during cache misses and Valkey node failures. Under-sizing RDS based on optimistic cache assumptions is strictly prohibited; rigorous load testing under simulated cache-miss and Valkey failure conditions is required before any database capacity down-scaling can be authorized.
