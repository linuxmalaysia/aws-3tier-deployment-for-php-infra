"""Unit tests for AI Processing Stack, Flowise + Qdrant + LiteLLM Integration Guide.

Verifies OKF frontmatter compliance, Flowise/Qdrant/LiteLLM architectural details,
CodeIgniter 4 PHP API request code snippets, TS/MC risk register entries, and
index registrations across docs/index.md, SUMMARY.md, llms.txt, and sitemaps.
"""

import os
import re
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOC_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "ai-processing-stack.md")


def test_ai_processing_doc_exists():
    """Ensure the AI Processing Stack documentation file exists."""
    assert os.path.exists(DOC_PATH), f"File not found: {DOC_PATH}"


def test_ai_processing_okf_frontmatter():
    """Verify OKF frontmatter attributes inside docs/engineering/ai-processing-stack.md."""
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert content.startswith("---"), "Document must start with YAML frontmatter"
    parts = content.split("---", 2)
    assert len(parts) >= 3, "YAML frontmatter not properly closed with '---'"

    fm = parts[1]
    assert 'layout: default' in fm
    assert 'okf_version: "0.1"' in fm
    assert 'type: "Technical Reference Guide"' in fm
    assert 'title: "AI Processing Stack, Flowise + Qdrant + LiteLLM Integration, and API Gateway Guide"' in fm
    assert 'timestamp:' in fm
    assert 'topics: ["aws", "3-tier", "ai-processing", "flowise", "qdrant", "litellm"]' in fm


def test_ai_processing_content_sections():
    """Verify core sections, components, and code examples exist in the document."""
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Core components
    assert "Flowise" in content
    assert "Qdrant" in content
    assert "LiteLLM" in content
    assert "CodeIgniter" in content
    assert "ap-southeast-5" in content

    # PHP API client class
    assert "class AiProcessingService" in content
    assert "generateChatCompletion" in content
    assert "executeFlowiseWorkflow" in content

    # cURL requests
    assert "curl -X POST" in content
    assert "/v1/chat/completions" in content
    assert "/v1/embeddings" in content

    # TS/MC risk register codes
    assert "TS-07" in content
    assert "TS-08" in content
    assert "TS-09" in content
    assert "MC-03" in content


def test_ai_processing_index_registrations():
    """Verify the new guide is properly indexed across all manifest files."""
    # docs/index.md
    index_md = os.path.join(REPO_ROOT, "docs", "index.md")
    with open(index_md, "r", encoding="utf-8") as f:
        index_content = f.read()
    assert "engineering/ai-processing-stack.html" in index_content

    # docs/SUMMARY.md
    docs_summary = os.path.join(REPO_ROOT, "docs", "SUMMARY.md")
    with open(docs_summary, "r", encoding="utf-8") as f:
        docs_summary_content = f.read()
    assert "engineering/ai-processing-stack.md" in docs_summary_content

    # SUMMARY.md
    root_summary = os.path.join(REPO_ROOT, "SUMMARY.md")
    with open(root_summary, "r", encoding="utf-8") as f:
        root_summary_content = f.read()
    assert "docs/engineering/ai-processing-stack.md" in root_summary_content

    # llms.txt
    llms_txt = os.path.join(REPO_ROOT, "llms.txt")
    with open(llms_txt, "r", encoding="utf-8") as f:
        llms_content = f.read()
    assert "docs/engineering/ai-processing-stack.md" in llms_content


def test_ai_processing_sitemap_registration():
    """Verify ai-processing-stack.md is included in scripts/generate_sitemaps.py."""
    script_path = os.path.join(REPO_ROOT, "scripts", "generate_sitemaps.py")
    with open(script_path, "r", encoding="utf-8") as f:
        script_content = f.read()
    assert "engineering/ai-processing-stack.md" in script_content
