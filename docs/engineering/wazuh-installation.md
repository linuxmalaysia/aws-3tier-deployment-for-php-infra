---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "Wazuh SIEM & XDR Deployment Guide: AWS Cloud, On-Premises AlmaLinux 10 & WSL2 Demo"
timestamp: "2026-08-13T10:00:00+08:00"
topics: ["wazuh", "siem", "xdr", "aws", "almalinux10", "wsl2", "podman", "security"]
---

**[SECURITY & COMPLIANCE]**

# Wazuh SIEM & XDR Deployment Guide: AWS Cloud, On-Premises AlmaLinux 10 & WSL2 Demo

Wazuh is an enterprise-grade, open-source security platform delivering unified Extended Detection and Response (XDR) and Security Information and Event Management (SIEM) capabilities. It monitors endpoints, cloud services, and containerized workloads, analyzing security events in real-time to detect threats, system misconfigurations, and compliance violations.

This guide provides an end-to-end operational blueprint for deploying Wazuh across three target environments:
1. **On Cloud (AWS):** Standalone production and staging deployments in **AWS Asia Pacific (Malaysia) `ap-southeast-5`** on Graviton (ARM64) with full USD/MYR financial breakdowns.
2. **On-Premises (AlmaLinux 10):** Production-grade enterprise deployment on physical or virtualized AlmaLinux 10 infrastructure using native packages or Podman systemd Quadlets.
3. **WSL2 Windows 11 Demo Environment:** Local developer laptop setup running AlmaLinux 10 inside WSL2 with Podman for demonstration, testing, and security rule evaluation.

---

## 🏛️ 1. Wazuh Architecture & Sizing Guidelines

The Wazuh central platform comprises three main components:
1. **Wazuh Indexer:** A highly scalable, full-text search engine based on OpenSearch that indexes, stores, and correlates alerts received from the server.
2. **Wazuh Server:** The management core that collects, analyzes, and evaluates telemetry data from agents using decryption, parsing, and rule-matching engines.
3. **Wazuh Dashboard:** The web user interface for visualizing alerts, managing agent deployments, conducting threat hunting, and executing RBAC configuration.

### Hardware Sizing Guidelines

System resource utilization correlates directly with Event Ingestion Rates (Events Per Second - EPS) and total active agents:

| Deployment Tier | Active Agents | Target EPS | Recommended Hardware | Minimum Feasible Hardware |
| :--- | :--- | :--- | :--- | :--- |
| **Development / Demo (WSL2)** | 1–15 | < 100 EPS | 2 vCPUs, 4 GiB RAM, 30 GB Disk | 2 vCPUs, 4 GiB RAM (JVM tuned) |
| **Light Production / Branch** | 1–35 | 100–500 EPS | 2 vCPUs, 8 GiB RAM, 100 GB SSD | 2 vCPUs, 4 GiB RAM |
| **Standard Enterprise** | 1–100 | 500–2,000 EPS | 4 vCPUs, 8 GiB RAM, 200 GB SSD | 4 vCPUs, 8 GiB RAM |
| **High Throughput Cluster** | 100–1,000+ | > 2,000 EPS | Multi-node Indexer/Server Cluster | Dedicated multi-node deployment |

---

## 💸 2. On Cloud Plan: AWS Malaysia (`ap-southeast-5`)

Deploying Wazuh as a standalone instance isolates security management traffic from general application auto-scaling groups while optimizing monthly cloud expenditure.

### Cost Breakdown Matrix (USD & MYR)

Exchange Rate Baseline: **1 USD ≈ 4.50 MYR**. Estimates assume On-Demand usage over ~730 monthly hours in `ap-southeast-5` compared against US East (`us-east-1`).

| Cost Category | Option A: Dev / Demo (Malaysia `ap-southeast-5`) | Option B: Light Prod (Malaysia `ap-southeast-5`) | Option C: Global Baseline (US East `us-east-1`) | Option D: Official AMI (Malaysia `ap-southeast-5`) |
| :--- | :--- | :--- | :--- | :--- |
| **Instance Type** | `t4g.medium` (ARM64) | `t4g.large` (ARM64) | `t3.medium` (x86_64) | `c5a.xlarge` (x86_64) |
| **vCPU / Memory** | 2 vCPUs / 4 GiB RAM | 2 vCPUs / 8 GiB RAM | 2 vCPUs / 4 GiB RAM | 4 vCPUs / 8 GiB RAM |
| **EC2 Compute** | $24.53 / RM 110.39 | $49.06 / RM 220.77 | $30.37 / RM 136.67 | $136.51 / RM 614.30 |
| **gp3 Storage** | $4.00 / RM 18.00 (50GB) | $8.00 / RM 36.00 (100GB) | $4.00 / RM 18.00 (50GB) | $8.00 / RM 36.00 (100GB) |
| **Public IPv4** | $3.65 / RM 16.43 | $3.65 / RM 16.43 | $3.65 / RM 16.43 | $3.65 / RM 16.43 |
| **AWS Backup** | $2.50 / RM 11.25 | $5.00 / RM 22.50 | $2.50 / RM 11.25 | $5.00 / RM 22.50 |
| **TOTAL (Monthly)** | **$34.68 / RM 156.07** | **$65.71 / RM 295.70** | **$40.52 / RM 182.35** | **$153.16 / RM 689.23** |

*Note: Selecting AWS Graviton (`t4g.large`, Option B) provides superior performance per dollar and saves over **57%** compared to launching the pre-built x86 AWS Marketplace AMI (`c5a.xlarge`, Option D).*

### AWS Security Group Rules

Configure ingress traffic restrictions on the standalone Wazuh security group:

| Port | Protocol | Source | Purpose |
| :--- | :--- | :--- | :--- |
| `22` | TCP | Admin Office IP / Jumphost | Secure SSH Administration |
| `443` | TCP | Management VPN / Whitelisted IP | Wazuh Dashboard Web Access |
| `1514` | TCP | Agent Subnets / Monitored Hosts | Wazuh Agent Data Communication |
| `1515` | TCP | Agent Subnets / Monitored Hosts | Wazuh Agent Enrollment Service |
| `55000` | TCP | Management API Clients | Wazuh RESTful API Access |

### Cloud Installation Execution (Clean OS + Assistant)

```bash
# SSH to the standalone Graviton instance
ssh -i "your-key.pem" ubuntu@<YOUR_WAZUH_EIP>

# Elevate to root
sudo su -

# Download installer script
curl -sO https://packages.wazuh.com/4.x/wazuh-install.sh

# Run All-in-One automated installation
bash wazuh-install.sh -a

# Note: On 4 GiB RAM instances (t4g.medium), bypass hardware check with -i:
# bash wazuh-install.sh -a -i
```

---

## 🏢 3. On-Premises Plan: AlmaLinux 10

For air-gapped data centers or enterprise on-premises environments running **AlmaLinux 10** (RHEL 10 derivative), Wazuh can be deployed using native RPM packages or containerized using Podman.

### Step 1: System Kernel & Performance Tuning

Elasticsearch/OpenSearch indexers require increased memory map limits and file descriptor boundaries.

Create `/etc/sysctl.d/99-wazuh.conf`:
```ini
vm.max_map_count=262144
fs.file-max=655360
```

Apply settings immediately:
```bash
sudo sysctl -p /etc/sysctl.d/99-wazuh.conf
```

Set security limits in `/etc/security/limits.d/wazuh.conf`:
```ini
wazuh-indexer soft nofile 65536
wazuh-indexer hard nofile 65536
wazuh-indexer soft nproc 4096
wazuh-indexer hard nproc 4096
```

### Step 2: Configure Firewall (`firewalld`) on AlmaLinux 10

```bash
# Enable required ports in firewalld
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=1514/tcp
sudo firewall-cmd --permanent --add-port=1515/tcp
sudo firewall-cmd --permanent --add-port=55000/tcp

# Reload firewall configuration
sudo firewall-cmd --reload
```

### Step 3: Install Wazuh Repository & Packages

```bash
# Import GPG key
sudo rpm --import https://packages.wazuh.com/key/GPG-KEY-WAZUH

# Add Wazuh YUM repository
sudo tee /etc/yum.repos.d/wazuh.repo << 'EOF'
[wazuh]
name=Wazuh repository
baseurl=https://packages.wazuh.com/4.x/yum/
gpgcheck=1
gpgkey=https://packages.wazuh.com/key/GPG-KEY-WAZUH
enabled=1
protect=1
metadata_expire=1d
EOF

# Execute All-in-One installation via assistant script
curl -sO https://packages.wazuh.com/4.x/wazuh-install.sh
sudo bash wazuh-install.sh -a
```

---

## 💻 4. WSL2 Windows 11 Plan: AlmaLinux 10 Demo Environment

To demonstrate Wazuh capabilities locally on a developer laptop without dedicated cloud infrastructure, run an AlmaLinux 10 environment inside Windows Subsystem for Linux (WSL2) utilizing **Podman** and **Podman Compose**.

### Step 1: Windows 11 Resource Allocation (`.wslconfig`)

Create or update `%USERPROFILE%\.wslconfig` in Windows 11 to ensure WSL2 has sufficient RAM and CPU cores:

```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
localhostForwarding=true
```

Restart WSL2 from PowerShell:
```powershell
wsl --shutdown
```

### Step 2: Install AlmaLinux 10 in WSL2

In PowerShell:
```powershell
# Install AlmaLinux-10 distribution
wsl --install AlmaLinux-10

# Launch AlmaLinux-10
wsl -d AlmaLinux-10
```

### Step 3: Kernel Tuning inside WSL2 (Critical)

Inside the AlmaLinux 10 WSL2 terminal:
```bash
# Check current virtual memory limit
sysctl vm.max_map_count

# Apply temporary setting
sudo sysctl -w vm.max_map_count=262144

# Persist across WSL2 sessions
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

### Step 4: Install Podman & Podman Compose

```bash
# Update system and install Podman tools
sudo dnf install -y podman podman-compose git

# Enable Podman socket for current user
systemctl --user enable --now podman.socket
```

### Step 5: Launch Containerized Wazuh Stack

```bash
# Clone the official Wazuh Docker/Podman repository
git clone https://github.com/wazuh/wazuh-docker.git -b v4.7.2 --single-branch
cd wazuh-docker/single-node

# Generate TLS certificates for local environment
docker-compose run --rm generator

# Launch stack using podman-compose
podman-compose up -d
```

### Step 6: Verify Stack & Access Dashboard

Verify running containers:
```bash
podman ps
```

Access the dashboard from your Windows 11 web browser:
- **URL:** `https://localhost:443` or `https://127.0.0.1:443`
- **Username:** `admin`
- **Password:** `SecretPassword1!` (or custom password defined in `docker-compose.yml`)

---

## 📡 5. Agent Enrollment (Linux & Windows)

Once the Wazuh server is operational (in AWS, On-Premises, or WSL2), enroll target endpoints to start collecting telemetry.

### Linux Target (Debian / Ubuntu):
```bash
wget https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.7.2-1_amd64.deb
sudo WAZUH_MANAGER='<YOUR_WAZUH_SERVER_IP>' dpkg -i wazuh-agent_4.7.2-1_amd64.deb
sudo systemctl daemon-reload
sudo systemctl enable --now wazuh-agent
```

### Linux Target (AlmaLinux / RHEL / Rocky):
```bash
sudo WAZUH_MANAGER='<YOUR_WAZUH_SERVER_IP>' dnf install -y https://packages.wazuh.com/4.x/yum/wazuh-agent-4.7.2-1.x86_64.rpm
sudo systemctl daemon-reload
sudo systemctl enable --now wazuh-agent
```

### Windows Target (PowerShell):
```powershell
Invoke-WebRequest -Uri https://packages.wazuh.com/4.x/windows/wazuh-agent-4.7.2-1.msi -OutFile ${env:tmp}\wazuh-agent.msi
msiexec.exe /i ${env:tmp}\wazuh-agent.msi /q WAZUH_MANAGER="<YOUR_WAZUH_SERVER_IP>"
Start-Service -Name "Wazuh"
```

---

## 🔒 6. Security Hardening & Operational Verification

1. **Password Rotation:** Rotate default administrator passwords immediately post-installation using `/usr/share/wazuh-indexer/plugins/opensearch-security/tools/wazuh-passwords-tool.sh`.
2. **Network Access Control:** Whitelist ingress access for ports `443` and `22` strictly to office public IP ranges or VPN gateways. Never expose management ports publicly (`0.0.0.0/0`).
3. **Automated Backups:** On AWS, attach AWS Backup policies targeting the 100 GB `gp3` storage volume for daily snapshot retention.

---

*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-13*
