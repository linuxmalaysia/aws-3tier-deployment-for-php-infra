---
layout: default
okf_version: "0.1"
type: "Agent Skill"
title: "Continuous Integration, Automation Workflows & Site Indexing Skill"
timestamp: "2026-08-13T12:00:00+08:00"
topics: ["cicd", "automation", "indexing", "workflows", "python"]
name: cicd-automation-workflows
description: "Instructs on procedures for managing CI/CD pipelines, automated doc processors, frontmatter standards, sitemap compilations, and static code validation."
---

# Continuous Integration, Automation Workflows & Site Indexing Skill

This custom agent skill incorporates all procedures, styles, and linter patterns for GitHub Actions pipelines, Python documentation formatters, sitemap indexers, and test scripts.

## When to Use This Skill
- Use this when modifying GitHub Actions OIDC workflows or Jekyll publication tasks.
- Use this when formatting documentation pages, adding new files, or updating frontmatter properties.
- Use this when adjusting static validation tests or running diagnostic suites in python.

## How to Use It (Procedures and Conventions)

### 1. Conditional & Automated CI/CD Pipelines
- **GitHub Actions setup:** The workflow `.github/workflows/opentofu.yml` conditionalizes credentials-based actions (e.g., plan, apply) to execute only when `secrets.AWS_ROLE_TO_ASSUME` is populated, avoiding crash-loops on fork PRs.
- **GitLab CI/CD Integration:** Integrates shared EFS/NFS mounts with Nginx custom server blocks, EFS metadata performance tuning (via `open_file_cache`), and robust alternatives.
- **Jekyll GH Pages:** Automatically builds static documents from `docs/` and publishes them to GitHub Pages.

### 2. OKF v0.1 Frontmatter Enforcement
- Every Markdown document must start on Line 1 with correct OKF v0.1 YAML frontmatter block starting and ending with `---`.
- String values containing colons, brackets, parentheses, or emojis must be double-quoted.
- All non-empty ISO timestamps must be double-quoted consistently using the `serialize_timestamp` helper in `scripts/prepare_docs.py` to prevent formatting mismatch errors.
- Always run the python formatter after modifying or creating documentation pages:
  ```bash
  python3 scripts/prepare_docs.py
  ```

### 3. Sitemaps and Security.txt Compilation
- Always execute sitemap generators to compile sitemap registries, robots.txt, and RFC 9116 `.well-known/security.txt` files across the workspace:
  ```bash
  python3 scripts/generate_sitemaps.py
  ```

### 4. Interactive Jekyll Layouts & PDF Generation
- Jekyll themes feature custom responsive sidebar layouts styled using CSS grids (`260px 1fr` on desktop, stacked on mobile).
- Interactive "PRINT PDF" buttons leverage CSS print blocks (forcing A4 margins and Day theme styling) and automated Puppeteer pdf engines on git pushes. Prevent page-break gaps by overriding screen `100vh` boundaries with `height: auto !important` inside `@media print` directives.

---
*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-13*
