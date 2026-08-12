#!/usr/bin/env python3
"""Unit and integration tests for the Disaster Recovery Option Two Malaysia documentation.

This test suite validates that the newly introduced documentation file:
* ``docs/executive/dr-option-two-malaysia.md``

adheres fully to the Open Knowledge Format (OKF) v0.1 YAML front matter contract,
includes standard footer copyright/license references, is mapped correctly from
the docs index and llms.txt, is in the navbar of _config.yml, and is successfully published in the sitemaps.
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

import prepare_docs
import generate_sitemaps

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
CONFIG_PATH = os.path.join(REPO_ROOT, "docs", "_config.yml")
DR_OPT_TWO_MD_PATH = os.path.join(REPO_ROOT, "docs", "executive", "dr-option-two-malaysia.md")
LAYOUT_PATH = os.path.join(REPO_ROOT, "docs", "_layouts", "default.html")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _read(path):
    """Utility helper to read a file from a specified path in UTF-8 format."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class DrOptionTwoMalaysiaDocsTestCase(unittest.TestCase):
    """Comprehensive test case for checking OKF front matter, footer metadata,

    content structure, and index/sitemap publication for Option Two documentation.
    """

    def test_files_exist(self):
        """Verifies that the requested Option Two documentation file is present."""
        self.assertTrue(os.path.isfile(DR_OPT_TWO_MD_PATH))

    def test_front_matter_okf_dr_option_two(self):
        """Validates the OKF v0.1 front matter rules for dr-option-two-malaysia.md."""
        content = _read(DR_OPT_TWO_MD_PATH)
        self.assertTrue(content.startswith("---\n"))
        parts = content.split("---", 2)
        fm = prepare_docs.parse_yaml_front_matter(parts[1])
        self.assertEqual(fm["layout"], "default")
        self.assertEqual(fm["okf_version"], "0.1")
        self.assertEqual(fm["type"], "Technical Reference Guide")
        self.assertEqual(
            fm["title"],
            "DR Option Two: Malaysia Region & Cross-Account Replication Strategy",
        )
        self.assertEqual(fm["topics"], ["aws", "3-tier", "disaster-recovery", "pricing"])
        self.assertEqual(fm["timestamp"], "2026-08-11T12:00:00+08:00")

        # Assert timestamp exists and uses the required double-quoted representation in raw file
        raw_lines = parts[1].splitlines()
        timestamp_line = [line.strip() for line in raw_lines if line.strip().startswith("timestamp:")]
        self.assertTrue(len(timestamp_line) > 0)
        self.assertEqual(timestamp_line[0], 'timestamp: "2026-08-11T12:00:00+08:00"')

    def test_footer_standard_compliance(self):
        """Verifies that the new document adheres fully to the footer standards

        by containing proper Deep State of Mind (DSOM) tags, copyright lines, and GPLv3 licenses.
        """
        content = _read(DR_OPT_TWO_MD_PATH)
        self.assertIn("Deep State of Mind (DSOM) For My AI Protocol", content)
        self.assertTrue(
            "Copyright &copy; 2005 - 2026 Harisfazillah Jamel" in content or
            "Copyright © 2005 - 2026 Harisfazillah Jamel" in content,
            "Copyright line not found in dr-option-two-malaysia.md"
        )
        self.assertIn("GNU General Public License v3.0", content)
        self.assertIn("[linuxmalaysia.com](https://linuxmalaysia.com/)", content)

    def test_navbar_mapped_correctly(self):
        """Validates that 'DR Option Two Malaysia' and its URL belong to the same navbar entry."""
        config_content = _read(CONFIG_PATH)
        match = re.search(
            r'-\s*title:\s*"DR Option Two Malaysia"\s*\n\s*url:\s*"/executive/dr-option-two-malaysia\.html"',
            config_content
        )
        self.assertIsNotNone(match, "Expected 'DR Option Two Malaysia' title and url to map to the same entry")

    def test_links_in_index(self):
        """Verifies that the new documentation page is correctly linked in docs/index.md."""
        index = _read(INDEX_PATH)
        self.assertIn("[DR Option Two Malaysia and Account Separation Guide](executive/dr-option-two-malaysia.html)", index)

    def test_indexed_in_llms_txt(self):
        """Verifies that the new documentation page is correctly indexed in llms.txt."""
        llms = _read(LLMS_PATH)
        self.assertIn("[DR Option Two Malaysia](docs/executive/dr-option-two-malaysia.md)", llms)

    def test_sitemap_publication(self):
        """Verifies publication entries in both XML sitemaps and text sitemaps,

        asserting that scripts/generate_sitemaps.py regenerates them.
        """
        # Run sitemap generator to assure freshness
        generate_sitemaps.main()

        sitemaps_txt = [
            os.path.join(REPO_ROOT, "sitemap.txt"),
            os.path.join(REPO_ROOT, "docs", "sitemap.txt")
        ]
        sitemaps_xml = [
            os.path.join(REPO_ROOT, "sitemap.xml"),
            os.path.join(REPO_ROOT, "docs", "sitemap.xml")
        ]

        expected_txt_urls = [
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/executive/dr-option-two-malaysia.html",
            "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/executive/dr-option-two-malaysia"
        ]

        expected_xml_urls = [
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/executive/dr-option-two-malaysia.html"
        ]

        for s_path in sitemaps_txt:
            content = _read(s_path)
            for url in expected_txt_urls:
                self.assertEqual(content.count(url), 1, f"URL {url} count is not 1 in {s_path}")

        import datetime
        for s_path in sitemaps_xml:
            content = _read(s_path)
            for url in expected_xml_urls:
                loc_tag = f"<loc>{url}</loc>"
                self.assertEqual(content.count(loc_tag), 1, f"XML tag {loc_tag} count is not 1 in {s_path}")

            # Parse XML and validate lastmod format and values, weekly changefreq, and 0.6 priority
            tree = ET.parse(s_path)
            root = tree.getroot()
            for url in expected_xml_urls:
                url_node = None
                for u in root.findall(f"{SITEMAP_NS}url"):
                    loc = u.find(f"{SITEMAP_NS}loc")
                    if loc is not None and loc.text == url:
                        url_node = u
                        break
                self.assertIsNotNone(url_node, f"URL {url} node not found in {s_path}")
                lastmod = url_node.find(f"{SITEMAP_NS}lastmod").text
                self.assertRegex(lastmod, r"^\d{4}-\d{2}-\d{2}$")
                try:
                    datetime.date.fromisoformat(lastmod)
                except ValueError as e:
                    self.fail(f"Invalid lastmod date {lastmod} in {s_path}: {e}")

                # Validate change frequency is weekly
                changefreq = url_node.find(f"{SITEMAP_NS}changefreq")
                self.assertIsNotNone(changefreq, f"changefreq tag missing in {s_path}")
                self.assertEqual(changefreq.text, "weekly")

                # Validate priority is 0.6
                priority = url_node.find(f"{SITEMAP_NS}priority")
                self.assertIsNotNone(priority, f"priority tag missing in {s_path}")
                self.assertEqual(float(priority.text), 0.6)

    def test_document_structure_and_headings(self):
        """Verifies key structural sections exist within the document."""
        content = _read(DR_OPT_TWO_MD_PATH)
        self.assertIn("**[DEVOPS EXECUTION]**", content)
        self.assertIn("## 1. DR Option Two Architecture & Sovereignty", content)
        self.assertIn("## 2. Copying the Production Stack: Step-by-Step Mechanisms", content)
        self.assertIn("## 3. AWS CLI Infrastructure Discovery Commands", content)
        self.assertIn("## 4. Disaster Recovery Strategies under Account Separation", content)
        self.assertIn("## 5. AWS Pricing Calculator Parameters (Copy-Paste Ready)", content)
        self.assertIn("## 6. Implementation Summary", content)

    def test_pricing_calculator_tables_exist(self):
        """Verifies the tables with correct parameters are listed."""
        content = _read(DR_OPT_TWO_MD_PATH)
        self.assertIn("Tier 1: Baseline Cost-Optimized Plan", content)
        self.assertIn("Tier 2: High-Performance Enterprise Plan", content)
        self.assertIn("RDS MariaDB", content)
        self.assertIn("Valkey", content)


if __name__ == "__main__":
    unittest.main()
