---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "GitLab CI/CD & AWS EFS Code Deployment"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier", "cicd", "automation"]
---

**[DEVOPS EXECUTION]**

# GitLab CI/CD & AWS EFS Code Deployment Architecture

This guide provides a comprehensive design and deployment blueprint for automating application delivery. It outlines a secure, scalable workflow where developers use **GitLab** for source control, triggering automated **GitLab CI/CD pipelines** that deploy code directly onto an **Amazon Elastic File System (EFS)**.

By mounting this shared network filesystem (NFSv4) concurrently on both **Auto Scaling Groups (ASGs)** and **Standalone EC2 instances**, application updates become instantly active across all nodes without rebuilding AMIs or performing slow rolling redeployments.

---

## 1. High-Level Architecture Overview

The system bridges an external GitLab repository with a secure, private AWS 3-tier VPC. Since EFS endpoints reside deep within private subnets, we implement a highly secure staging-and-sync mechanism.

```
 [ Developer ] ──(git push)──► [ GitLab Repo ]
                                     │
                                     ▼ (Triggers Pipeline)
                        [ GitLab CI/CD Runner ]
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         │ (Authentication via AWS OIDC Role Assumption)         │
         ▼                                                       ▼
 ┌───────────────┐                                       ┌───────────────┐
 │ Branch: main  │                                       │ Tag: v*.*.*   │
 └───────┬───────┘                                       └───────┬───────┘
         │ (Uploads Staging Build)                               │ (Uploads Prod Build)
         ▼                                                       ▼
 ┌───────────────────────────────────────────────────────────────────────┐
 │                      AWS S3 Deployment Bucket                         │
 └───────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼ (Triggers SSM Run Command)
 ┌───────────────────────────────────────────────────────────────────────┐
 │               AWS Systems Manager (SSM) Run Command                   │
 └───────────────────────────────────┬───────────────────────────────────┘
                                     │
                                     ▼ (Executes Sync Script)
 ┌───────────────────────────────────────────────────────────────────────┐
 │                    Utility/Sync Instance (VPC)                        │
 └───────────────────────────────────┬───────────────────────────────────┘
                                     │ (Saves / unpacks assets onto EFS)
                                     ▼
 ┌───────────────────────────────────────────────────────────────────────┐
 │                     Amazon EFS Shared File System                     │
 └──────┬────────────────────────────┼────────────────────────────┬──────┘
        │                            │                            │
        ▼ (Mounts EFS)               ▼ (Mounts EFS)               ▼ (Mounts EFS)
 ┌───────────────┐           ┌───────────────┐           ┌───────────────┐
 │  Frontend ASG │           │  Backend ASG  │           │ Standalone EC2│
 │   (Nginx)     │           │ (API App Node)│           │ (Staging Node)│
 └───────────────┘           └───────────────┘           └───────────────┘
```

### Core Flow Steps:
1. **Commit & Push:** A developer pushes code or creates a git tag in GitLab.
2. **GitLab CI/CD Trigger:** The GitLab runner starts, authenticates dynamically to AWS using **OIDC IAM Role Assumption**, runs tests, compiles build artifacts (e.g., node modules, frontend assets), and tars the build.
3. **Artifact Staging:** The runner uploads the tarball artifact to a secure, private **AWS S3 Deployment Bucket**.
4. **Automated EFS Syncing:** The runner triggers an **AWS Systems Manager (SSM) Run Command** targeting a dedicated internal Utility/Sync instance (or the Bastion host) that has the EFS volume mounted.
5. **Atomic Unpacking:** The Utility instance downloads the tarball from S3, unpacks it into the appropriate EFS sub-directory, and atomically swaps symlinks to complete the deploy in milliseconds.
6. **Instant Access:** Because the EFS volume is mounted across all active ASG instances and standalone staging nodes, the code is immediately available to the running applications without any instance terminations or server reboots.

---

## 2. Shared EFS Directory & Mounting Strategy

To maintain complete Isolation of Concerns and prevent staging/production resource conflicts, EFS must be structured logically.

### 2.1 EFS Directory Layout
We partition EFS into two top-level environments (`production` and `staging`) with application sub-directories:

```
/mnt/efs/
├── staging/                           # Used exclusively by Standalone EC2 Instances
│   ├── frontend/                      # Frontend HTML/JS assets
│   └── backend/                       # Backend API server code
│
└── production/                        # Used by Auto Scaling Groups (ASGs)
    ├── frontend/                      # Production Frontend assets
    └── backend/                       # Production Backend API code
```

### 2.2 Secure Mounting on EC2 Instances (Ubuntu 26.04 LTS & AL2023)
To ensure reliable, encrypted-in-transit connections to EFS, we use `amazon-efs-utils` over NFSv4 with TLS (Port 2049).

#### A. Interactive or Bootstrap Script Mounting:
```bash
# Install EFS Utilities
# For Amazon Linux 2023 (ASG Nodes):
sudo dnf install -y amazon-efs-utils

# For Ubuntu 26.04 LTS (Standalone Staging Nodes):
sudo apt-get update && sudo apt-get install -y binutils cpp
git clone https://github.com/aws/efs-utils.git /tmp/efs-utils
cd /tmp/efs-utils && ./build-deb.sh
sudo apt-get install -y ./build/amazon-efs-utils*deb

# Create Mount Directories
sudo mkdir -p /mnt/efs

# Mount with TLS enabled (Encapsulated over Port 2049)
# Replace fs-xxxxxx with your actual EFS File System ID
sudo mount -t efs -o tls,iam fs-xxxxxx:/ /mnt/efs
```

#### B. Persistent Mount Configuration (`/etc/fstab`):
To guarantee EFS is automatically remounted if an ASG instance launches or a standalone node is rebooted, append the following entry to `/etc/fstab`:
```text
fs-xxxxxx:/ /mnt/efs efs _netdev,tls,iam,defaults 0 0
```
*(The `_netdev` option prevents the system from attempting to mount EFS before network interfaces are fully initialized).*

---

## 3. Nginx Configuration & Path Design

To serve code residing on network-attached storage efficiently, Nginx must be configured to minimize file system traversal overhead and handle the static/dynamic paths correctly.

### 3.1 Nginx Path Allocation

| Instance Role | Local Mount Path | App Root Directory (Served by Nginx) |
| :--- | :--- | :--- |
| **Production Frontend ASG** | `/mnt/efs` | `/mnt/efs/production/frontend/` |
| **Production Backend ASG** | `/mnt/efs` | `/mnt/efs/production/backend/` (App running via PM2/systemd) |
| **Standalone Staging EC2** | `/mnt/efs` | `/mnt/efs/staging/frontend/` & `/mnt/efs/staging/backend/` |

---

### 3.2 Performance Tuning for Network Filesystems (EFS)
Because EFS is a distributed network filesystem, standard POSIX metadata lookups (like `stat()`, which checks if a file exists or has changed) introduce millisecond network round-trips. Under high web traffic, this can severely throttle Nginx performance.

**Mitigation:** Enforce Nginx-level file descriptor caching. Add the following directives inside your global `/etc/nginx/nginx.conf` (within the `http` block):

```nginx
# Cache open file descriptors, their sizes, and modification times
open_file_cache          max=2000 inactive=20s;
open_file_cache_valid    30s;
open_file_cache_min_uses 2;
open_file_cache_errors   on;
```

---

### 3.3 Production Frontend Nginx Configuration (ASG Node)
Apply this configuration to the instances running in your **Frontend Web ASG** (`/etc/nginx/sites-available/default`):

```nginx
server {
    listen 80;
    server_name app.linuxmalaysia.com;

    # Root pointing to the production frontend EFS path
    root /mnt/efs/production/frontend;
    index index.html index.htm;

    # Performance optimizations for EFS
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;

    # Enable Gzip Compression to save bandwidth
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    # Standard SPA Routing or Static File Server
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Route backend API requests to the Backend ALB
    location /api/ {
        # Core VPC DNS Resolver with short TTL to handle Backend ALB scaling
        resolver 169.254.169.254 valid=10s;
        set $backend_upstream "http://internal-production-backend-alb-123456.ap-southeast-5.elb.amazonaws.com";

        proxy_pass $backend_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static Assets Cache Control
    location ~* \.(?:css|js|jpg|jpeg|gif|png|ico|svg|woff|woff2|ttf|otf)$ {
        expires 7d;
        add_header Cache-Control "public, no-transform";
        access_log off;
    }

    # Custom Error Pages
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

---

### 3.4 Standalone Staging Nginx Configuration (EC2 Staging Node)
Staging nodes host both frontend and backend APIs on a single standalone instance for cost efficiency. Apply this layout (`/etc/nginx/sites-available/default`):

```nginx
server {
    listen 80;
    server_name staging.linuxmalaysia.com;

    # Staging Frontend Root Directory
    root /mnt/efs/staging/frontend;
    index index.html;

    sendfile on;

    # Staging Frontend SPA Routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Staging API reverse proxy pointing to a local Node.js/Python service
    location /api/ {
        # Staging backend app usually runs locally on port 5000
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Disable buffering for real-time staging logs/WebSocket support
        proxy_buffering off;
    }
}
```

---

## 4. Automated GitLab CI/CD Pipeline Configuration

To trigger automatic deployments based on code versioning, we configure the pipeline to recognize:
1. **Pushes to `main` branch:** Deploys instantly to the **Staging / Standalone** environment.
2. **Git Release Tags (`v*.*.*`):** Deploys to the **Production / ASG** environment.

### Production-Ready `.gitlab-ci.yml` Manifest

Place this file in the root of your code repository:

```yaml
stages:
  - lint
  - build
  - deploy

variables:
  AWS_DEFAULT_REGION: "ap-southeast-5" # Malaysia Region
  S3_STAGING_BUCKET: "s3://company-deployment-staging-bucket-ap-southeast-5"
  S3_PROD_BUCKET: "s3://company-deployment-prod-bucket-ap-southeast-5"
  SYNC_INSTANCE_STAGING_ID: "i-0123456789staging" # Standalone EC2 Staging Node ID
  SYNC_INSTANCE_PROD_ID: "i-0123456789utility" # Prod EFS Admin Utility Instance ID

# AWS Authentication via OIDC (No persistent IAM credentials stored in GitLab!)
.aws-auth:
  id_tokens:
    MY_OIDC_TOKEN:
      aud: https://gitlab.com
  before_script:
    - mkdir -p ~/.aws
    - echo "AssumeRoleWithWebIdentity"
    - >
      export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s"
      $(aws sts assume-role-with-web-identity
      --role-arn "arn:aws:iam::112233445566:role/GitLabCI-AWS-OIDC-Role"
      --role-session-name "GitLabPipeline-${CI_PIPELINE_ID}"
      --web-identity-token "${MY_OIDC_TOKEN}"
      --query "Credentials.[AccessKeyId,SecretAccessKey,SessionToken]"
      --output text))

# ==================== LINT STAGE ====================
code-lint:
  stage: lint
  image: node:20-alpine
  script:
    - npm ci
    - npm run lint
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/

# ==================== BUILD STAGE ====================
build-assets:
  stage: build
  image: node:20-alpine
  artifacts:
    paths:
      - dist/
      - package.json
      - package-lock.json
    expire_in: 1 week
  script:
    - npm ci
    - npm run build
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/

# ==================== DEPLOY STAGES ====================

# Deploy Staging: Automatically triggered on commits/merges to main branch
deploy-staging:
  extends: .aws-auth
  stage: deploy
  image: amazon/aws-cli:latest
  dependencies:
    - build-assets
  script:
    # 1. Package the build files
    - tar -czf staging-build.tar.gz dist/ package.json package-lock.json

    # 2. Upload tarball to Staging S3 Bucket
    - aws s3 cp staging-build.tar.gz ${S3_STAGING_BUCKET}/staging-build.tar.gz

    # 3. Trigger AWS SSM Run Command on Staging Instance to pull and unpack
    - >
      aws ssm send-command
      --instance-ids "${SYNC_INSTANCE_STAGING_ID}"
      --document-name "AWS-RunShellScript"
      --comment "Deploy staging files from GitLab CI"
      --parameters 'commands=[
        "aws s3 cp '"${S3_STAGING_BUCKET}"'/staging-build.tar.gz /tmp/staging-build.tar.gz",
        "mkdir -p /mnt/efs/staging/frontend_new",
        "tar -xzf /tmp/staging-build.tar.gz -C /mnt/efs/staging/frontend_new",
        "rm -rf /mnt/efs/staging/frontend_old",
        "[ -d /mnt/efs/staging/frontend ] && mv /mnt/efs/staging/frontend /mnt/efs/staging/frontend_old",
        "mv /mnt/efs/staging/frontend_new /mnt/efs/staging/frontend",
        "rm -rf /mnt/efs/staging/frontend_old /tmp/staging-build.tar.gz",
        "echo Deployment Successful"
      ]'
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# Deploy Production: Triggered exclusively by creating a Tag (e.g., v1.0.0)
deploy-production:
  extends: .aws-auth
  stage: deploy
  image: amazon/aws-cli:latest
  dependencies:
    - build-assets
  script:
    # 1. Package the production files
    - tar -czf prod-build.tar.gz dist/ package.json package-lock.json

    # 2. Upload to Production S3 Bucket
    - aws s3 cp prod-build.tar.gz ${S3_PROD_BUCKET}/prod-build-${CI_COMMIT_TAG}.tar.gz

    # 3. Trigger SSM Run Command on Utility Admin instance to unpack onto the shared EFS
    - >
      aws ssm send-command
      --instance-ids "${SYNC_INSTANCE_PROD_ID}"
      --document-name "AWS-RunShellScript"
      --comment "Deploy production files to EFS from GitLab CI"
      --parameters 'commands=[
        "aws s3 cp '"${S3_PROD_BUCKET}"'/prod-build-'"${CI_COMMIT_TAG}"'.tar.gz /tmp/prod-build.tar.gz",
        "mkdir -p /mnt/efs/production/frontend_new",
        "tar -xzf /tmp/prod-build.tar.gz -C /mnt/efs/production/frontend_new",
        "rm -rf /mnt/efs/production/frontend_old",
        "[ -d /mnt/efs/production/frontend ] && mv /mnt/efs/production/frontend /mnt/efs/production/frontend_old",
        "mv /mnt/efs/production/frontend_new /mnt/efs/production/frontend",
        "rm -rf /mnt/efs/production/frontend_old /tmp/prod-build.tar.gz",
        "echo Production Shared EFS Deployment Successful"
      ]'
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
```

---

## 5. Architectural Evaluation & Better Alternatives

While deploying application code over EFS NFS mounts provides rapid deployment cycles and immediate propagation, it represents a **classic hybrid design pattern with notable operational tradeoffs.**

Below is an engineering analysis comparing EFS deployment to modern cloud-native standards.

### 5.1 Tradeoffs of the EFS NFS Code-Serving Approach

#### The Drawbacks:
1. **Network Latency Bottleneck:** Filesystem operations (`stat`, `open`, `read`) over network NFSv4 run significantly slower than on local NVMe/SSD EBS volumes. If an application (e.g., Python/Node.js) imports hundreds of source files at startup, load times are substantially degraded.
2. **Atomic Swap Synchronization Risks:** If an instance executes active code while EFS is being overwritten, it can load partial files, causing runtime exceptions. (Our symlink atomic swap mitigated this, but node-level system file-locks can still lock operations).
3. **Write Concurrency and POSIX File Locking:** Multiple instances running backend APIs attempting to write logs, cache files, or local SQLite data on the same mounted EFS directory will experience lock contention, causing thread blockages.
4. **No Version Immutability (Risk of Corruption):** A single bad build or a malicious script executing on an ASG node can overwrite the shared code folder, instantaneously corrupting/compromising *all* ASG nodes and standalone instances simultaneously.
5. **No Easy Atomic Rollback:** Rollbacks require manual filesystem restores or triggering an old S3 unpack command.

---

### 5.2 Proposed Solution 1: Containerization (Docker + Amazon ECS/EKS) — *Highly Recommended*

This is the standard modern cloud-native deployment model.

```
 [ Dev Push ] ──► [ GitLab CI ] ──► [ Build Docker Image ] ──► [ Push to Amazon ECR ]
                                                                       │
                                                                       ▼
                                                           [ Trigger ECS Service Update ]
                                                                       │
                                                                       ▼
                                                           [ ECS Tasks on Fargate/EC2 ]
```

* **How it works:** GitLab CI/CD builds a standalone Docker Image containing Nginx and the code. It pushes this image to **Amazon Elastic Container Registry (ECR)**. It then triggers an ECS Service rolling update.
* **Why it is superior:**
  - **Complete Isolation & Immutability:** Each container is an exact, unchangeable replica of the tested image.
  - **No Network Storage Bottleneck:** The container runs files off local virtual memory/EBS storage inside the host, resulting in sub-millisecond execution loops.
  - **Zero-Downtime Deployments:** ECS manages blue/green or rolling upgrades automatically, starting healthy new containers before terminating old ones.
  - **Instant rollback:** Rollback is as simple as reverting the active image tag to the previous version in ECR.

---

### 5.3 Proposed Solution 2: Stateless S3-Pull Bootstrapping with ASG Instance Refresh

If keeping EC2 instances is mandatory, decouple them from the EFS file system using local EBS drives hydrated from S3.

```
 [ Dev Push ] ──► [ GitLab CI ] ──► [ Build Code & Tarball ] ──► [ Push to Amazon S3 ]
                                                                        │
                                                                        ▼ (SSM or Instance Refresh)
                                                                 [ Launch Template Update ]
                                                                        │
                                                                        ▼ (ASG Rolling Update)
                                                                 [ Pull Tarball onto Local EBS ]
```

* **How it works:**
  1. GitLab CI/CD compiles the code, zips it, and uploads the immutable artifact to S3 (e.g., `s3://bucket/deploy-v1.0.0.zip`).
  2. The pipeline updates an SSM Parameter or updates the **Auto Scaling Group Launch Template** User Data to reference the new version.
  3. The pipeline triggers an **ASG Instance Refresh** (a controlled, automated rolling upgrade where AWS replaces old instances with new ones).
  4. During bootstrap, the EC2 instance pulls the zip file down from S3, decompresses it locally onto its high-speed EBS volume (`/var/www/html/`), and starts Nginx.
* **Why it is superior:**
  - **Performance:** Nginx serves files directly off local high-speed SSDs (EBS) without network NFS lookups.
  - **Reliability:** If one instance's file system is corrupted, the other instances in the ASG remain perfectly healthy.
  - **Versioned per-instance copy:** Each instance has its own isolated, stable copy of the code extracted to local storage. If an auto-scaling event occurs, the newly launched instance pulls the identical versioned zip file.
