---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "AWS CLI Installation and Infrastructure Discovery Guide"
timestamp: "2026-08-05T22:20:36+08:00"
topics: ["aws", "3-tier", "automation", "security"]
---

# AWS CLI Installation and Infrastructure Discovery Guide

**[DEVOPS EXECUTION]**

This document provides a comprehensive, production-grade guide for installing, configuring, and utilizing version 2 of the **AWS Command Line Interface (AWS CLI)** to discover and query our secure, highly-available 3-tier PHP & Web infrastructure inside the **AWS Asia Pacific (Malaysia) region (`ap-southeast-5`)**.

By following this guide, systems engineers and administrators can efficiently audit security groups, auto-scaling statuses, database parameters, Valkey cache nodes, and application load balancer targets without relying solely on the AWS Management Console.

---

## 1. Prerequisites

Before installing the AWS CLI, ensure you have the following ready:
* **AWS Account Access:** An active AWS IAM User or Role with read-only/audit permissions (or administrator permissions for deployment). Do not use root account credentials.
* **Network Connectivity:** A secure connection to the internet. If querying internal resources (like RDS or private Valkey clusters), make sure you are routed via the whitelisted Jumphost/Bastion or connected to our corporate network/VPN.
* **Supported Linux Distributions:** This guide covers Debian/Ubuntu-derived and RHEL-derived OS installations, as well as MacOS and Windows.

---

## 2. Installing or Updating to the Latest AWS CLI Version 2

We natively use **AWS CLI version 2**, which supports modern credential helpers, SSO integration, and interactive features.

### A. Linux (Ubuntu, Debian, RHEL, Rocky Linux, AlmaLinux)
To install the AWS CLI version 2 on Linux, use the official pre-built zipped bundle:

```bash
# Update local packages and install prerequisites
sudo apt-get update && sudo apt-get install -y curl unzip  # Debian/Ubuntu
# or
sudo dnf install -y curl unzip                             # RHEL/Rocky/Alma

# Download the official installation bundle
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Unzip the installer package
unzip awscliv2.zip

# Run the install command
sudo ./aws/install

# Verify the installation
aws --version
```

To update an existing installation on Linux, use the `--update` flag:
```bash
sudo ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli --update
```

### B. macOS
Using the official pkg installer:
```bash
# Download the macOS pkg package
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"

# Install the pkg
sudo installer -pkg AWSCLIV2.pkg -target /

# Verify the installation
aws --version
```

### C. Windows (PowerShell)
Using the MSI installer in Windows:
```powershell
# Download and install via MSI
Start-Process msiexec.exe -ArgumentList '/i https://awscli.amazonaws.com/AWSCLIV2.msi /qn' -Wait

# Verify the installation (open a new PowerShell session)
aws --version
```

### D. Alternative: Running via Docker
If you prefer not to install the CLI directly on your host, you can run the official Amazon ECR Public Docker image:
```bash
docker run --rm -it -v ~/.aws:/root/.aws public.ecr.aws/aws-cli/aws-cli:latest --version
```

---

## 3. Configuring the AWS CLI

Once installed, you must configure your local environment with security credentials, default regions, and output formats.

### A. Quick Setup (IAM User Access Keys)
If using traditional long-lived access keys, run:
```bash
aws configure
```
You will be prompted for:
* **AWS Access Key ID:** `AKIAIOSFODNN7EXAMPLE`
* **AWS Secret Access Key:** `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
* **Default region name:** `ap-southeast-5` (natively targeting our Malaysia Region)
* **Default output format:** `json` (or `yaml` / `table` for readability)

### B. Setup via AWS IAM Identity Center (Recommended)
For single sign-on (SSO) and temporary credentials:
```bash
aws configure sso
```
Follow the interactive prompts to authenticate via your web browser.

---

## 4. Querying and Discovering Our 3-Tier Infrastructure

Once configured, use the following target commands to gather critical architectural information. Ensure you explicitly query the primary region (`--region ap-southeast-5`).

### A. Core Networking & VPC Discovery
To discover our custom VPC, public/private subnets, and Route Tables:

```bash
# 1. List our 3-Tier VPC
aws ec2 describe-vpcs \
  --region ap-southeast-5 \
  --filters "Name=tag:Project,Values=aws-3tier-php" \
  --query "Vpcs[*].{VpcId:VpcId,CidrBlock:CidrBlock,Name:Tags[?Key=='Name'].Value|[0]}" \
  --output table

# 2. Query all subnets under the VPC
aws ec2 describe-subnets \
  --region ap-southeast-5 \
  --filters "Name=vpc-id,Values=vpc-xxxxxx" \
  --query "Subnets[*].{SubnetId:SubnetId,CidrBlock:CidrBlock,AZ:AvailabilityZone,Name:Tags[?Key=='Name'].Value|[0]}" \
  --output table

# 3. View Internet Gateways and NAT Gateways
aws ec2 describe-nat-gateways \
  --region ap-southeast-5 \
  --query "NatGateways[*].{NatGatewayId:NatGatewayId,SubnetId:SubnetId,State:State}" \
  --output table
```

### B. Security Groups & Zero-Trust Firewall Audit
Verify that our network microsegmentation rules are correctly enforced:

```bash
# 1. Discover all security groups related to our project
aws ec2 describe-security-groups \
  --region ap-southeast-5 \
  --filters "Name=tag:Project,Values=aws-3tier-php" \
  --query "SecurityGroups[*].{GroupId:GroupId,GroupName:GroupName,Description:Description}" \
  --output table

# 2. Audit ingress rules of our Application instances to ensure Zero-Trust ALB-only access
aws ec2 describe-security-groups \
  --region ap-southeast-5 \
  --group-ids sg-xxxxxx \
  --query "SecurityGroups[0].IpPermissions" \
  --output json
```

### C. Compute Layer & Auto Scaling Groups (ASG)
Monitor and inspect active compute nodes running Nginx & PHP-FPM:

```bash
# 1. List our Auto Scaling Groups
aws autoscaling describe-auto-scaling-groups \
  --region ap-southeast-5 \
  --query "AutoScalingGroups[*].{ASGName:AutoScalingGroupName,Min:MinSize,Max:MaxSize,Desired:DesiredCapacity,LaunchTemplate:LaunchTemplate.LaunchTemplateName}" \
  --output table

# 2. Find currently running EC2 instances launched by the ASG
aws ec2 describe-instances \
  --region ap-southeast-5 \
  --filters "Name=tag:aws:autoscaling:groupName,Values=main-portal-ec2-my-asg" "Name=instance-state-name,Values=running" \
  --query "Reservations[*].Instances[*].{InstanceId:InstanceId,PrivateIp:PrivateIpAddress,LaunchTime:LaunchTime}" \
  --output table
```

### D. Application Load Balancer (ALB) and Target Group Health
Check the load balancing tier and the health statuses of downstream compute targets:

```bash
# 1. Describe application load balancers
aws elbv2 describe-load-balancers \
  --region ap-southeast-5 \
  --query "LoadBalancers[*].{ALBName:LoadBalancerName,DNSName:DNSName,State:State.Code}" \
  --output table

# 2. Check the health of targets in our Target Group
aws elbv2 describe-target-health \
  --region ap-southeast-5 \
  --target-group-arn arn:aws:elasticloadbalancing:ap-southeast-5:123456789012:targetgroup/my-tg/xxxxxx \
  --query "TargetHealthDescriptions[*].{TargetId:Target.Id,Port:Target.Port,HealthStatus:TargetHealth.State}" \
  --output table
```

### E. RDS MariaDB Database Cluster Configuration
Confirm the performance parameters and storage scaling configurations of our Multi-AZ DB tier:

```bash
# 1. View the RDS instances
aws rds describe-db-instances \
  --region ap-southeast-5 \
  --query "DBInstances[*].{DBInstanceIdentifier:DBInstanceIdentifier,Engine:Engine,EngineVersion:EngineVersion,Class:DBInstanceClass,Status:DBInstanceStatus}" \
  --output table

# 2. Verify Multi-AZ is enabled and check backup windows
aws rds describe-db-instances \
  --region ap-southeast-5 \
  --db-instance-identifier secure-app-db \
  --query "DBInstances[0].{MultiAZ:MultiAZ,BackupRetentionPeriod:BackupRetentionPeriod,PreferredBackupWindow:PreferredBackupWindow}" \
  --output json
```

### F. ElastiCache Valkey Session Cluster Status
Inspect our horizontal Valkey caching instances deployed in the database subnet tier:

```bash
# 1. Discover Valkey replication groups
aws elasticache describe-replication-groups \
  --region ap-southeast-5 \
  --query "ReplicationGroups[*].{ReplicationGroupId:ReplicationGroupId,Status:Status,NodeGroups:NodeGroups[0].NodeGroupMembers[*].CacheClusterId}" \
  --output json

# 2. Describe Cache Clusters and cache engine parameters
aws elasticache describe-cache-clusters \
  --region ap-southeast-5 \
  --query "CacheClusters[*].{CacheClusterId:CacheClusterId,Engine:Engine,EngineVersion:EngineVersion,NodeStatus:CacheClusterStatus}" \
  --output table
```

---

## 5. Troubleshooting AWS CLI Configuration Errors

If you encounter issues while running AWS CLI commands, consult these common fixes:

### A. "ExpiredToken" or "SignatureDoesNotMatch"
* **Root Cause:** Your local IAM credentials have expired or are incorrect.
* **Fix:** Re-authenticate via `aws configure` or `aws sso login` to refresh your access session tokens.

### B. "Could not connect to the endpoint URL"
* **Root Cause:** The default region is set incorrectly, or your connection is blocked by a local proxy, firewall, or DNS misconfiguration.
* **Fix:** Ensure `--region ap-southeast-5` is specified. If you are querying internal RDS endpoints, make sure you are routing requests from the whitelisted cyberjaya CIDR ranges or via our secure Bastion tunnel.

### C. "AccessDenied" or "UnauthorizedOperation"
* **Root Cause:** Your IAM user or role lacks the necessary AWS permissions to query these specific resources (e.g., missing `ec2:DescribeVpcs` or `rds:DescribeDBInstances`).
* **Fix:** Attach the standard AWS-managed `ReadOnlyAccess` policy or a customized least-privilege auditing IAM policy to your identity.
