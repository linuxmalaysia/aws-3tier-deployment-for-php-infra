---
layout: default
okf_version: "0.1"
type: "Active Context Manifest"
title: "Active Context Manifest (.agents/brain/active_context_manifest.md)"
timestamp: 2026-08-05T22:40:00+08:00
topics: ["context-management", "brain", "dsom", "active-context", "governance"]
description: "Active session file manifest indexing the core operating rules, goals, and currently loaded context files for this workspace."
---

# 🧠 Active Context Manifest

This manifest indexes the active mental context, current task checkpoints, and core sovereign rules loaded for this session. It serves as our spatial memory anchor under the Deep State of Mind (DSOM) framework.

---

## 1. Active Session Focus

* **Goal:** Adopt and codify the Local Knowledge-First Discovery Protocol, establishing a strict 5-step local discovery flow inside `.agents/AGENTS.md` and `docs/SOP-KNOWLEDGE-FIRST-DISCOVERY.md` before querying terminal, live servers, or external services.
* **Workspace:** AWS 3-Tier PHP CodeIgniter Infrastructure deployment via OpenTofu.

---

## 2. Spatial Memory Anchors (SSOT Files)

These files represent the Single Source of Truth (SSOT) and must be queried in order of priority before executing commands:

| Priority | Document | Purpose / Topics |
|---|---|---|
| 1 | `AGENTS.md` | Root operating guidelines and entry gateway |
| 2 | `.agents/AGENTS.md` | Sovereign Master Constitution (Rule 20 / Rule 21) |
| 3 | `docs/SOP-KNOWLEDGE-FIRST-DISCOVERY.md` | 5-Step local discovery workflow standard operating procedure |
| 4 | `.agents/skills/jules-knowledge/SKILL.md` | Workspace-specific engineering skills and structural defaults |
| 5 | `docs/index.md` | Documentation Portal Index |

---

## 3. Session Progress Checkpoints

- [x] Create `.agents/AGENTS.md` (Sovereign Constitution)
- [x] Edit root `AGENTS.md` (Gateway to sovereign rules)
- [x] Create `docs/SOP-KNOWLEDGE-FIRST-DISCOVERY.md` (SOP for Local Knowledge-First Discovery)
- [x] Create `.agents/brain/active_context_manifest.md` (Active Context Index)
- [ ] Verify creation and modification of files
- [ ] Run `python3 scripts/prepare_docs.py` (Validate and compile OKF frontmatter)
- [ ] Run Python unit tests
- [ ] Complete pre-commit checklist and submit changes
