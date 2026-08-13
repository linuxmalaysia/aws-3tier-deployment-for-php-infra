---
layout: default
okf_version: "0.1"
type: "Sovereign Constitution"
title: "The Sovereign Constitution & Rulebook (.agents/AGENTS.md)"
timestamp: "2026-08-05T22:30:00+08:00"
topics: ["aws", "3-tier", "ai-agents", "instructions", "dsom", "governance"]
---

# The Sovereign Constitution & Rulebook (.agents/AGENTS.md)

This is the Sovereign Constitution and Master Rulebook for all AI Agents collaborating on the **AWS 3-Tier Deployment for PHP & Web Infra** repository. You must obey and enforce every directive here.

---

## 1. Local Knowledge-First & Metadata Discovery Mandate (Rule 20)

BEFORE executing exploratory terminal commands, probing live AWS instances, checking SSM states, running Ansible playbooks, or querying search engines to find facts, the AI agent **MUST FIRST** search local project knowledge in `.agents/brain/` and `docs/`.

* **Execution Flow:**
  1. Use keyword searches/grepping on local OKF frontmatter (`topics:` / `description:`) inside `.agents/brain/` and `docs/`.
  2. Targeted file reading via line-range views or file-specific reading before processing large documentation bodies.
  3. Probing live resources (SSM commands, OpenTofu outputs, Ansible nodes) is strictly restricted to applying configuration updates or verifying live state that is completely undocumented locally.

---

## 2. Temporal Knowledge Verification Mandate (Rule 21)

Every markdown document in this project possesses an OKF v0.1 YAML Frontmatter containing a `timestamp` field.
* **Verification Gate:**
  1. Inspect the `timestamp` field of the local knowledge document you are reading.
  2. If the local information is contextually outdated or suspected to be stale:
     - Research external sources (AWS Documentation, OpenTofu Release Notes) to check for newer standards.
     - Present a structured comparison of local knowledge vs. the new findings to the human operator.
     - **Seek explicit human verification** before updating documents or running deployment scripts.

---

## 3. Project Archetype & Environment Guidelines

Keep your context anchored strictly within the project boundaries:
1. **PHP Web Infrastructure:** Serving CodeIgniter applications via Nginx and PHP-FPM on AWS Graviton (`ap-southeast-5`).
2. **Deterministic Infrastructure-as-Code:** Use modular OpenTofu code. Avoid quick manual patches.
3. **No AI/RAG in Prod Application:** The core runtime application tier is a pure, classical PHP framework completely free of AI or RAG components. Keep any AI tools, prompt templates, and skills isolated under `.agents/`.

---

## 4. Google Antigravity-Compatible Agent Skills (.agents/skills/)

All AI agents operating within this workspace must understand and utilize the custom Agent Skills registered under `.agents/skills/`.

* **Unified Skill Architecture:**
  - Every skill directory contains a `SKILL.md` containing combined OKF v0.1 and Agent Skills open standard frontmatter, explicitly retaining both the `name` (unique identifier, with an optional containing folder name fallback if omitted) and `description` metadata fields.
  - Discovery leverages both fields at startup, with `description` acting as the semantic search trigger.
  - Every skill ends with the standard Deep State of Mind (DSOM) AI Protocol footer.
* **Exchange and Synergy:**
  - Google Jules and Google Antigravity share these exact skills to ensure consistent domain expertise, execution flow, security safeguards, and deployment commands without experiencing context amnesia across agent turn executions.
* **Discovered Skills Catalog:**
  1. `jules-knowledge`: Workspace architectural standards, target regions, and default parameters.
  2. `gitbook-llm-assets`: GitBook summary configurations, XML/TXT sitemaps, and LLM assets compilation tools.
  3. `asimp-security-audit`: Lynis/OpenSCAP audits, Ansible privilege/mode checking rules, and rootless Podman constraints.
  4. `disaster-recovery-sovereignty`: DR Option Two configurations, Malaysian PDPA Section 129 checks, and banker's rounding compliance tests.
  5. `opentofu-cloud-engineering`: VPC subnets, zero-trust ALB ingress rules, IMDSv2 launch templates, and MariaDB/Valkey overrides.
  6. `cicd-automation-workflows`: GitHub Actions conditional OIDC, GitLab NFS performance, Python doc formatting, and printing page-break overrides.
