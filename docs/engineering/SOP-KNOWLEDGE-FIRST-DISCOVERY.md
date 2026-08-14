---
layout: default
okf_version: "0.1"
type: standard_operating_procedure
title: "📚 SOP: Local Knowledge-First Discovery & OKF Context Protocol"
timestamp: "2026-08-05T22:35:00Z"
topics: ["okf", "discovery", "context-management", "brain", "dsom", "SOP", "governance"]
description: "SOP detailing how AI agents and human operators leverage OKF YAML frontmatter (topics, description) in .agents/brain/ and docs/ to perform fast local discovery before executing remote SSH, Ansible, SSM, or OpenTofu commands."
---

**[SECURITY & COMPLIANCE]**

# 📚 SOP: Local Knowledge-First Discovery & OKF Context Protocol


## 1. Executive Intent

To prevent unnecessary SSH probes, redundant terminal commands, token window exhaustion, and context loss during agentic sessions on this **AWS 3-Tier PHP Infrastructure** project, all AI agents must strictly adhere to the **Local Knowledge-First Protocol**.

All project facts, architectural specifications, module configurations (OpenTofu VPC, Security Groups, ALB, RDS, Valkey, WAF, Jumphost), and operational guidelines are indexed using **OKF v0.1 YAML Frontmatter** in `.agents/` and `docs/`.


---


## 2. Standard Operating Procedure (5-Step Discovery Flow)


```text
[ Step 1: Local OKF Search ] ──▶ grep / find on .agents/ and docs/ (topics: / description:)
         │
         ▼
[ Step 2: Targeted File Viewing ] ──▶ read_file / targeted range view on matched .md files
         │
         ▼
[ Step 3: Temporal Verification Gate ] ──▶ Verify OKF timestamp. Research external standards.
         │
         ▼
[ Step 4: Human Verification Gate ] ──▶ Present comparison and seek explicit operator approval.
         │
         ▼
[ Step 5: Terminal Execution Gate ] ──▶ Apply OpenTofu plans, run SSM, or check live state.
```


### Step 1: Local Frontmatter & Metadata Search

Before issuing any remote, state-changing, or external exploratory commands (such as executing `tofu plan`, running SSM queries against live AWS environments, or querying Google), you must perform local discovery. Read-only local commands (such as using `grep` to find local files) are explicitly allowed before the execution gate.

1. Search local OKF frontmatter for relevant `topics:` or `description:` keywords using local tools or local `grep`:

   ```bash
   # Search for RDS or database related local documentation
   grep -ri "topics:.*database" docs/ .agents/
   ```

2. Consult `.agents/brain/active_context_manifest.md` and `AGENTS.md` first (this consultation is required).


### Step 2: Targeted File Viewing

Once the relevant documentation file is found:
- Read specific lines or files using read tools to save context tokens.


### Step 3: Temporal Verification Gate

Check the `timestamp` field in the OKF frontmatter of the matched document:
- If the timestamp indicates that the local specification might be stale or outdated relative to your current knowledge or objective:
  1. Research external authoritative resources (AWS documentation, OpenTofu registry) to find the latest standards (this research is required).
  2. Synthesize a comparison between local documentation and external findings.
  3. **Seek human verification** before updating documentation, running terraform/tofu scripts, or modifying active servers.


### Step 4: Human Verification & Knowledge Update

- Based on the decision in Step 3, perform OKF-compliant document updates before executing infrastructure changes. Run `python3 scripts/prepare_docs.py` to keep YAML metadata correct and updated.


### Step 5: AWS/SSM/Terminal Execution Gate

Remote, state-changing, or external exploratory commands (including OpenTofu plan/apply, live AWS/SSM probes, and external search engine queries) are authorized **ONLY** after completing the local discovery flow, and specifically when:
- Deploying configuration or code changes to staging/production.
- Querying live state, logs, or metrics that cannot possibly be answered by local documentation.


---


## 3. Mandatory Rules Reference

* **Rule 6 (OKF Topics):** All `.md` files must open on line 1 with `---` and contain `topics: [3-5 keywords]`.
* **Rule 12 (Metadata-First Discovery):** Always query `topics:` and `description:` metadata before reading full file bodies.
* **Rule 20 (Local Knowledge-First Mandate):** Search local `.agents/` and `docs/` before issuing remote commands or terminal checks.
* **Rule 21 (Temporal Knowledge Verification Mandate):** Verify OKF timestamps and consult the human operator if the local knowledge is contextually outdated.
