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

## 4. Google Antigravity-Compatible Agent Skills (.agents/skills/ & skills/)

All AI agents operating within this workspace must understand and utilize the custom Agent Skills registered under `.agents/skills/` and synchronized to root `skills/` (following [Google Antigravity Agent Skills](https://antigravity.google/docs/skills) and [AgentSkills.io](https://agentskills.io/home)).

* **Unified Skill Architecture & Dual-Path Sync:**
  - Every skill directory contains a `SKILL.md` containing combined OKF v0.2 (`spec_version: "0.2"`, trust pillars) and Agent Skills open standard frontmatter, explicitly retaining both the `name` and `description` metadata fields.
  - Skill packages are synchronized between `.agents/skills/` and root `skills/` for 100% interoperability across Google Antigravity, AgentSkills.io, Warp Agent Skills, and Google Jules agent runners.
  - Every skill ends with the standard Deep State of Mind (DSOM) AI Protocol footer.
* **Exchange and Synergy:**
  - Google Jules and Google Antigravity share these exact skills to ensure consistent domain expertise, execution flow, security safeguards, and deployment commands without experiencing context amnesia across agent turn executions.
* **Discovered Agent Skills Catalog & Parameters:**

| Skill Name | Directory Path | Description | Key Operational Parameters |
| :--- | :--- | :--- | :--- |
| **`jules-knowledge`** | `.agents/skills/jules-knowledge/`<br>`skills/jules-knowledge/` | Comprehensive workspace instructions, architectural mappings, security boundaries, and operational knowledge curated from Google Jules. | AWS region (`ap-southeast-5`), Graviton ARM64 (`t4g.micro`), 19 DSOM Entry Points, Tri-Phasic Mind cognitive model. |
| **`gitbook-llm-assets`** | `.agents/skills/gitbook-llm-assets/`<br>`skills/gitbook-llm-assets/` | Instructions and procedures for compiling LLM context files, managing GitBook config files, and generating XML and TXT sitemaps. | `SUMMARY.md`, `.gitbook.yaml`, `scripts/generate_llms_assets.py`, `scripts/generate_sitemaps.py`. |
| **`asimp-security-audit`** | `.agents/skills/asimp-security-audit/`<br>`skills/asimp-security-audit/` | Guidelines and procedures for system integrity management, host-level security audits, compliance reporting, and static analysis verification. | Lynis, OpenSCAP, `tests/test_ansible_playbooks.py`, `tests/test_podman_containers.py`, SPA Checklist. |
| **`disaster-recovery-sovereignty`** | `.agents/skills/disaster-recovery-sovereignty/`<br>`skills/disaster-recovery-sovereignty/` | Procedural guidelines, architecture reviews, costing calculations, and regulatory alignment for disaster recovery and sovereignty configurations. | DR Option Two (Malaysia `ap-southeast-5`), PDPA Section 129, Banker's Rounding (`Decimal`), AWS Pricing Calculator. |
| **`opentofu-cloud-engineering`** | `.agents/skills/opentofu-cloud-engineering/`<br>`skills/opentofu-cloud-engineering/` | Standards and troubleshooting patterns for OpenTofu configurations, network designs, compute nodes, databases, and DNS configurations. | OpenTofu >= 1.6.0, VPC subnets, security groups, WAFv2, ASG launch templates, IMDSv2 `mktemp -d` parallelization. |
| **`cicd-automation-workflows`** | `.agents/skills/cicd-automation-workflows/`<br>`skills/cicd-automation-workflows/` | Procedures for managing CI/CD pipelines, automated doc processors, frontmatter standards, sitemap compilations, and static code validation. | GitHub Actions OIDC (`.github/workflows/opentofu.yml`), Node.js 22 LTS, `scripts/prepare_docs.py`, Jekyll responsive layout. |
