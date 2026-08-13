#!/usr/bin/env python3
"""Unit tests for the SOP: Local Knowledge-First Discovery documentation.

This module provides unit tests to verify that the newly integrated SOP document:
* ``docs/engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.md``

is properly structured under OKF v0.1 standards and is consistently referenced and
indexed in:
* ``docs/SUMMARY.md`` and root ``SUMMARY.md``
* ``docs/index.md``
* ``llms.txt``, compiled ``llms-full.txt``, and ``llms-context.xml``
* Text and XML sitemaps

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_sop_knowledge_first_discovery
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

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
SOP_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "SOP-KNOWLEDGE-FIRST-DISCOVERY.md")
DOCS_SUMMARY_PATH = os.path.join(REPO_ROOT, "docs", "SUMMARY.md")
ROOT_SUMMARY_PATH = os.path.join(REPO_ROOT, "SUMMARY.md")

ROOT_LLMS_FULL = os.path.join(REPO_ROOT, "llms-full.txt")
DOCS_LLMS_FULL = os.path.join(REPO_ROOT, "docs", "llms-full.txt")
ROOT_LLMS_XML = os.path.join(REPO_ROOT, "llms-context.xml")
DOCS_LLMS_XML = os.path.join(REPO_ROOT, "docs", "llms-context.xml")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _read(path):
    """Read and return content of a file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_front_matter(content):
    """Parse OKF front matter from markdown content."""
    stripped = content.lstrip()
    parts = stripped.split("---", 2)
    front_matter_text = parts[1]
    body_text = parts[2]
    front_matter = prepare_docs.parse_yaml_front_matter(front_matter_text)
    return front_matter, body_text


class SopFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of the SOP-KNOWLEDGE-FIRST-DISCOVERY.md file."""

    @classmethod
    def setUpClass(cls):
        """Set up test inputs by reading the SOP file."""
        cls.content = _read(SOP_PATH)
        cls.front_matter, cls.body_text = _parse_front_matter(cls.content)

    def test_file_exists(self):
        """Verify the SOP document exists on disk."""
        self.assertTrue(os.path.isfile(SOP_PATH))

    def test_starts_with_front_matter_delimiter(self):
        """Ensure file starts with the standard front matter delimiter."""
        self.assertTrue(self.content.startswith("---\n"))

    def test_required_okf_fields_present(self):
        """Check presence of all required OKF fields."""
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_layout_is_default(self):
        """Verify layout is default."""
        self.assertEqual(self.front_matter["layout"], "default")

    def test_okf_version_is_expected_value(self):
        """Verify OKF version is 0.1."""
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_title_field_value(self):
        """Verify title field is set."""
        self.assertEqual(
            self.front_matter["title"],
            "SOP: Knowledge-First Discovery & Context Preservation Protocol",
        )

    def test_type_matches_configured(self):
        """Verify correct custom OKF type is set."""
        self.assertEqual(self.front_matter["type"], "standard_operating_procedure")


class SopIntegrationTestCase(unittest.TestCase):
    """Tests for indexing and registration consistency across sitemaps and indexes."""

    def test_summaries_contain_sop(self):
        """Verify both summary files index the SOP guide."""
        docs_summary = _read(DOCS_SUMMARY_PATH)
        root_summary = _read(ROOT_SUMMARY_PATH)

        self.assertIn(
            "* [SOP: Local Knowledge-First Discovery](engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.md)",
            docs_summary,
        )
        self.assertIn(
            "* [SOP: Local Knowledge-First Discovery](docs/engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.md)",
            root_summary,
        )

    def test_index_contains_sop_html_link(self):
        """Verify index.md references the compiled HTML file under Deployment & CI/CD."""
        index_content = _read(INDEX_PATH)
        self.assertIn(
            "(engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.html)",
            index_content,
        )

    def test_llms_txt_contains_sop_md_link(self):
        """Verify llms.txt references the SOP markdown file."""
        llms_content = _read(LLMS_PATH)
        self.assertIn(
            "[SOP: Local Knowledge-First Discovery](docs/engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.md)",
            llms_content,
        )

    def test_compiled_llms_assets_contain_sop_content(self):
        """Verify both full text and XML assets compile the SOP contents."""
        for path in [ROOT_LLMS_FULL, DOCS_LLMS_FULL]:
            with self.subTest(path=path):
                content = _read(path)
                self.assertIn("Local Knowledge-First Discovery & OKF Context Protocol", content)
                self.assertIn("Standard Operating Procedure detailing the 5-step local discovery flow", content)

        for path in [ROOT_LLMS_XML, DOCS_LLMS_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                doc_node = root.find(".//document[@url='docs/engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.md']")
                self.assertIsNotNone(doc_node, f"SOP document node missing in {path}")
                self.assertIn("Executive Intent", doc_node.text)


if __name__ == "__main__":
    unittest.main()
