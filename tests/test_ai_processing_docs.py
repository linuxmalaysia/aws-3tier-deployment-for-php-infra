#!/usr/bin/env python3
"""Unit tests for AI Processing Stack, Flowise + Qdrant + LiteLLM Integration Guide.

Verifies OKF frontmatter compliance, Flowise/Qdrant/LiteLLM architectural details,
CodeIgniter 4 PHP API request code snippets, TS/MC risk register entries, and
index registrations across docs/index.md, SUMMARY.md, llms.txt, and sitemaps.
"""Unit tests for the AI Processing Stack, Flowise + Qdrant + LiteLLM Integration guide.

This test validates:
* ``docs/engineering/ai-processing-stack.md`` OKF front matter and content structure.
* Integration across ``docs/index.md``, ``SUMMARY.md``, ``docs/SUMMARY.md``, and ``llms.txt``.
* Absence of leftover git merge-conflict markers in files touched by this change.
* Presence in text and XML sitemaps (root and docs copies).
* Presence and consistency of ``llms-context.xml`` / ``llms-full.txt`` (root and docs copies).
* Correct ordering of the new page in ``scripts/generate_sitemaps.py``'s
  ``sort_relative_paths`` helper.

Run with:
    python3 -m unittest discover -s tests
"""

import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOC_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "ai-processing-stack.md")


def _read(path):
    """
    Read a UTF-8 encoded text file.
    
    Parameters:
        path: Path to the file to read.
    
    Returns:
        The file contents as a string.
    """
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
        """Verify that the AI Processing Stack guide is registered in the documentation indexes."""
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
import xml.etree.ElementTree as ET
from typing import Any, Dict, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import prepare_docs  # noqa: E402
import generate_sitemaps  # noqa: E402

DOC_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "ai-processing-stack.md")
INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
ROOT_SUMMARY_PATH = os.path.join(REPO_ROOT, "SUMMARY.md")
DOCS_SUMMARY_PATH = os.path.join(REPO_ROOT, "docs", "SUMMARY.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
GENERATE_SITEMAPS_SCRIPT = os.path.join(SCRIPTS_DIR, "generate_sitemaps.py")

ROOT_SITEMAP_TXT = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_TXT = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_XML = os.path.join(REPO_ROOT, "sitemap.xml")
DOCS_SITEMAP_XML = os.path.join(REPO_ROOT, "docs", "sitemap.xml")

ROOT_LLMS_CONTEXT_XML = os.path.join(REPO_ROOT, "llms-context.xml")
DOCS_LLMS_CONTEXT_XML = os.path.join(REPO_ROOT, "docs", "llms-context.xml")
ROOT_LLMS_FULL_TXT = os.path.join(REPO_ROOT, "llms-full.txt")
DOCS_LLMS_FULL_TXT = os.path.join(REPO_ROOT, "docs", "llms-full.txt")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

GH_BASE = "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
GB_BASE = "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/"

GH_URL = GH_BASE + "engineering/ai-processing-stack.html"
GB_URL = GB_BASE + "engineering/ai-processing-stack"

MD_URL = "docs/engineering/ai-processing-stack.md"
DOCS_REL_MD_URL = "engineering/ai-processing-stack.md"

FRONT_MATTER_TITLE = (
    "AI Processing Stack, Flowise + Qdrant + LiteLLM Integration, and API Gateway Guide"
)
HEADING_TITLE = (
    "AI Processing Stack, Flowise + Qdrant + LiteLLM Integration, & API Gateway Guide"
)
SHORT_TITLE = "AI Processing Stack Guide"
DESC = (
    "Deep-dive into AI processing infrastructure, Flowise visual workflow "
    "orchestration, Qdrant vector retrieval, LiteLLM proxy routing, and "
    "production PHP CodeIgniter API request patterns."
)

MERGE_CONFLICT_MARKERS = ["<<<<<<<", "=======", ">>>>>>>"]


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _parse_front_matter(content: str) -> Tuple[Dict[str, Any], str]:
    if not content.startswith("---\n"):
        raise ValueError("Document does not start with opening front matter delimiter '---\\n'")

    closing_idx = content.find("\n---\n", 4)
    if closing_idx == -1:
        if content.endswith("\n---"):
            closing_idx = len(content) - 4
        else:
            raise ValueError("Document missing closing front matter delimiter '\\n---\\n'")

    front_matter_text = content[4:closing_idx]
    body_text = content[closing_idx + 5:] if content[closing_idx:].startswith("\n---\n") else content[closing_idx + 4:]

    front_matter = prepare_docs.parse_yaml_front_matter(front_matter_text)
    return front_matter, body_text


class AiProcessingDocFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of docs/engineering/ai-processing-stack.md."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.content = _read(DOC_PATH)
        cls.front_matter, cls.body_text = _parse_front_matter(cls.content)

    def test_file_exists(self) -> None:
        self.assertTrue(os.path.isfile(DOC_PATH))

    def test_starts_with_front_matter_delimiter(self) -> None:
        self.assertTrue(self.content.startswith("---\n"))

    def test_required_okf_fields_present(self) -> None:
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            with self.subTest(key=key):
                self.assertIn(key, self.front_matter)

    def test_layout_is_default(self) -> None:
        self.assertEqual(self.front_matter["layout"], "default")

    def test_okf_version_is_expected_value(self) -> None:
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_title_field_value(self) -> None:
        self.assertEqual(self.front_matter["title"], FRONT_MATTER_TITLE)

    def test_type_matches_prepare_docs_inference(self) -> None:
        inferred_type = prepare_docs.infer_okf_type(
            "docs/engineering/ai-processing-stack.md"
        )
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_contain_expected_keywords(self) -> None:
        expected_topics = ["aws", "3-tier", "ai-processing", "flowise", "qdrant", "litellm"]
        self.assertEqual(self.front_matter["topics"], expected_topics)

    def test_timestamp_matches_iso8601_with_offset(self) -> None:
        self.assertRegex(
            self.front_matter["timestamp"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$",
        )


class AiProcessingDocContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of docs/engineering/ai-processing-stack.md."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.content = _read(DOC_PATH)

    def test_contains_top_level_heading(self) -> None:
        self.assertIn(f"# {HEADING_TITLE}", self.content)

    def test_security_compliance_banner_present(self) -> None:
        self.assertIn("**[SECURITY & COMPLIANCE]**", self.content)

    def test_numbered_sections_present(self) -> None:
        headings = [
            "## 1. AI Processing Infrastructure Overview",
            "## 2. Deep-Dive Component Architecture",
            "## 3. Production PHP CodeIgniter AI API Requests",
            "## 4. Technology Risk & Licensing Register (TS/MC Series Updates)",
            "## 5. Architectural Alignment & Summary",
        ]
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)

    def test_component_subsections_present(self) -> None:
        subsections = [
            "### A. Flowise: Visual AI Workflow Orchestrator",
            "### B. Qdrant: AI-Native Vector Database",
            "### C. LiteLLM: Unified Model Proxy & Gateway",
            "### A. CodeIgniter 4 AI API Client Service",
            "### B. Native cURL Test Execution Commands",
        ]
        for heading in subsections:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)

    def test_mentions_core_components_and_region(self) -> None:
        for keyword in ["Flowise", "Qdrant", "LiteLLM", "CodeIgniter", "ap-southeast-5"]:
            with self.subTest(keyword=keyword):
                self.assertIn(keyword, self.content)

    def test_php_service_class_and_methods_present(self) -> None:
        self.assertIn("class AiProcessingService", self.content)
        self.assertIn("public function generateChatCompletion(", self.content)
        self.assertIn("public function executeFlowiseWorkflow(", self.content)
        self.assertIn("namespace App\\Services;", self.content)

    def test_php_code_block_wrapped_in_raw_liquid_tags(self) -> None:
        # PHP code containing braces/vars must be shielded from Jekyll/Liquid
        # templating with {% raw %} ... {% endraw %} tags.
        raw_start = self.content.find("{% raw %}")
        raw_end = self.content.find("{% endraw %}")
        php_class_idx = self.content.find("class AiProcessingService")

        self.assertNotEqual(raw_start, -1, "{% raw %} tag missing")
        self.assertNotEqual(raw_end, -1, "{% endraw %} tag missing")
        self.assertGreater(php_class_idx, raw_start, "PHP code must appear after {% raw %}")
        self.assertLess(php_class_idx, raw_end, "PHP code must appear before {% endraw %}")

    def test_curl_commands_present(self) -> None:
        self.assertIn("curl -X POST", self.content)
        self.assertIn("/v1/chat/completions", self.content)
        self.assertIn("/v1/embeddings", self.content)
        self.assertIn("bedrock/qwen3-70b", self.content)
        self.assertIn("bedrock/qwen3-embedding", self.content)

    def test_risk_register_table_entries_present(self) -> None:
        for code in ["TS-07", "TS-08", "TS-09", "MC-03"]:
            with self.subTest(code=code):
                self.assertIn(code, self.content)
        self.assertIn("MIT License", self.content)
        self.assertIn("Apache 2.0 / Permissive", self.content)


class IndexAndSummaryIntegrationTestCase(unittest.TestCase):
    """Tests for index.md, SUMMARY.md, docs/SUMMARY.md, and llms.txt integration."""

    def test_index_md_link_present(self) -> None:
        content = _read(INDEX_PATH)
        self.assertIn(
            f"[{HEADING_TITLE}](engineering/ai-processing-stack.html)",
            content,
        )

    def test_root_summary_md_link_present(self) -> None:
        content = _read(ROOT_SUMMARY_PATH)
        self.assertIn(f"[{SHORT_TITLE}]({MD_URL})", content)

    def test_docs_summary_md_link_present(self) -> None:
        content = _read(DOCS_SUMMARY_PATH)
        self.assertIn(f"[{SHORT_TITLE}]({DOCS_REL_MD_URL})", content)

    def test_llms_txt_link_present(self) -> None:
        content = _read(LLMS_PATH)
        self.assertIn(f"[{SHORT_TITLE}]({MD_URL}) : {DESC}", content)

    def test_root_summary_no_merge_conflict_markers(self) -> None:
        content = _read(ROOT_SUMMARY_PATH)
        for marker in MERGE_CONFLICT_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, content)

    def test_llms_txt_no_merge_conflict_markers(self) -> None:
        content = _read(LLMS_PATH)
        for marker in MERGE_CONFLICT_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, content)

    def test_root_summary_jules_entry_survives_merge(self) -> None:
        # Regression: SUMMARY.md previously had unresolved conflict markers around
        # this entry; ensure the Jules bullet survives alongside the new entry.
        content = _read(ROOT_SUMMARY_PATH)
        self.assertIn(
            "[Autonomous AI Pair-Programming with Google Jules](docs/jules-platform-guide.md)",
            content,
        )

    def test_llms_txt_jules_entry_survives_merge(self) -> None:
        content = _read(LLMS_PATH)
        self.assertIn(
            "[Autonomous AI Pair-Programming with Google Jules](docs/jules-platform-guide.md)",
            content,
        )

    def test_ai_processing_entry_ordered_between_wazuh_and_asimp(self) -> None:
        content = _read(ROOT_SUMMARY_PATH)
        wazuh_idx = content.find("Wazuh SIEM & XDR Deployment Guide")
        ai_idx = content.find(SHORT_TITLE)
        asimp_idx = content.find("ASIMP for AI Agents")

        self.assertNotEqual(wazuh_idx, -1)
        self.assertNotEqual(ai_idx, -1)
        self.assertNotEqual(asimp_idx, -1)
        self.assertLess(wazuh_idx, ai_idx, "AI Processing Stack Guide should follow Wazuh entry")
        self.assertLess(ai_idx, asimp_idx, "AI Processing Stack Guide should precede ASIMP entry")


class SitemapIntegrationTestCase(unittest.TestCase):
    """Tests for sitemaps txt/xml integration."""

    def test_text_sitemaps_contain_expected_urls(self) -> None:
        for path in [DOCS_SITEMAP_TXT, ROOT_SITEMAP_TXT]:
            with self.subTest(path=path):
                content = _read(path)
                self.assertIn(GH_URL, content)
                self.assertIn(GB_URL, content)

    def test_xml_sitemaps_contain_expected_locs(self) -> None:
        for path in [DOCS_SITEMAP_XML, ROOT_SITEMAP_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                locs = [
                    loc.text
                    for loc in root.findall(f"{SITEMAP_NS}url/{SITEMAP_NS}loc")
                ]
                self.assertIn(GH_URL, locs)

    def test_xml_sitemap_entry_has_expected_priority_and_changefreq(self) -> None:
        tree = ET.parse(ROOT_SITEMAP_XML)
        root = tree.getroot()
        for url_node in root.findall(f"{SITEMAP_NS}url"):
            loc_node = url_node.find(f"{SITEMAP_NS}loc")
            if loc_node is not None and loc_node.text == GH_URL:
                changefreq = url_node.find(f"{SITEMAP_NS}changefreq")
                priority = url_node.find(f"{SITEMAP_NS}priority")
                self.assertEqual(changefreq.text, "weekly")
                self.assertEqual(priority.text, "0.6")
                return
        self.fail(f"Could not locate <url> entry for {GH_URL} in sitemap.xml")


class LlmsContextXmlIntegrationTestCase(unittest.TestCase):
    """Tests for llms-context.xml / docs/llms-context.xml integration."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root_content = _read(ROOT_LLMS_CONTEXT_XML)
        cls.docs_content = _read(DOCS_LLMS_CONTEXT_XML)

    def test_files_exist(self) -> None:
        self.assertTrue(os.path.isfile(ROOT_LLMS_CONTEXT_XML))
        self.assertTrue(os.path.isfile(DOCS_LLMS_CONTEXT_XML))

    def test_root_and_docs_copies_are_identical(self) -> None:
        self.assertEqual(self.root_content, self.docs_content)

    def test_xml_is_well_formed(self) -> None:
        try:
            ET.parse(ROOT_LLMS_CONTEXT_XML)
        except ET.ParseError as e:
            self.fail(f"llms-context.xml is not valid XML: {e}")

    def test_document_node_attributes_match_expected_metadata(self) -> None:
        tree = ET.parse(ROOT_LLMS_CONTEXT_XML)
        root = tree.getroot()
        matches = [
            doc for doc in root.findall(".//document")
            if doc.get("title") == SHORT_TITLE
        ]
        self.assertEqual(len(matches), 1, f"Expected exactly one document node titled '{SHORT_TITLE}'")

        doc_node = matches[0]
        self.assertEqual(doc_node.get("url"), MD_URL)
        self.assertEqual(doc_node.get("desc"), DESC)
        self.assertIn("Flowise", doc_node.text or "")
        self.assertIn("class AiProcessingService", doc_node.text or "")


class LlmsFullTxtIntegrationTestCase(unittest.TestCase):
    """Tests for llms-full.txt / docs/llms-full.txt integration."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root_content = _read(ROOT_LLMS_FULL_TXT)
        cls.docs_content = _read(DOCS_LLMS_FULL_TXT)

    def test_files_exist(self) -> None:
        self.assertTrue(os.path.isfile(ROOT_LLMS_FULL_TXT))
        self.assertTrue(os.path.isfile(DOCS_LLMS_FULL_TXT))

    def test_root_and_docs_copies_are_identical(self) -> None:
        self.assertEqual(self.root_content, self.docs_content)

    def test_contains_section_heading_and_description(self) -> None:
        self.assertIn(f"## {SHORT_TITLE}", self.root_content)
        self.assertIn(f"*{DESC}*", self.root_content)
        self.assertIn(f"# {HEADING_TITLE}", self.root_content)


class GenerateSitemapsOrderingUnitTestCase(unittest.TestCase):
    """Direct unit tests for generate_sitemaps.sort_relative_paths ordering."""

    def test_ai_processing_stack_listed_in_original_order_source(self) -> None:
        with open(GENERATE_SITEMAPS_SCRIPT, encoding="utf-8") as f:
            script_content = f.read()
        self.assertIn('"engineering/ai-processing-stack.md"', script_content)

    def test_sort_relative_paths_orders_ai_processing_stack_correctly(self) -> None:
        # Shuffle the three relevant, already-known paths and confirm sort_relative_paths
        # restores the canonical order: opentofu-migration -> ai-processing-stack -> asimp.
        shuffled = [
            "engineering/asimp-for-ai-agents.md",
            "engineering/ai-processing-stack.md",
            "engineering/opentofu-migration.md",
        ]
        result = generate_sitemaps.sort_relative_paths(shuffled)
        self.assertEqual(
            result,
            [
                "engineering/opentofu-migration.md",
                "engineering/ai-processing-stack.md",
                "engineering/asimp-for-ai-agents.md",
            ],
        )

    def test_sort_relative_paths_is_stable_when_only_new_path_supplied(self) -> None:
        # Boundary case: a single known path should sort deterministically on its own.
        result = generate_sitemaps.sort_relative_paths(["engineering/ai-processing-stack.md"])
        self.assertEqual(result, ["engineering/ai-processing-stack.md"])

    def test_sort_relative_paths_places_unknown_paths_after_known_ones(self) -> None:
        # Negative/boundary case: an unrecognized file path (not in original_order)
        # must sort after known engineering docs rather than raising or interleaving.
        result = generate_sitemaps.sort_relative_paths(
            [
                "engineering/zzz-not-in-original-order.md",
                "engineering/ai-processing-stack.md",
                "engineering/opentofu-migration.md",
            ]
        )
        self.assertEqual(
            result,
            [
                "engineering/opentofu-migration.md",
                "engineering/ai-processing-stack.md",
                "engineering/zzz-not-in-original-order.md",
            ],
        )


if __name__ == "__main__":
    unittest.main()
