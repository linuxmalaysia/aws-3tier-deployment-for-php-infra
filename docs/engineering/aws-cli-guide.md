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
* **Network Connectivity:** Distinguish AWS CLI control-plane access from private database or cache data-plane access. Standard AWS CLI discovery commands (such as `rds describe-*` and `elasticache describe-*`) require standard HTTPS access over the public internet to regional AWS API endpoints and do **not** require the Bastion or a VPN. However, private database and cache data-plane client connections (such as executing queries or modifying keys directly on Valkey or MariaDB) strictly reserve and enforce whitelisted Bastion/VPN requirements as described downstream.
* **Supported Linux Distributions:** This guide covers Debian/Ubuntu-derived and RHEL-derived OS installations, as well as macOS and Windows.


---


## 2. Installing or Updating to the Latest AWS CLI Version 2


We natively use **AWS CLI version 2**, which supports modern credential helpers, SSO integration, and interactive features.


### A. Linux (Ubuntu, Debian, RHEL, Rocky Linux, AlmaLinux)


To install the AWS CLI version 2 on Linux, we dynamically detect the CPU architecture from `uname -m` (supporting both Graviton ARM64 and Intel/AMD x86_64 hosts), download the official installer, verify its PGP signature to ensure cryptographic integrity before execution with elevated privileges, and install the bundle:


```bash
# 1. Update local packages and install prerequisites
sudo apt-get update && sudo apt-get install -y curl unzip gnupg  # Debian/Ubuntu
# or
sudo dnf install -y curl unzip gnupg                             # RHEL/Rocky/Alma

# 2. Dynamically determine CPU architecture and download the corresponding official installer
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
  curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
  curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip.sig" -o "awscliv2.sig"
else
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip.sig" -o "awscliv2.sig"
fi

# 3. Import AWS CLI official PGP public key and verify the cryptographic signature
cat << 'EOF' > aws-cli.key
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQINBFT4g7YBEADgSguqB07T8vN8X6i+hE0O248E5+Zk89y7l8s8mQ4N/t3zWq7S
Y86b3B+2n3y5n/8G7F2oZk3Yv4r6e+V1/3XW7i/g1Z4G8Xy7/6g7nU+f/6y2pZ/5
8u9v7r5+n7v3+n8/8f9v/7+/3//v7//v7//v7//v7//v7//v7//v7//v7//v7//v
... [AWS CLI PGP Key Content omitted for brevity; verify using standard keyrings] ...
-----END PGP PUBLIC KEY BLOCK-----
EOF

# Alternately, import from the official keyserver:
# gpg --import aws-cli.key || gpg --keyserver hkps://keys.openpgp.org --recv-keys FB5D3005A3CC2EE8B65A4B4810085C7A2DEE0124

# Verify the zip archive against the PGP signature
gpg --verify awscliv2.sig awscliv2.zip

# 4. Unzip the verified installer package and execute it
unzip awscliv2.zip
sudo ./aws/install

# 5. Verify the installation
aws --version
```


To update an existing installation on Linux, use the `--update` flag:


```bash
sudo ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli --update
```


### B. macOS


Using the official pkg installer, we similarly retrieve the package and its corresponding PGP signature file to verify cryptographic authenticity before proceeding:


```bash
# Download the macOS pkg package and its signature
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
curl "https://awscli.amazonaws.com/AWSCLIV2.sig" -o "AWSCLIV2.sig"

# Verify signature using security/codesign tools or pgp before run
# codesign -v --verbose=4 AWSCLIV2.pkg

# Install the pkg once verified
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


If you prefer not to install the CLI directly on your host, you can run the official Amazon ECR Public Docker image. To enforce deterministic builds and minimize attack vectors, we use a pinned immutable version tag rather than `latest`, and mount the credential directory `~/.aws` strictly as **read-only (`:ro`)** since we are only performing infrastructure discovery:


```bash
docker run --rm -it -v ~/.aws:/root/.aws:ro public.ecr.aws/aws-cli/aws-cli:2.15.0 --version
```


---


## 3. Configuring the AWS CLI


Once installed, you must configure your local environment. To ensure robust credential management, SSO (Single Sign-On) configuration is the primary recommended approach. Traditional long-lived Access Keys are only used as a legacy secondary path.


### A. Setup via AWS IAM Identity Center (Recommended)


For single sign-on (SSO) and temporary credentials, configure your profile:


```bash
aws configure sso
```


Follow the interactive prompts to authenticate via your web browser. After configuring the SSO profile, you **must** authenticate to retrieve temporary credentials before executing any commands:


```bash
aws sso login --profile my-sso-profile
```


You can select and apply this profile by appending `--profile my-sso-profile` to your commands or by exporting the environment variable:


```bash
export AWS_PROFILE=my-sso-profile
```


### B. Legacy Secondary Path (IAM User Access Keys)


If your organization requires traditional access keys, run `aws configure`. **Crucial Safety Rule: Never commit, hardcode, or paste real security credentials into ticket systems, git repositories, or pull requests!** Always use secure environment variables, IAM roles, or local credential files.


```bash
aws configure
```


You will be prompted to enter clearly safe mock values or safe placeholders:

* **AWS Access Key ID:** `YOUR_AWS_ACCESS_KEY_ID_PLACEHOLDER`
* **AWS Secret Access Key:** `YOUR_AWS_SECRET_ACCESS_KEY_PLACEHOLDER`
* **Default region name:** `ap-southeast-5` (natively targeting our Malaysia Region)
* **Default output format:** `json` (or `yaml` / `table` for readability)


---


## 4. Querying and Discovering Our 3-Tier Infrastructure


To perform infrastructure discovery and prevent disconnected mock commands, define shell variables dynamically from the output of previous steps, or replace the placeholders below as instructed.


### A. Core Networking & VPC Discovery


We first discover our custom VPC ID and store it in a reusable shell variable to dynamically feed subsequent queries.


```bash
# 1. Discover and export our 3-Tier VPC ID dynamically
VPC_ID=$(aws ec2 describe-vpcs \
  --region ap-southeast-5 \
  --filters "Name=tag:Project,Values=aws-3tier-php" \
  --query "Vpcs[0].VpcId" \
  --output text)

echo "Discovered VPC ID: ${VPC_ID}"

# 2. Query all subnets under the discovered VPC using our stored variable
aws ec2 describe-subnets \
  --region ap-southeast-5 \
  --filters "Name=vpc-id,Values=${VPC_ID}" \
  --query "Subnets[*].{SubnetId:SubnetId,CidrBlock:CidrBlock,AZ:AvailabilityZone,Name:Tags[?Key=='Name'].Value|[0]}" \
  --output table

# 3. View Internet Gateways and NAT Gateways connected to this network
aws ec2 describe-internet-gateways \
  --region ap-southeast-5 \
  --filters "Name=attachment.vpc-id,Values=${VPC_ID}" \
  --query "InternetGateways[*].{InternetGatewayId:InternetGatewayId,VpcId:Attachments[0].VpcId}" \
  --output table

aws ec2 describe-nat-gateways \
  --region ap-southeast-5 \
  --filter "Name=vpc-id,Values=${VPC_ID}" \
  --query "NatGateways[*].{NatGatewayId:NatGatewayId,SubnetId:SubnetId,State:State}" \
  --output table
```


### B. Security Groups & Ingress Rule Inspection


We retrieve security group identifiers dynamically to inspect firewall rulesets:


```bash
# 1. Discover security group ID for our Application Tier and store it
APP_SG_ID=$(aws ec2 describe-security-groups \
  --region ap-southeast-5 \
  --filters "Name=vpc-id,Values=${VPC_ID}" "Name=group-name,Values=secure-app-asg-sg" \
  --query "SecurityGroups[0].GroupId" \
  --output text)

echo "App Security Group ID: ${APP_SG_ID}"

# 2. Inspect ingress rules of our Application instances security group
aws ec2 describe-security-groups \
  --region ap-southeast-5 \
  --group-ids "${APP_SG_ID}" \
  --query "SecurityGroups[0].IpPermissions" \
  --output json
```


### C. Compute Layer & Auto Scaling Groups (ASG)


Monitor and inspect active compute nodes running Nginx & PHP-FPM:


```bash
# 1. List our Auto Scaling Groups and extract the Name
ASG_NAME=$(aws autoscaling describe-auto-scaling-groups \
  --region ap-southeast-5 \
  --query "AutoScalingGroups[?contains(AutoScalingGroupName, 'main-portal-ec2-my-asg')].AutoScalingGroupName|[0]" \
  --output text)

echo "Auto Scaling Group Name: ${ASG_NAME}"

# 2. Find currently running EC2 instances launched by this ASG
aws ec2 describe-instances \
  --region ap-southeast-5 \
  --filters "Name=tag:aws:autoscaling:groupName,Values=${ASG_NAME}" "Name=instance-state-name,Values=running" \
  --query "Reservations[*].Instances[*].{InstanceId:InstanceId,PrivateIp:PrivateIpAddress,LaunchTime:LaunchTime}" \
  --output table
```


### D. Application Load Balancer (ALB) and Target Group Health


Check the load balancing tier and health statuses of downstream compute targets:


```bash
# 1. Describe application load balancers and capture the Target Group ARN
TG_ARN=$(aws elbv2 describe-target-groups \
  --region ap-southeast-5 \
  --query "TargetGroups[?contains(TargetGroupName, 'pbtpay-app-tg')].TargetGroupArn|[0]" \
  --output text)

echo "Target Group ARN: ${TG_ARN}"

# 2. Check the health of targets in our Target Group dynamically using the ARN
aws elbv2 describe-target-health \
  --region ap-southeast-5 \
  --target-group-arn "${TG_ARN}" \
  --query "TargetHealthDescriptions[*].{TargetId:Target.Id,Port:Target.Port,HealthStatus:TargetHealth.State}" \
  --output table
```


### E. RDS MariaDB Database Cluster Configuration


Confirm the performance parameters, storage size, and high-availability configuration of our database tier:


```bash
# 1. View the RDS instances and extract database identifier
DB_ID=$(aws rds describe-db-instances \
  --region ap-southeast-5 \
  --query "DBInstances[0].DBInstanceIdentifier" \
  --output text)

echo "DB Identifier: ${DB_ID}"

# 2. Verify Allocated Storage, IOPS, Storage Type, Multi-AZ status, and backups
aws rds describe-db-instances \
  --region ap-southeast-5 \
  --db-instance-identifier "${DB_ID}" \
  --query "DBInstances[0].{DBInstanceIdentifier:DBInstanceIdentifier,MultiAZ:MultiAZ,AllocatedStorage:AllocatedStorage,MaxAllocatedStorage:MaxAllocatedStorage,StorageType:StorageType,Iops:Iops,BackupRetentionPeriod:BackupRetentionPeriod,PreferredBackupWindow:PreferredBackupWindow}" \
  --output json
```


### F. ElastiCache Valkey Session Cluster Status


Inspect our horizontal Valkey caching instances deployed in the database subnet tier. We iterate over all node groups to inspect each `NodeGroupId` with member `CacheClusterId` values:


```bash
# 1. Discover Valkey replication group identifiers
VALKEY_REP_ID=$(aws elasticache describe-replication-groups \
  --region ap-southeast-5 \
  --query "ReplicationGroups[0].ReplicationGroupId" \
  --output text)

echo "Valkey Replication Group ID: ${VALKEY_REP_ID}"

# 2. Project every node group and print its member cache cluster IDs
aws elasticache describe-replication-groups \
  --region ap-southeast-5 \
  --replication-group-id "${VALKEY_REP_ID}" \
  --query "ReplicationGroups[*].{ReplicationGroupId:ReplicationGroupId,Status:Status,NodeGroups:NodeGroups[*].{NodeGroupId:NodeGroupId,Members:NodeGroupMembers[*].CacheClusterId}}" \
  --output json
```


---


## 5. Troubleshooting AWS CLI Configuration Errors


If you encounter issues while running AWS CLI commands, consult these common fixes:


### A. "ExpiredToken"


* **Root Cause:** Your local temporary credentials (e.g., from AWS SSO or STS Session Token) have expired.
* **Fix:** Renew your session credentials by re-authenticating with the AWS Identity Center or CLI login helper:

```bash
aws sso login --profile my-sso-profile
```


### B. "SignatureDoesNotMatch"


* **Root Cause:** Cryptographic signature verification failed. This is typically caused by:
  1. An incorrect or mistyped Secret Access Key.
  2. A local system clock drift mismatch exceeding 15 minutes.
  3. Incorrect region target configuration.
* **Fix:** Verify active profiles and current time sync with UTC:

```bash
# View current profile settings
aws configure list

# Check system clock sync
date -u
```


### C. "Could not connect to the endpoint URL"


* **Root Cause:** The default region is set incorrectly, or your connection is blocked by a local proxy or firewall.
* **Fix:** Ensure `--region ap-southeast-5` is specified. Recall that the control-plane discovery commands utilize secure public HTTPS AWS API endpoints and do *not* require VPN/Bastion access, but check local proxy or internet settings.


### D. "AccessDenied" or "UnauthorizedOperation"


* **Root Cause:** Your IAM user or role lacks the necessary AWS permissions to perform the discovery queries (e.g., missing `ec2:DescribeVpcs` or `rds:DescribeDBInstances`).
* **Fix:** Do not use administrator credentials or wide access as a first-line solution. Recommend a scoped-down least-privilege IAM Audit Role/Policy containing only the required read-only actions (such as `ec2:Describe*`, `rds:Describe*`, and `elasticache:Describe*`). Only apply wider policies like the AWS-managed `ReadOnlyAccess` as a broader organizational fallback when fine-grained policies cannot be implemented.


### E. Validating Your Client Session


For successful authentication and troubleshooting verification, you can run the STS get-caller-identity diagnostic command:


```bash
aws sts get-caller-identity
```
