---
layout: default
okf_version: "0.1"
type: "Agent Skill"
title: "GitBook Publishing & LLM Assets Compilation Skill"
timestamp: "2026-08-13T12:00:00+08:00"
topics: ["gitbook", "llms", "documentation", "sitemaps"]
name: gitbook-llm-assets
description: "Provides instructions and procedures for compiling LLM context files, managing GitBook config files, and generating XML and TXT sitemaps."
---

# GitBook Publishing & LLM Assets Compilation Skill

This custom agent skill encapsulates all operational knowledge regarding GitBook publishing, LLM context file compilation, sitemap generation, and testing validations in our repository.

## When to Use This Skill
- Use this when modifying or regenerating `llms.txt`, `llms-full.txt`, or `llms-context.xml`.
- Use this when updating GitBook structures in `.gitbook.yaml` or `SUMMARY.md`.
- Use this when regenerating text/XML sitemaps, `robots.txt`, or `.well-known/security.txt`.

## How to Use It (Procedures and Conventions)

### 1. GitBook Integration & Table of Contents
- The repository is configured for GitBook publishing via `.gitbook.yaml` and `SUMMARY.md` placed at the root of the repository.
- Ensure all references inside `SUMMARY.md` point to the original files in `docs/` without moving them.
- The correct production GitHub Pages URL is: `https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/`.

### 2. LLM Assets Compilation
- The Python asset compiler `scripts/generate_llms_assets.py` provides an API and a CLI utility (`llms_txt2ctx`) to parse `llms.txt`.
- It automatically outputs a compiled markdown file `llms-full.txt` and an escaped XML context file `llms-context.xml` in both the repository root and `docs/` directory.
- Always regenerate these assets when updating the documentation tree or the file hierarchy.

### 3. Sitemap & SEO Automation
- The repository uses `scripts/generate_sitemaps.py` to compile and generate `sitemap.txt`, `sitemap.xml`, `robots.txt`, and RFC 9116 `.well-known/security.txt` in both the repository root and `docs/` directories.
- This ensures proper indexing across both GitHub Pages and GitBook domains.
- The `.well-known` folder must be explicitly whitelisted inside `docs/_config.yml`.

### 4. Continuous Testing & Verification
- Dedicated unit test coverage is maintained in `tests/test_llms_assets.py` and `tests/test_sitemaps.py`.
- These tests verify the syntax of GitBook config files, the correctness of `SUMMARY.md`, and the structure and well-formedness of `llms-context.xml` and `llms-full.txt`.

---
*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-13*
