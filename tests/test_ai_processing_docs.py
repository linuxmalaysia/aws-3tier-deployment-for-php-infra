#!/usr/bin/env python3
"""Unit tests for AI Processing Stack, Flowise + Qdrant + LiteLLM Integration Guide.

Verifies OKF frontmatter compliance, Flowise/Qdrant/LiteLLM architectural details,
CodeIgniter 4 PHP API request code snippets, TS/MC risk register entries, and
index registrations across docs/index.md, SUMMARY.md, llms.txt, and sitemaps.

Run with:
    python3 -m unittest discover -s tests
"""

import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOC_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "ai-processing-stack.md")


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class AiProcessingDocsTestCase(unittest.TestCase):
    """Tests for docs/engineering/ai-processing-stack.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(DOC_PATH)

    def test_ai_processing_doc_exists(self):
        """Ensure the AI Processing Stack documentation file exists."""
        self.assertTrue(os.path.exists(DOC_PATH), f"File not found: {DOC_PATH}")

    def test_ai_processing_okf_frontmatter(self):
        """Verify OKF frontmatter attributes inside docs/engineering/ai-processing-stack.md."""
        self.assertTrue(self.content.startswith("---"), "Document must start with YAML frontmatter")
        parts = self.content.split("---", 2)
        self.assertGreaterEqual(len(parts), 3, "YAML frontmatter not properly closed with '---'")

        fm = parts[1]
        self.assertIn('layout: default', fm)
        self.assertIn('okf_version: "0.1"', fm)
        self.assertIn('type: "Technical Reference Guide"', fm)
        self.assertIn('title: "AI Processing Stack, Flowise + Qdrant + LiteLLM Integration, and API Gateway Guide"', fm)
        self.assertIn('timestamp:', fm)
        self.assertIn('topics: ["aws", "3-tier", "ai-processing", "flowise", "qdrant", "litellm"]', fm)

    def test_ai_processing_content_sections(self):
        """Verify core sections, components, and code examples exist in the document."""
        # Core components
        self.assertIn("Flowise", self.content)
        self.assertIn("Qdrant", self.content)
        self.assertIn("LiteLLM", self.content)
        self.assertIn("CodeIgniter", self.content)
        self.assertIn("ap-southeast-5", self.content)

        # PHP API client class
        self.assertIn("class AiProcessingService", self.content)
        self.assertIn("generateChatCompletion", self.content)
        self.assertIn("executeFlowiseWorkflow", self.content)

        # cURL requests
        self.assertIn("curl -X POST", self.content)
        self.assertIn("/v1/chat/completions", self.content)
        self.assertIn("/v1/embeddings", self.content)

        # TS/MC risk register codes
        self.assertIn("TS-07", self.content)
        self.assertIn("TS-08", self.content)
        self.assertIn("TS-09", self.content)
        self.assertIn("MC-03", self.content)

    def test_ai_processing_index_registrations(self):
        """Verify the new guide is properly indexed across all manifest files."""
        # docs/index.md
        index_md = os.path.join(REPO_ROOT, "docs", "index.md")
        index_content = _read(index_md)
        self.assertIn("engineering/ai-processing-stack.html", index_content)

        # docs/SUMMARY.md
        docs_summary = os.path.join(REPO_ROOT, "docs", "SUMMARY.md")
        docs_summary_content = _read(docs_summary)
        self.assertIn("engineering/ai-processing-stack.md", docs_summary_content)

        # SUMMARY.md
        root_summary = os.path.join(REPO_ROOT, "SUMMARY.md")
        root_summary_content = _read(root_summary)
        self.assertIn("docs/engineering/ai-processing-stack.md", root_summary_content)

        # llms.txt
        llms_txt = os.path.join(REPO_ROOT, "llms.txt")
        llms_content = _read(llms_txt)
        self.assertIn("docs/engineering/ai-processing-stack.md", llms_content)

    def test_ai_processing_sitemap_registration(self):
        """Verify ai-processing-stack.md is included in scripts/generate_sitemaps.py."""
        script_path = os.path.join(REPO_ROOT, "scripts", "generate_sitemaps.py")
        script_content = _read(script_path)
        self.assertIn("engineering/ai-processing-stack.md", script_content)


if __name__ == "__main__":
    unittest.main()
