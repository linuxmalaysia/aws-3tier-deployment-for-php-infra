---
layout: default
okf_version: "0.1"
type: "Conceptual Explanation"
title: "The Diátaxis Framework in AWS Secure 3-Tier"
timestamp: "2026-08-05T22:30:00+08:00"
topics: ["diataxis", "documentation", "framework", "architecture"]
---

# The Diátaxis Framework in Our Project

This project adopts the **Diátaxis Framework** to structure and govern its technical documentation. Diátaxis is a systematic framework designed to solve the problem of poorly structured documentation by focusing on the needs of the reader rather than the developer's internal categorization.

By dividing our documentation into four distinct quadrants—**Tutorials**, **How-To Guides**, **Reference**, and **Explanation**—we ensure that users can always find information suited to their immediate cognitive context.

---

## The Four Quadrants of Diátaxis

```
                       PRACTICAL

            Tutorials      │     How-To Guides
            (Learning)     │     (Problem-Solving)
                           │
  ACQUISITION ─────────────┼───────────── ACTION
  (Study)                  │             (Work)
                           │
            Explanation    │     Reference
            (Understanding)│     (Information)

                       THEORETICAL
```

Each quadrant serves a specific purpose, has its own style, and addresses a unique type of question:

### 1. Tutorials (Learning-Oriented)
- **Objective:** Teach the reader how to get started through a guided, step-by-step learning lesson.
- **Tone:** Encouraging, narrative-driven, and highly prescriptive.
- **Execution:** Focused on a beginner-friendly path (e.g., [Setting up a Development Sandbox](../tutorials/setup-development-sandbox.html)) using a real but simple dataset.

### 2. How-To Guides (Problem-Oriented)
- **Objective:** Answer specific, practical real-world questions for developers who already have a basic understanding.
- **Tone:** Concise, focused, and goal-directed.
- **Execution:** Solving concrete tasks like [Deploying Infrastructure with OpenTofu](../how-to/deploy-infrastructure.html), [Auditing Ansible Playbooks](../how-to/audit-ansible-and-podman.html), or [Generating Sitemaps](../how-to/generate-sitemaps-and-llm-assets.html).

### 3. Reference (Information-Oriented)
- **Objective:** Provide exhaustive, factual, and scannability-optimized reference material about every tool, script, and configuration parameter in the project.
- **Tone:** Objective, neutral, dry, and highly structured.
- **Execution:** Detailing CLI inputs, outputs, schemas, exit codes, and static linter rules in [Scripts and Helpers Reference](../reference/scripts-reference.html) and [Linter Rules Specifications](../reference/static-analysis-rules.html).

### 4. Explanation (Understanding-Oriented)
- **Objective:** Provide conceptual clarity, historical context, architectural deep dives, and discussions on key design choices.
- **Tone:** Reflective, analytical, and informative.
- **Execution:** Explaining advanced topics like [Lightweight Parsing and Metadata Parallelization](../explanation/lightweight-parsers.html).

---

## Why Diátaxis is Integrated Here

Prior to implementing Diátaxis, our documentation co-mingled low-level CLI specifications, architectural blueprints, and beginner setup guides in single monolithic markdown files. This led to high cognitive load, stale documentation, and difficulty in identifying gaps.

With Diátaxis:
1. **Clear Division of Labor:** Developers writing new features know exactly where to put configuration references (Reference), tutorial workflows (Tutorials), operational runbooks (How-To Guides), or architectural trade-off discussions (Explanation).
2. **AI-Friendly Ingestion:** Our `generate_llms_assets.py` parser compiles documentation in a way that respects this logical separation, allowing LLM agents to accurately categorize and leverage project knowledge.
3. **Improved Dual-Platform Compatibility:** The GitBook `SUMMARY.md` and Jekyll-based GitHub Pages indices are clean, intuitive, and highly scannable.
