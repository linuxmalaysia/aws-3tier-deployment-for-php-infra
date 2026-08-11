---
layout: default
okf_version: "0.1"
type: "Technical Reference Guide"
title: "Secure Developer Access Guide"
timestamp: 2026-08-05T22:20:36+08:00
topics: ["aws", "3-tier", "security", "bastion"]
---

**[SECURITY & COMPLIANCE]**

# Secure Developer AWS Access Guide (SSH Jumphost)

This guide provides technical research, architectural specifications, and step-by-step instructions for developers based in our **Cyberjaya, Selangor, Malaysia** office to securely access private AWS resources (private ASG compute servers, database systems, and standalone staging instances) using a highly secure, cost-optimized SSH Jumphost (Bastion).

---

## Architectural Research & Feasibility Analysis

### The Question: "Can/Should we deploy the Jumphost outside a VPC?"

During design discussions, a proposal was raised: **"Does deploying a small Amazon Linux not in a VPC give us a better and cheaper solution?"**

Based on cloud architecture fundamentals and AWS networking constraints, this proposal is **both technically impossible and architecturally undesirable**. Here is why:

1. **VPC Requirement in AWS:**
   Since the retirement of AWS EC2-Classic, **every EC2 instance must run inside a Virtual Private Cloud (VPC)**. There is no longer any option to deploy a "raw" EC2 instance outside of a VPC.
2. **The "Separate Jumphost VPC" Anti-Pattern:**
   Even if the proposal is interpreted as deploying the Jumphost inside a *separate management VPC* (instead of our main application VPC), this approach is **not** cheaper or safer. It introduces severe cost and operational overhead:
   - **Transit Gateway (TGW) Costs:** To connect the separate Jumphost VPC to the private subnets of our application VPC, we would need to provision an AWS Transit Gateway. In the **AWS Asia Pacific (Malaysia) region (`ap-southeast-5`)**, a TGW attachment costs **$0.05 per hour** (~$36.50/mo per VPC connection) plus a **$0.02 per GB** data processing fee. This alone is **3.5x more expensive** than running the entire jumphost itself!
   - **VPC Peering Complexity:** Alternatively, establishing a VPC Peering Connection requires updating routing tables in both VPCs, dealing with inter-AZ data transfer fees ($0.01/GB in each direction), and managing dual security boundaries, which increases the likelihood of human error.
   - **Resource Duplication:** A separate VPC would require its own Internet Gateway, public subnets, and routing infrastructure, duplicating base costs.

### The Optimal Solution: Public Subnet + Strict IP Whitelisting

The **best, safest, and cheapest** approach is to deploy a small `t4g.micro` instance (equipped with energy-efficient ARM64 Graviton processors) inside the **existing public subnet** of our main application VPC:
- **No Extra AWS Networking Cost:** It reuses the existing public Internet Gateway and routing infrastructure.
- **Strict Ingress Firewalling (Zero-Trust):** The Jumphost's Security Group permits inbound TCP port 22 connections **exclusively** from the public CIDR of our **Cyberjaya, Selangor, Malaysia office** (configurable via `jumphost_allowed_ssh_cidr`). All other internet traffic is dropped silently at the AWS Hypervisor layer.
- **Deep Private Isolation:** The private compute nodes (ASG) and standalone dev environments have **no public IP addresses** and are completely unreachable from the public internet. They only permit SSH (port 22) ingress **exclusively from the Jumphost's Security Group**.
- **Minimal Cost Impact:** Running a `t4g.micro` with a 15GB gp3 EBS root volume and an Elastic IP costs only **~$10.98 USD / month** (~RM 49.41 MYR/mo) on-demand, which can be further optimized via Savings Plans.

---

## Technical Specifications of the Jumphost

Our OpenTofu setup automates this configuration. The Jumphost is deployed with:
* **Base OS:** Supports canonical **Ubuntu 24.04 LTS** (allows 100% compliance with the ASIMP hardening framework) or **Amazon Linux 2023**, matching the input options supported by the module.
* **Network Sizing:** `t4g.micro` (ARM64/Graviton), costing **$0.0084/hour**.
* **Storage:** 15GB gp3 SSD, encrypted at rest (`gp3` storage at `$0.08/GB-mo`).
* **Static IP:** Associated with an AWS Elastic IP (EIP) so developers have a stable endpoint that does not change upon reboot.

---

## OS Hardening & Auditing via ASIMP

To protect our access gateway, the Jumphost must be hardened using **ASIMP (Ansible System Integrity Management Platform)**. ASIMP implements a "Measure, Harden, Re-Measure" security flow.

### Key SSH Hardening Policies Configured via ASIMP:
1. **Disable Password-Based Authentication:** Only cryptographic keys are allowed.
2. **Disable Root Logins:** Root SSH is strictly disabled (`PermitRootLogin no`). Developers must connect using their own unprivileged user (e.g., `ubuntu` or standard service accounts) and escalate using `sudo` if authorized.
3. **Restricted Cryptographic Cipher Suites:** Enforces modern, secure key exchange algorithms and ciphers, completely blocking obsolete/weak ones (e.g., MD5, SHA-1, 3DES, Blowfish).
   - **Allowed Key Exchange (KEX):** `curve25519-sha256`, `diffie-hellman-group16-sha512`
   - **Allowed MACs:** `hmac-sha2-512-etm@openssh.com`
   - **Allowed Ciphers:** `chacha20-poly1305@openssh.com`, `aes256-gcm@openssh.com`
4. **Active Connection Auditing:** OpenSCAP and Lynis run scheduled audits to verify CIS Level 2 benchmark compliance, writing audit scorecard logs to `/var/log/asimp-baseline-scores.json`.

---

## Critical SSH Private Key Security Guidelines

The private SSH key represents the developer's identity and grants administrative access. If a private key is compromised, the entire AWS infrastructure is at risk. All developers must follow these strict guidelines:

### 1. Always Use a Strong Passphrase
Never generate a passwordless SSH key. Always encrypt the private key with a strong passphrase. This ensures that even if the private key file is stolen (e.g., from a physical laptop loss or malware infection), the attacker cannot use it without decrypting it first.

### 2. Never Share Private Keys
A private key is private. It must **never** be shared via Slack, Email, WhatsApp, or uploaded to any shared network. Under no circumstances should multiple developers share the same SSH key.

### 3. Never Check Keys into Version Control
Ensure that private keys (such as `.pem`, `.id_ed25519`, `.ppk`) are never committed to Git repositories. Add a global rule in your `.gitignore` file:
```ignore
# Ignore SSH Keys
*.pem
*.key
id_ed25519
id_rsa
*.ppk
```

### 4. Apply Strict File Permissions (OS-Specific)

#### On Linux / macOS (Unix File Permissions)
SSH clients will refuse to use private keys that are too openly readable. The `.ssh` directory and key files must be restricted:
```bash
# Secure the SSH directory (read/write/search for owner only)
chmod 700 ~/.ssh

# Secure the private key file (read/write for owner only, no access for anyone else)
chmod 600 ~/.ssh/id_ed25519

# Secure public keys (read/write for owner, read-only for others)
chmod 644 ~/.ssh/id_ed25519.pub
```

#### On Windows (NTFS Access Control Lists)
Windows does not use standard Unix permissions, but the OpenSSH client on Windows still enforces strict security. To secure a private key (`id_ed25519` or `key.pem`) on Windows:

##### Option A: Using PowerShell (Fastest)
Run the following commands in PowerShell to strip inheritance and grant permissions exclusively to the current logged-in user:
```powershell
# Store key path in a variable
$keyPath = "$Home\.ssh\id_ed25519"

# Strip inheriting permissions and remove all group permissions
icacls $keyPath /inheritance:r

# Grant full control exclusively to the current logged-in user
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
icacls $keyPath /grant:r "${currentUser}:F"
```

##### Option B: Using Windows File Explorer (GUI)
1. Right-click the private key file (`id_ed25519`) and select **Properties**.
2. Go to the **Security** tab, and click **Advanced**.
3. Click **Disable inheritance** and select "Remove all inherited permissions from this object".
4. Click **Add**, click "Select a principal", type your Windows username, and click **Check Names**.
5. Set permissions to **Full control** and click **OK** -> **Apply** -> **OK**.

---

## Developer Access Step-by-Step Instructions

To reach private AWS resources (e.g., Standalone Instance `10.0.10.15`), developers use the Jumphost as a transit bridge.

```
 [ Cyberjaya Office ]
   (Public IP)
       │ (Port 22 Inbound)
       ▼
 ┌────────────────────────────────────────────────────────┐
 │                      VPC BOUNDARY                      │
 │                                                        │
 │  [ Public Subnet ]                                     │
 │    - Jumphost (Elastic IP: 54.x.y.z)                   │
 │         │                                              │
 │         └──────────┐ (SSH ProxyJump / Port 22 Private) │
 │                    ▼                                   │
 │  [ Private Subnet ]                                    │
 │    - Standalone Dev Instance (Private IP: 10.0.10.15)  │
 │    - ASG Web Nodes (Private IPs)                       │
 └────────────────────────────────────────────────────────┘
```

Below are instructions for macOS, Linux, and Windows platforms.

### 1. macOS Developer Setup

macOS has native SSH client support. We recommend generating an **Ed25519** key, which is modern, lightweight, and highly secure.

#### Step 1: Generate your SSH Key Pair
Open Terminal and run:
```bash
ssh-keygen -t ed25519 -C "yourname@office.com"
```
*Note: Specify a secure passphrase when prompted.*

#### Step 2: Register your Public Key on AWS
Provide your public key (`~/.ssh/id_ed25519.pub`) to your AWS administrator. They will register it on the Jumphost and private instances.

#### Step 3: Configure your local SSH config file
To avoid typing complex commands every time, create or edit your SSH configuration file (`~/.ssh/config`):
```bash
nano ~/.ssh/config
```

Insert the following block (replace `54.x.y.z` with the Jumphost's actual Elastic IP address and `your-key` with your private key name):
```text
# Common SSH settings
Host *
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519

# The SSH Jumphost
Host aws-jumphost
  HostName 54.x.y.z
  User ubuntu

# Private Standalone / ASG Application servers
Host aws-private-*
  # Use wildcard mapping to route any private VPC IP via Jumphost
  HostName 10.0.*
  User ubuntu
  ProxyJump aws-jumphost
```
*Save and close (`Ctrl+O` then `Ctrl+X`).*

#### Step 4: Access your Private Instances
Now, you can SSH into any private instance inside the VPC using a single, secure command:
```bash
# Connect directly to a private instance (macOS routes this transparently via Jumphost)
ssh aws-private-10.0.10.15
```

---

### 2. Linux (Ubuntu) Developer Setup

Linux systems use OpenSSH. The configuration is almost identical to macOS.

#### Step 1: Generate your SSH Key Pair
```bash
ssh-keygen -t ed25519 -C "yourname@office.com"
```

#### Step 2: Configure your SSH config file
Create or edit your local SSH configuration file:
```bash
nano ~/.ssh/config
```

Add the following configuration block:
```text
Host *
  AddKeysToAgent yes
  IdentityFile ~/.ssh/id_ed25519

Host aws-jumphost
  HostName 54.x.y.z
  User ubuntu

Host aws-private-*
  HostName 10.0.*
  User ubuntu
  ProxyJump aws-jumphost
```

#### Step 3: Start SSH Agent & Load Key
Add these commands to your terminal profile (`~/.bashrc` or `~/.zshrc`) to automate loading:
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

#### Step 4: Access Private Instances
```bash
ssh aws-private-10.0.10.15
```

---

### 3. Windows Developer Setup

Windows developers can use **PowerShell (with native OpenSSH)** or **PuTTY**.

---

#### Method A: Using PowerShell & Native OpenSSH (Recommended)

Modern Windows 10/11 has OpenSSH Client installed by default.

##### Step 1: Generate your SSH Key Pair
Open PowerShell and run:
```powershell
ssh-keygen -t ed25519 -C "yourname@office.com"
```

##### Step 2: Enable and configure Windows SSH Agent
Start the Windows SSH Agent service (requires running PowerShell as Administrator once):
```powershell
# Set Startup Type to Automatic
Set-Service -Name ssh-agent -StartupType Automatic

# Start the Service
Start-Service ssh-agent

# Load your Private Key into the Agent
ssh-add $Home\.ssh\id_ed25519
```

##### Step 3: Configure your local SSH Config File
In PowerShell, edit or create the SSH config file:
```powershell
notepad $Home\.ssh\config
```

Add the following configuration block (replace `54.x.y.z` with the Jumphost's Elastic IP):
```text
Host *
  AddKeysToAgent yes
  IdentityFile ~/.ssh/id_ed25519

Host aws-jumphost
  HostName 54.x.y.z
  User ubuntu

Host aws-private-*
  HostName 10.0.*
  User ubuntu
  ProxyJump aws-jumphost
```

##### Step 4: Secure Key Permissions
As shown in the Key Security section, secure your private key:
```powershell
$keyPath = "$Home\.ssh\id_ed25519"
icacls $keyPath /inheritance:r
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
icacls $keyPath /grant:r "${currentUser}:F"
```

##### Step 5: Connect directly
Now, connect securely to your private staging servers via PowerShell:
```powershell
ssh aws-private-10.0.10.15
```

---

#### Method B: Using PuTTY (GUI-Based SSH Client)

If you prefer using PuTTY, follow these steps to set up secure tunneling.

##### Step 1: Generate Key using PuTTYgen
1. Download and open **PuTTYgen**.
2. Select **Ed25519** (or RSA 4096) under "Parameters -> Type of key to generate".
3. Click **Generate** and move your mouse randomly over the blank area.
4. Enter a strong **Key passphrase**.
5. Click **Save private key** and save it as `id_ed25519.ppk` inside a secure folder (e.g., `C:\Users\username\.ssh\`).
6. Copy the text from the top box ("Public key for pasting into OpenSSH authorized_keys file") and send it to your AWS administrator.

##### Step 2: Secure PPK file permissions
1. Right-click your `id_ed25519.ppk` file and click **Properties**.
2. Go to **Security** -> **Advanced**.
3. Click **Disable inheritance** -> select "Remove all inherited permissions".
4. Add your personal Windows user principal with **Full Control**.

##### Step 3: Configure PuTTY for Proxy SSH Session (ProxyCommand/plink)
To establish multi-hop SSH tunnels in PuTTY:
1. Open **PuTTY**.
2. In the **Session** category (on the left):
   - **Host Name (or IP address):** Type the private IP of the target server (e.g., `10.0.10.15`).
   - **Port:** `22`.
3. In the **Connection -> SSH -> Auth -> Credentials** category:
   - Browse and select your `id_ed25519.ppk` private key.
4. In the **Connection -> Proxy** category:
   - **Proxy type:** Select **Local**.
   - **Proxy hostname:** Type the Jumphost's Elastic IP (e.g., `54.x.y.z`).
   - **Port:** `22`.
   - **Telnet command, or local proxy command:** Type the following (replace paths with your actual PuTTY installation and key paths):
     ```text
     plink -batch -v ubuntu@%proxyhost -i "C:\Users\YOUR_USERNAME\.ssh\id_ed25519.ppk" -nc %host:%port
     ```
5. Return to the **Session** category:
   - Type a name under "Saved Sessions" (e.g., `AWS-Private-10.0.10.15`).
   - Click **Save**.
6. Click **Open**. PuTTY will connect to the Jumphost first, proxy the connection, and open the private server terminal transparently!

##### Method C: Alternatively, using Port Forwarding (SSH Tunnel) via PuTTY
If you prefer standard SSH Port Forwarding:
1. Open **PuTTY** and configure a connection to the Jumphost:
   - **Host Name (or IP address):** Jumphost Elastic IP (`54.x.y.z`).
   - **User:** `ubuntu`.
2. Go to **Connection -> SSH -> Tunnels**.
3. In "Add new forwarded port":
   - **Source port:** Type a local random port (e.g., `9022`).
   - **Destination:** Type the private IP of your staging server and SSH port (e.g., `10.0.10.15:22`).
   - Click **Add**.
4. Go back to the **Session** category, save it as `AWS-Jumphost-Tunnel`, and click **Open** (enter key passphrase when prompted).
5. Open a **second** PuTTY window:
   - **Host Name (or IP address):** `127.0.0.1`.
   - **Port:** `9022`.
   - Select your private key under **Connection -> SSH -> Auth -> Credentials** and open!
