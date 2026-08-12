#!/usr/bin/env python3
"""Unit tests for the ASIMP for AI Agents documentation added in this PR.

This PR introduces a new documentation page:
* ``docs/engineering/asimp-for-ai-agents.md``

And integrates it across several files:
* ``docs/index.md``       -- adds a bulleted link pointing at
  ``engineering/asimp-for-ai-agents.html``.
* ``llms.txt``            -- adds an AI-agent index entry pointing at
  ``docs/engineering/asimp-for-ai-agents.md``.
* ``sitemap.txt`` / ``docs/sitemap.txt``   -- adds GitHub Pages and GitBook
  URLs for the new page.
* ``sitemap.xml`` / ``docs/sitemap.xml``   -- adds a ``<url>`` entry for the
  new page.

These files are treated as plain text/XML (rather than requiring a live
Jekyll build) to stay dependency free.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_asimp_for_ai_agents_docs
"""
import os
import re
import sys
import unittest
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import prepare_docs  # noqa: E402
import generate_sitemaps  # noqa: E402

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
ASIMP_AI_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "asimp-for-ai-agents.md")
ROOT_SITEMAP_TXT = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_TXT = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_XML = os.path.join(REPO_ROOT, "sitemap.xml")
DOCS_SITEMAP_XML = os.path.join(REPO_ROOT, "docs", "sitemap.xml")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

GH_BASE = "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
GB_BASE = "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/"

GH_URL = GH_BASE + "engineering/asimp-for-ai-agents.html"
GB_URL = GB_BASE + "engineering/asimp-for-ai-agents"


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_front_matter(content):
    stripped = content.lstrip()
    parts = stripped.split("---", 2)
    front_matter_text = parts[1]
    body_text = parts[2]
    front_matter = prepare_docs.parse_yaml_front_matter(front_matter_text)
    return front_matter, body_text


class AsimpAiFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of docs/engineering/asimp-for-ai-agents.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ASIMP_AI_PATH)
        cls.front_matter, cls.body_text = _parse_front_matter(cls.content)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(ASIMP_AI_PATH))

    def test_starts_with_front_matter_delimiter(self):
        self.assertTrue(self.content.startswith("---\n"))

    def test_required_okf_fields_present(self):
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_layout_is_default(self):
        self.assertEqual(self.front_matter["layout"], "default")

    def test_okf_version_is_expected_value(self):
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_title_field_value(self):
        self.assertEqual(
            self.front_matter["title"],
            "ASIMP for AI Agents: Cognitive Twin Integration & Persistent Memory Guide",
        )

    def test_type_matches_prepare_docs_inference(self):
        inferred_type = prepare_docs.infer_okf_type(
            "docs/engineering/asimp-for-ai-agents.md"
        )
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_match_authored_values_exactly(self):
        self.assertEqual(
            self.front_matter["topics"],
            ["security", "compliance", "ai-agents", "dsom", "asimp"],
        )

    def test_timestamp_matches_iso8601_with_offset(self):
        self.assertRegex(
            self.front_matter["timestamp"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$",
        )

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        self.assertEqual(heading_match.group(1).strip(), self.front_matter["title"])


class AsimpAiContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of docs/engineering/asimp-for-ai-agents.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ASIMP_AI_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn(
            "# ASIMP for AI Agents: Cognitive Twin Integration & Persistent Memory Guide",
            self.content,
        )

    def test_sections_present(self):
        headings = [
            "## 1. Executive Summary & Core Philosophy",
            "## 2. Spatial Memory Anchors (`.agents/brain/` & Gateway)",
            "## 3. The 5-Step Local Knowledge-First Discovery Protocol",
            "## 4. Token Performance & Progressive Disclosure",
            "## 5. Step-by-Step Implementation Sequence of ASIMP with DSOM",
            "## 6. Verification and Audit Ledger",
        ]
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)

    def test_mentions_dsom_and_asimp(self):
        self.assertIn("Deep State of Mind", self.content)
        self.assertIn("ASIMP", self.content)

    def test_mentions_agents_and_brain_folders(self):
        self.assertIn(".agents/AGENTS.md", self.content)
        self.assertIn("AGENTS.md", self.content)
        self.assertIn(".agents/brain/", self.content)


class IndexMdIntegrationTestCase(unittest.TestCase):
    """Tests for index.md link and placement."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)

    def test_link_present(self):
        self.assertIn(
            "[ASIMP for AI Agents: Cognitive Twin Integration & Persistent Memory Guide]"
            "(engineering/asimp-for-ai-agents.html)",
            self.content,
        )

    def test_appears_in_deployment_cicd_section(self) -> None:
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n### |\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[ASIMP for AI Agents: Cognitive Twin Integration & Persistent Memory Guide]"
            "(engineering/asimp-for-ai-agents.html)",
            section_match.group(1),
        )


class LlmsTxtIntegrationTestCase(unittest.TestCase):
    """Tests for llms.txt integration."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LLMS_PATH)

    def test_entry_present(self) -> None:
        self.assertIn(
            "[ASIMP for AI Agents](docs/engineering/asimp-for-ai-agents.md)",
            self.content,
        )


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


if __name__ == "__main__":
    unittest.main()
