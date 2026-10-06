#!/usr/bin/env python3
"""Unit tests for the Hybrid Integration: AWS Site-to-Site VPN vs. On-Premises
Fusio API Gateway documentation added in this PR.

This PR introduces a new documentation page
(``docs/engineering/onprem-vpn-vs-fusio-api.md``) and wires it up across:

* ``docs/index.md``                     -- adds a bullet link pointing at
  ``engineering/onprem-vpn-vs-fusio-api.html`` under "Deployment & CI/CD".
* ``docs/SUMMARY.md`` & ``SUMMARY.md``   -- adds GitBook TOC entries.
* ``llms.txt``                           -- adds an entry for LLM indexing.
* ``sitemap.txt`` / ``sitemap.xml``      -- adds URL entries for the new page.

Run with:
    python3 -m unittest discover -s tests
or:
    pytest tests/test_onprem_vpn_vs_fusio_api_docs.py
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
DOC_PATH = os.path.join(
    REPO_ROOT, "docs", "engineering", "onprem-vpn-vs-fusio-api.md"
)
DOCS_SUMMARY_PATH = os.path.join(REPO_ROOT, "docs", "SUMMARY.md")
ROOT_SUMMARY_PATH = os.path.join(REPO_ROOT, "SUMMARY.md")
LLMS_TXT_PATH = os.path.join(REPO_ROOT, "llms.txt")

DOCS_SITEMAP_TXT_PATH = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_TXT_PATH = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_XML_PATH = os.path.join(REPO_ROOT, "docs", "sitemap.xml")
ROOT_SITEMAP_XML_PATH = os.path.join(REPO_ROOT, "sitemap.xml")

EXPECTED_GH_URL = (
    "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
    "engineering/onprem-vpn-vs-fusio-api.html"
)
EXPECTED_GB_URL = (
    "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/"
    "docs/engineering/onprem-vpn-vs-fusio-api"
)

SITEMAP_XML_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class IndexMdOnpremVpnVsFusioApiLinkTestCase(unittest.TestCase):
    """Tests for the link in docs/index.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)

    def test_link_present(self):
        self.assertIn(
            "[Hybrid Integration: AWS Site-to-Site VPN vs. On-Premises Fusio API Gateway]"
            "(engineering/onprem-vpn-vs-fusio-api.html)",
            self.content,
        )

    def test_link_in_deployment_cicd_section(self):
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n### |\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[Hybrid Integration: AWS Site-to-Site VPN vs. On-Premises Fusio API Gateway]"
            "(engineering/onprem-vpn-vs-fusio-api.html)",
            section_match.group(1),
        )

    def test_target_file_exists(self):
        self.assertTrue(os.path.isfile(DOC_PATH))


class OnpremVpnVsFusioApiFrontMatterTestCase(unittest.TestCase):
    """Tests for OKF front matter of docs/engineering/onprem-vpn-vs-fusio-api.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(DOC_PATH)
        stripped = cls.content.lstrip()
        parts = stripped.split("---", 2)
        cls.front_matter_text = parts[1]
        cls.body_text = parts[2]
        cls.front_matter = prepare_docs.parse_yaml_front_matter(
            cls.front_matter_text
        )

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(DOC_PATH))

    def test_required_okf_fields_present(self):
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_okf_version_is_0_1(self):
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_title_field_value(self):
        self.assertEqual(
            self.front_matter["title"],
            "Hybrid Integration: AWS Site-to-Site VPN vs. On-Premises Fusio API Gateway",
        )

    def test_topics_list(self):
        self.assertEqual(
            self.front_matter["topics"],
            ["aws", "3-tier", "vpn", "fusio", "hybrid"],
        )


class OnpremVpnVsFusioApiContentStructureTestCase(unittest.TestCase):
    """Tests for structural content of docs/engineering/onprem-vpn-vs-fusio-api.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(DOC_PATH)

    def test_contains_hybrid_architecture_marker(self):
        self.assertIn("**[HYBRID ARCHITECTURE & FINANCIAL EVALUATION]**", self.content)

    def test_contains_architectural_comparison_heading(self):
        self.assertIn("## Architectural Comparison", self.content)

    def test_contains_aws_cost_breakdown_heading(self):
        self.assertIn("## AWS Cost Breakdown", self.content)

    def test_contains_technical_recommendation_heading(self):
        self.assertIn("## Technical Recommendation", self.content)

    def test_contains_notice_and_disclaimer_heading(self):
        self.assertIn("## Notice & Disclaimer", self.content)

    def test_contains_usd_and_myr_costing_data(self):
        self.assertIn("~$36.00", self.content)
        self.assertIn("~RM 162.00", self.content)
        self.assertIn("~$36.50", self.content)
        self.assertIn("~RM 164.25", self.content)

    def test_contains_option_one_plus_fusio_tandem_recommendation(self):
        self.assertIn("Option 1 + Fusio in tandem", self.content)

    def test_footer_contains_copyright_and_license(self):
        self.assertIn("Copyright © 2005 - 2026 Harisfazillary Jamel", self.content)
        self.assertIn("GNU General Public License v3.0", self.content)


class SummaryAndLlmsRegistrationTestCase(unittest.TestCase):
    """Tests registration in SUMMARY.md and llms.txt."""

    def test_docs_summary_contains_entry(self):
        content = _read(DOCS_SUMMARY_PATH)
        self.assertIn("engineering/onprem-vpn-vs-fusio-api.md", content)

    def test_root_summary_contains_entry(self):
        content = _read(ROOT_SUMMARY_PATH)
        self.assertIn("docs/engineering/onprem-vpn-vs-fusio-api.md", content)

    def test_llms_txt_contains_entry(self):
        content = _read(LLMS_TXT_PATH)
        self.assertIn("docs/engineering/onprem-vpn-vs-fusio-api.md", content)


class SitemapArtifactsOnpremVpnVsFusioApiTestCase(unittest.TestCase):
    """Tests sitemap.txt and sitemap.xml entries."""

    def test_gh_url_present_in_root_sitemap_txt(self):
        content = _read(ROOT_SITEMAP_TXT_PATH)
        self.assertIn(EXPECTED_GH_URL, content)

    def test_gb_url_present_in_root_sitemap_txt(self):
        content = _read(ROOT_SITEMAP_TXT_PATH)
        self.assertIn(EXPECTED_GB_URL, content)

    def test_url_node_present_in_root_sitemap_xml(self):
        tree = ET.parse(ROOT_SITEMAP_XML_PATH)
        root = tree.getroot()
        locs = [
            loc.text
            for loc in root.findall(f"{SITEMAP_XML_NS}url/{SITEMAP_XML_NS}loc")
        ]
        self.assertIn(EXPECTED_GH_URL, locs)


if __name__ == "__main__":
    unittest.main()
