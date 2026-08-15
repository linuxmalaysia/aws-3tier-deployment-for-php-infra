#!/usr/bin/env python3
"""Unit tests for the Wazuh SIEM & XDR documentation.

This test validates:
* ``docs/engineering/wazuh-installation.md``
* Integration across ``docs/index.md``, ``SUMMARY.md``, and ``llms.txt``.
* Presence in text and XML sitemaps.

Run with:
    python3 -m unittest discover -s tests
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
SUMMARY_PATH = os.path.join(REPO_ROOT, "SUMMARY.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
WAZUH_DOC_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "wazuh-installation.md")
ROOT_SITEMAP_TXT = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_TXT = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_XML = os.path.join(REPO_ROOT, "sitemap.xml")
DOCS_SITEMAP_XML = os.path.join(REPO_ROOT, "docs", "sitemap.xml")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

GH_BASE = "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
GB_BASE = "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/"

GH_URL = GH_BASE + "engineering/wazuh-installation.html"
GB_URL = GB_BASE + "engineering/wazuh-installation"


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


class WazuhDocFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of docs/engineering/wazuh-installation.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(WAZUH_DOC_PATH)
        cls.front_matter, cls.body_text = _parse_front_matter(cls.content)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(WAZUH_DOC_PATH))

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
            "Wazuh SIEM & XDR Deployment Guide: AWS Cloud, On-Premises AlmaLinux 10 & WSL2 Demo",
        )

    def test_type_matches_prepare_docs_inference(self):
        inferred_type = prepare_docs.infer_okf_type(
            "docs/engineering/wazuh-installation.md"
        )
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_contain_expected_keywords(self):
        expected_topics = ["wazuh", "siem", "xdr", "aws", "almalinux10", "wsl2", "podman", "security"]
        for topic in expected_topics:
            self.assertIn(topic, self.front_matter["topics"])


class WazuhDocContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of docs/engineering/wazuh-installation.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(WAZUH_DOC_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn(
            "# Wazuh SIEM & XDR Deployment Guide: AWS Cloud, On-Premises AlmaLinux 10 & WSL2 Demo",
            self.content,
        )

    def test_sections_present(self):
        headings = [
            "## 🏛️ 1. Wazuh Architecture & Sizing Guidelines",
            "## 💸 2. On Cloud Plan: AWS Malaysia (`ap-southeast-5`)",
            "## 🏢 3. On-Premises Plan: AlmaLinux 10",
            "## 💻 4. WSL2 Windows 11 Plan: AlmaLinux 10 Demo Environment",
            "## 📡 5. Agent Enrollment (Linux & Windows)",
            "## 🔒 6. Security Hardening & Operational Verification",
        ]
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)

    def test_mentions_wsl2_and_almalinux(self):
        self.assertIn("AlmaLinux 10", self.content)
        self.assertIn("WSL2", self.content)
        self.assertIn("vm.max_map_count=262144", self.content)
        self.assertIn("Podman", self.content)


class IndexAndSummaryIntegrationTestCase(unittest.TestCase):
    """Tests for index.md, SUMMARY.md, and llms.txt integration."""

    def test_index_md_link_present(self):
        content = _read(INDEX_PATH)
        self.assertIn(
            "[Wazuh SIEM & XDR Deployment Guide](engineering/wazuh-installation.html)",
            content,
        )

    def test_summary_md_link_present(self):
        content = _read(SUMMARY_PATH)
        self.assertIn(
            "[Wazuh SIEM & XDR Deployment Guide](docs/engineering/wazuh-installation.md)",
            content,
        )

    def test_llms_txt_link_present(self):
        content = _read(LLMS_PATH)
        self.assertIn(
            "[Wazuh SIEM & XDR Deployment Guide](docs/engineering/wazuh-installation.md)",
            content,
        )


class SitemapIntegrationTestCase(unittest.TestCase):
    """Tests for sitemaps txt/xml integration."""

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
