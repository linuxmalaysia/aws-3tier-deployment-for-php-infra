#!/usr/bin/env python3
"""Unit tests for the Google Jules Platform Guide documentation.

This test suite verifies:
- File presence and OKF v0.1 frontmatter metadata for ``docs/jules-platform-guide.md``.
- Structural content and required Diátaxis headings.
- Index registrations in ``docs/index.md``, ``docs/SUMMARY.md``, ``SUMMARY.md``, and ``llms.txt``.
- Sitemap indexing in ``sitemap.txt`` and ``sitemap.xml``.
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

JULES_GUIDE_PATH = os.path.join(REPO_ROOT, "docs", "jules-platform-guide.md")
INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
DOCS_SUMMARY_PATH = os.path.join(REPO_ROOT, "docs", "SUMMARY.md")
ROOT_SUMMARY_PATH = os.path.join(REPO_ROOT, "SUMMARY.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")

ROOT_SITEMAP_TXT = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_TXT = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_XML = os.path.join(REPO_ROOT, "sitemap.xml")
DOCS_SITEMAP_XML = os.path.join(REPO_ROOT, "docs", "sitemap.xml")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
GH_URL = "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/jules-platform-guide.html"
GB_URL = "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/jules-platform-guide"


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


class TestJulesPlatformGuideFrontMatter(unittest.TestCase):
    """Tests for the OKF v0.1 front matter of docs/jules-platform-guide.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(JULES_GUIDE_PATH)
        cls.front_matter, cls.body_text = _parse_front_matter(cls.content)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(JULES_GUIDE_PATH))

    def test_starts_with_front_matter_delimiter(self):
        self.assertTrue(self.content.startswith("---\n"))

    def test_required_okf_fields_present(self):
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_layout_is_default(self):
        self.assertEqual(self.front_matter["layout"], "default")

    def test_okf_version_is_expected_value(self):
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_type_field_value(self):
        self.assertEqual(self.front_matter["type"], "Technical Reference Guide")

    def test_title_field_value(self):
        self.assertEqual(
            self.front_matter["title"],
            "Autonomous AI Pair-Programming & Multi-Agent Operations with Google Jules",
        )

    def test_topics_contain_jules_and_ai_agents(self):
        topics = self.front_matter["topics"]
        self.assertIn("jules", topics)
        self.assertIn("ai-agents", topics)
        self.assertIn("dsom", topics)
        self.assertIn("antigravity", topics)

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        self.assertEqual(heading_match.group(1).strip(), self.front_matter["title"])


class TestJulesPlatformGuideContentStructure(unittest.TestCase):
    """Tests for the structural content of docs/jules-platform-guide.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(JULES_GUIDE_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn(
            "# Autonomous AI Pair-Programming & Multi-Agent Operations with Google Jules",
            self.content,
        )

    def test_required_diataxis_sections_present(self):
        headings = [
            "## 1. Overview & Engineering Philosophy",
            "## 2. Step-by-Step Build & Implementation Log",
            "## 3. Collaborative Engineering via GitHub PR Comments",
            "## 4. Advanced Interoperability: Jules API, CLI, & Google Antigravity",
            "## 5. Why Developers Fall in Love with Google Jules",
            "## 6. Verification & Quality Gates",
        ]
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)

    def test_mentions_key_frameworks_and_tools(self):
        self.assertIn("OpenTofu", self.content)
        self.assertIn("Ansible", self.content)
        self.assertIn("IMDSv2", self.content)
        self.assertIn("Termux", self.content)
        self.assertIn("Google Antigravity", self.content)

    def test_concludes_with_dsom_footer(self):
        self.assertIn(
            "*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-05*",
            self.content,
        )


class TestJulesPlatformGuideIndexIntegrations(unittest.TestCase):
    """Tests for index links in docs/index.md, SUMMARY files, and llms.txt."""

    def test_index_md_contains_link(self):
        content = _read(INDEX_PATH)
        self.assertIn("jules-platform-guide.html", content)

    def test_docs_summary_contains_link(self):
        content = _read(DOCS_SUMMARY_PATH)
        self.assertIn("jules-platform-guide.md", content)

    def test_root_summary_contains_link(self):
        content = _read(ROOT_SUMMARY_PATH)
        self.assertIn("docs/jules-platform-guide.md", content)

    def test_llms_txt_contains_entry(self):
        content = _read(LLMS_PATH)
        self.assertIn("docs/jules-platform-guide.md", content)


class TestJulesPlatformGuideSitemapIntegrations(unittest.TestCase):
    """Tests for sitemap indexing of the new guide."""

    def test_text_sitemaps_contain_expected_urls(self):
        for path in [DOCS_SITEMAP_TXT, ROOT_SITEMAP_TXT]:
            with self.subTest(path=path):
                content = _read(path)
                self.assertIn(GH_URL, content)
                self.assertIn(GB_URL, content)

    def test_xml_sitemaps_contain_expected_locs(self):
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
