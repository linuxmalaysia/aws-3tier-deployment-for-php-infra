#!/usr/bin/env python3
"""Acceptance tests for the Hybrid Integration: AWS Site-to-Site VPN vs. On-Premises
Fusio API Gateway documentation added in this PR.

This PR introduces a new documentation page
(``docs/engineering/onprem-vpn-vs-fusio-api.md``) and wires it up across:

* ``docs/index.md``                     -- adds a bullet link pointing at
  ``engineering/onprem-vpn-vs-fusio-api.html`` under "Deployment & CI/CD".
* ``docs/SUMMARY.md`` & ``SUMMARY.md``   -- adds GitBook TOC entries.
* ``llms.txt``                           -- adds an entry for LLM indexing.
* ``sitemap.txt`` / ``sitemap.xml``      -- adds URL entries for the new page.

Run with:
    python3 -m unittest discover -s tests -p 'test_onprem_vpn_vs_fusio_api_docs.py'
"""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
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

    def test_front_matter_starts_on_first_line_without_bom_or_whitespace(self):
        self.assertTrue(self.content.startswith("---\n"))
        self.assertIn("\n---\n", self.content[4:])

    def test_layout_and_timestamp_are_publishable(self):
        self.assertEqual(self.front_matter["layout"], "default")
        timestamp = datetime.fromisoformat(self.front_matter["timestamp"])
        self.assertIsNotNone(timestamp.utcoffset())


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
        self.assertIn("USD", self.content)
        self.assertIn("MYR", self.content)
        self.assertIn("RM", self.content)
        self.assertIn("$", self.content)

    def test_contains_option_one_plus_fusio_tandem_recommendation(self):
        self.assertIn("Option 1 + Fusio in tandem", self.content)

    def test_footer_contains_copyright_and_license(self):
        self.assertIn("Copyright © 2005 - 2026 Harisfazillah Jamel", self.content)
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

    def test_each_navigation_entry_resolves_once_to_the_source_page(self):
        for path in (INDEX_PATH, DOCS_SUMMARY_PATH, ROOT_SUMMARY_PATH, LLMS_TXT_PATH):
            with self.subTest(path=os.path.relpath(path, REPO_ROOT)):
                links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", _read(path))
                targets = [url for url in links if "onprem-vpn-vs-fusio-api" in url]
                self.assertEqual(len(targets), 1, targets)
                target = targets[0]
                if path == INDEX_PATH:
                    self.assertTrue(target.endswith(".html"), target)
                    target = target[:-5] + ".md"
                self.assertEqual(
                    os.path.abspath(os.path.join(os.path.dirname(path), target)),
                    DOC_PATH,
                )


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

    def test_text_sitemaps_publish_exactly_the_two_canonical_urls(self):
        for path in (ROOT_SITEMAP_TXT_PATH, DOCS_SITEMAP_TXT_PATH):
            with self.subTest(path=os.path.relpath(path, REPO_ROOT)):
                urls = [line.strip() for line in _read(path).splitlines()
                        if "onprem-vpn-vs-fusio-api" in line]
                # Reject duplicates, source .md URLs, and malformed suffixes.
                self.assertCountEqual(urls, [EXPECTED_GH_URL, EXPECTED_GB_URL])

    def test_xml_sitemaps_publish_one_canonical_entry_with_source_date(self):
        front_matter = prepare_docs.parse_yaml_front_matter(_read(DOC_PATH).split("---", 2)[1])
        expected_date = datetime.fromisoformat(front_matter["timestamp"]).date().isoformat()
        for path in (ROOT_SITEMAP_XML_PATH, DOCS_SITEMAP_XML_PATH):
            with self.subTest(path=os.path.relpath(path, REPO_ROOT)):
                root = ET.parse(path).getroot()
                entries = [node for node in root.findall(f"{SITEMAP_XML_NS}url")
                           if "onprem-vpn-vs-fusio-api" in
                           (node.findtext(f"{SITEMAP_XML_NS}loc") or "")]
                self.assertEqual(len(entries), 1)
                entry = entries[0]
                for field, expected in (("loc", EXPECTED_GH_URL),
                                        ("lastmod", expected_date),
                                        ("changefreq", "weekly"), ("priority", "0.6")):
                    self.assertEqual(entry.findtext(f"{SITEMAP_XML_NS}{field}"), expected)


class OnpremVpnVsFusioApiCostingTestCase(unittest.TestCase):
    """Check the published estimates against their stated assumptions, not live prices."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(DOC_PATH)

    def table(self, option):
        match = re.search(
            rf"^### Option {option} Cost Profile[^\n]*\n(.*?)(?=^### |^## |\Z)",
            self.content, re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match, f"Missing cost profile for option {option}")
        rows = [tuple(cell.strip().replace("**", "") for cell in line.strip("|").split("|"))
                for line in match.group(1).splitlines() if line.startswith("|")]
        self.assertGreater(len(rows), 2)
        for row in rows:
            self.assertEqual(len(row), 4, row)
        labels = [row[0] for row in rows[2:]]
        self.assertEqual(len(labels), len(set(labels)), "Duplicate cost components")
        return {row[0]: row[1:] for row in rows[2:]}

    def amounts(self, cell, currency):
        values = re.findall(rf"{re.escape(currency)}\s*(\d+(?:\.\d+)?)", cell)
        self.assertTrue(values, f"Missing {currency} amount in {cell!r}")
        return [Decimal(value) for value in values]

    def test_estimate_assumptions_are_explicit(self):
        self.assertIn("1 USD = 4.50 MYR", self.content)
        self.assertIn("730-hour month", self.content)
        self.assertIn("`ap-southeast-5`", self.content)

    def test_hourly_fixed_costs_include_both_vpn_endpoints(self):
        cases = (
            (1, "AWS Site-to-Site VPN Connection", Decimal("0.05"), 1),
            (1, "Tunnel Public IPv4 Addresses (2 endpoints)", Decimal("0.005"), 2),
            (2, "AWS NAT Gateway (1 AZ)", Decimal("0.045"), 1),
            (2, "Public IPv4 Allocation (Elastic IP)", Decimal("0.005"), 1),
        )
        for option, label, hourly_rate, quantity in cases:
            with self.subTest(option=option, component=label):
                metric, usd, _ = self.table(option)[label]
                self.assertEqual(self.amounts(metric, "$")[0], hourly_rate)
                self.assertEqual(self.amounts(usd, "$"), [hourly_rate * 730 * quantity])

    def test_every_myr_estimate_converts_usd_with_cent_rounding(self):
        for option in (1, 2):
            for label, (_, usd, myr) in self.table(option).items():
                with self.subTest(option=option, component=label):
                    expected = [(amount * Decimal("4.50")).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP)
                        for amount in self.amounts(usd, "$")]
                    self.assertEqual(self.amounts(myr, "RM"), expected)

    def test_fixed_baselines_exclude_bandwidth_and_processing(self):
        components = {
            1: ("AWS Site-to-Site VPN Connection", "Tunnel Public IPv4 Addresses (2 endpoints)",
                "Virtual Private Gateway (VGW)"),
            2: ("AWS NAT Gateway (1 AZ)", "Public IPv4 Allocation (Elastic IP)"),
        }
        for option, labels in components.items():
            with self.subTest(option=option):
                rows = self.table(option)
                total = sum(self.amounts(rows[label][1], "$")[0] for label in labels)
                self.assertEqual(self.amounts(rows["Total Baseline (Excluding Bandwidth)"][1], "$"),
                                 [total])

    def test_included_gateway_and_inbound_transfer_are_free(self):
        rows = self.table(1)
        for label in ("Virtual Private Gateway (VGW)", "Data Transfer IN (On-Prem to AWS)"):
            with self.subTest(component=label):
                self.assertEqual(self.amounts(rows[label][1], "$"), [Decimal("0")])
                self.assertEqual(self.amounts(rows[label][2], "RM"), [Decimal("0")])

    def test_variable_costs_use_100_gb_and_preserve_egress_range(self):
        for option, label in ((1, "Data Transfer OUT (AWS to On-Prem)"),
                              (2, "Internet Egress (AWS to On-Prem)"),
                              (2, "NAT Data Processing")):
            with self.subTest(option=option, component=label):
                metric, usd, myr = self.table(option)[label]
                self.assertIn("per 100 GB", usd)
                self.assertIn("per 100 GB", myr)
                self.assertEqual(self.amounts(usd, "$"),
                                 [rate * 100 for rate in self.amounts(metric, "$")])

    def test_recommendation_repeats_baselines_from_cost_tables(self):
        row = next(line for line in self.content.splitlines()
                   if line.startswith("| **AWS Fixed Baseline Cost** |"))
        columns = row.strip("|").split("|")[1:]
        for option, cell in enumerate(columns, 1):
            with self.subTest(option=option):
                _, usd, myr = self.table(option)["Total Baseline (Excluding Bandwidth)"]
                self.assertEqual(self.amounts(cell, "$")[0], self.amounts(usd, "$")[0])
                self.assertEqual(self.amounts(cell, "RM"), self.amounts(myr, "RM"))


class OnpremVpnVsFusioApiCompiledAssetsTestCase(unittest.TestCase):
    """Validate only this page's entries in the four changed LLM artifacts."""

    @classmethod
    def setUpClass(cls):
        cls.body = _read(DOC_PATH).split("---", 2)[2].strip()
        cls.doc_url = "docs/engineering/onprem-vpn-vs-fusio-api.md"

    def test_xml_copies_embed_the_complete_unescaped_source_exactly_once(self):
        for prefix in ("", "docs"):
            with self.subTest(directory=prefix or "root"):
                root = ET.parse(os.path.join(REPO_ROOT, prefix, "llms-context.xml")).getroot()
                entries = [node for node in root.findall(".//document")
                           if "onprem-vpn-vs-fusio-api" in node.get("url", "")]
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0].get("url"), self.doc_url)
                self.assertEqual((entries[0].text or "").strip(), self.body)

    def test_xml_titles_and_descriptions_match_the_llm_index(self):
        match = re.search(r"^- \[([^\]]+)\]\(" + re.escape(self.doc_url) + r"\) : (.+)$",
                          _read(LLMS_TXT_PATH), re.MULTILINE)
        self.assertIsNotNone(match)
        for prefix in ("", "docs"):
            with self.subTest(directory=prefix or "root"):
                root = ET.parse(os.path.join(REPO_ROOT, prefix, "llms-context.xml")).getroot()
                entry = root.find(f".//document[@url='{self.doc_url}']")
                self.assertIsNotNone(entry)
                self.assertEqual(entry.get("title"), match.group(1))
                self.assertEqual(entry.get("desc"), match.group(2))

    def test_full_text_copies_embed_the_complete_source_exactly_once(self):
        for prefix in ("", "docs"):
            with self.subTest(directory=prefix or "root"):
                content = _read(os.path.join(REPO_ROOT, prefix, "llms-full.txt"))
                self.assertEqual(content.count(self.body), 1)
                heading = "# Hybrid Integration: AWS Site-to-Site VPN vs. On-Premises Fusio API Gateway"
                self.assertEqual(content.splitlines().count(heading), 1)


if __name__ == "__main__":
    unittest.main()
