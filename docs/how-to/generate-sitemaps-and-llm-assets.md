---
layout: default
okf_version: "0.1"
type: "How-To Guide"
title: "Generating Sitemaps and LLM-Friendly Assets"
timestamp: "2026-08-05T22:30:00+08:00"
topics: ["how-to", "sitemaps", "llms", "generation", "assets"]
---

# Generating Sitemaps and LLM-Friendly Assets

This guide explains how to generate, synchronize, and update XML sitemaps, robots.txt, security.txt, and AI/LLM-friendly assets (`llms.txt`, `llms-full.txt`, and `llms-context.xml`) across your repository directories.

---

## How to Regenerate Sitemaps and Web Metadata

Whenever you add, rename, or delete documentation pages under the `docs/` folder, you must synchronize sitemap files.

### Step 1: Execute the Sitemap compiler
Run the script using the Python interpreter:

```bash
python3 scripts/generate_sitemaps.py
```

### Step 2: Confirm file outputs
The compiler will search all markdown pages, determine standard URLs, and produce four critical production assets in both your repository root and `docs/` directories:
* `sitemap.txt` (a newline-separated plain list of pages)
* `sitemap.xml` (formal XML schema compliant index)
* `robots.txt` (search engine directives pointing to sitemaps)
* `.well-known/security.txt` (RFC 9116 compliant security contact file)

---

## How to Compile LLM and AI Context Assets

Our repository hosts a high-density asset compilation system mapping references inside `llms.txt` to compile standard LLM context sets.

### Step 1: Run the LLM asset compiler
Compile the high-density files by executing:

```bash
python3 scripts/generate_llms_assets.py
```

### Step 2: Validate generated XML
Verify that the output was constructed correctly and parses cleanly:

```bash
python3 -m unittest tests/test_llms_assets.py
```

---

## Automated CI Hook Synchronisation

Both sitemap generation and LLM asset compilers are automatically verified inside our GitHub Actions workflows (`.github/workflows/jekyll-gh-pages.yml` and `docs-ci.yml`).

If you make modifications to documentation but forget to execute these local python compilers, the CI step will flag a file-mismatch error and prompt you to run them. Always run both compilers and verify using `python3 -m unittest discover -s tests` before pushing to your branch.
