---
layout: default
okf_version: "0.1"
type: "How-To Guide"
title: "Deploying & Destroying AWS 3-Tier Infrastructure"
timestamp: "2026-08-05T22:30:00+08:00"
topics: ["how-to", "deploy", "destroy", "opentofu", "infrastructure"]
---

# Deploying & Destroying AWS 3-Tier Infrastructure


This how-to guide explains how to deploy and destroy our secure **AWS Secure 3-Tier PHP CodeIgniter** infrastructure in the `ap-southeast-5` (Malaysia) region using our automated shell helpers.

---


## How to Deploy the Infrastructure


Deploying the stack involves running the pre-flight checks, validating OpenTofu code, planning the resource changes, and applying them.


### Step 1: Prepare variables file


First, make sure that `terraform.tfvars` exists in the `terraform/` directory. If it is already present, skip this copy step to preserve any existing custom configurations and credentials. If it is absent, run:

```bash
cd terraform/
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your custom VPC ranges, whitelisted SSH endpoints (e.g. Cyberjaya CIDR), and database engine details.


### Step 2: Run the deployment script


Return to the repository root before running the script:

```bash
cd ..
./scripts/deploy.sh
```

**What this script does behind the scenes:**

1. Validates that the `tofu` CLI is installed.
2. Checks for `terraform.tfvars` and falls back if missing.
3. Automatically formats all OpenTofu configuration files in place using `tofu fmt -recursive` (which may rewrite files).
4. Performs logical and syntactic validation via `tofu validate`.
5. Compiles and saves an execution plan to `tfplan`.
6. Prompts you for final confirmation before modifying any AWS resources.

---


## How to Destroy the Infrastructure


When you no longer require the active AWS environment, destroy all provisioned assets safely to prevent unwanted FinOps charges.


### Step 1: Run the destruction helper


From the root of the repository, execute:

```bash
./scripts/destroy.sh
```

**What this script does behind the scenes:**

1. Verifies that the `tofu` CLI is active.
2. Ensures that OpenTofu has been initialized and that `.terraform/` state mapping exists.
3. Warns you with a red high-visibility banner.
4. Prompts you for final confirmation. If `y` is selected, it triggers `tofu destroy -auto-approve` immediately.

---


## Troubleshooting Incomplete Deployments


### Issue: "Port already in use" or "Backend lock failed"


If your deploy was interrupted, OpenTofu might lock your local state or backend.

**Solution:**

Before running `tofu force-unlock`, you must confirm that no other OpenTofu process is actively running or still owns the backend lock. Once confirmed, unlock the state file using the lock ID printed in your terminal error log:

```bash
cd terraform/
tofu force-unlock <LOCK_ID>
```


### Issue: Missing AWS Access Keys


If the deployment errors with `No valid credential sources found`, configure your AWS profile:

```bash
aws configure --region ap-southeast-5
```
