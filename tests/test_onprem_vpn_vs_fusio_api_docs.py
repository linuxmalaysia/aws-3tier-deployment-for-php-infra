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

import prepare_docs  # type: ignore # noqa: E402
import generate_sitemaps  # type: ignore # noqa: E402
import generate_llms_assets  # type: ignore # noqa: E402

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
DOC_RELATIVE_PATH = "docs/engineering/onprem-vpn-vs-fusio-api.md"


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

    def test_front_matter_starts_at_first_byte(self):
        """Leading whitespace or a BOM would prevent Jekyll recognizing it."""
        self.assertTrue(self.content.startswith("---\n"))

    def test_layout_and_heading_match_publishing_metadata(self):
        self.assertEqual(self.front_matter["layout"], "default")
        self.assertEqual(
            re.findall(r"^# (.+)$", self.body_text, re.MULTILINE),
            [self.front_matter["title"]],
        )

    def test_timestamp_is_valid_and_timezone_aware(self):
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

    def test_each_navigation_link_is_unique_and_resolves_to_the_guide(self):
        for path, target in (
            (INDEX_PATH, "engineering/onprem-vpn-vs-fusio-api.html"),
            (DOCS_SUMMARY_PATH, "engineering/onprem-vpn-vs-fusio-api.md"),
            (ROOT_SUMMARY_PATH, DOC_RELATIVE_PATH),
            (LLMS_TXT_PATH, DOC_RELATIVE_PATH),
        ):
            with self.subTest(path=os.path.relpath(path, REPO_ROOT)):
                links = re.findall(r"\[([^\]\n]+)\]\(([^)\n]+)\)", _read(path))
                matches = [
                    (label, url) for label, url in links
                    if "onprem-vpn-vs-fusio-api" in url
                ]
                self.assertEqual(len(matches), 1)
                label, url = matches[0]
                self.assertTrue(label.strip())
                self.assertEqual(url, target)
                source = os.path.splitext(url)[0] + ".md"
                self.assertEqual(
                    os.path.abspath(os.path.join(os.path.dirname(path), source)),
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

    def test_both_text_sitemaps_have_exactly_the_two_canonical_urls(self):
        for path in (ROOT_SITEMAP_TXT_PATH, DOCS_SITEMAP_TXT_PATH):
            with self.subTest(path=os.path.relpath(path, REPO_ROOT)):
                urls = [
                    line for line in _read(path).splitlines()
                    if "onprem-vpn-vs-fusio-api" in line
                ]
                self.assertCountEqual(urls, [EXPECTED_GH_URL, EXPECTED_GB_URL])

    def test_both_xml_sitemaps_have_one_canonical_entry_with_metadata(self):
        timestamp = generate_sitemaps.get_file_okf_timestamp(DOC_PATH)
        self.assertIsNotNone(timestamp)
        for path in (ROOT_SITEMAP_XML_PATH, DOCS_SITEMAP_XML_PATH):
            with self.subTest(path=os.path.relpath(path, REPO_ROOT)):
                root = ET.parse(path).getroot()
                nodes = [
                    node for node in root.findall(f"{SITEMAP_XML_NS}url")
                    if "onprem-vpn-vs-fusio-api" in
                    node.findtext(f"{SITEMAP_XML_NS}loc", default="")
                ]
                self.assertEqual(len(nodes), 1)
                for field, expected in (
                    ("loc", EXPECTED_GH_URL),
                    ("lastmod", timestamp),
                    ("changefreq", "weekly"),
                    ("priority", "0.6"),
                ):
                    with self.subTest(field=field):
                        self.assertEqual(
                            nodes[0].findtext(f"{SITEMAP_XML_NS}{field}"), expected
                        )


class OnpremVpnVsFusioApiCostingTestCase(unittest.TestCase):
    """Check internal arithmetic of the estimates, without live pricing calls."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(DOC_PATH)

    def _table(self, heading):
        section = re.search(
            rf"^{re.escape(heading)}\n(.*?)(?=^## |^### |\Z)",
            self.content, re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(section, heading)
        rows = [
            [cell.strip().replace("**", "") for cell in line.strip("|").split("|")]
            for line in section.group(1).splitlines() if line.startswith("|")
        ]
        self.assertGreaterEqual(len(rows), 3, heading)
        return rows[2:]  # Skip column headings and the Markdown separator.

    def _amounts(self, cell, currency):
        amounts = re.findall(re.escape(currency) + r"\s*([\d,]+\.\d+)", cell)
        self.assertTrue(amounts, cell)
        return [Decimal(value.replace(",", "")) for value in amounts]

    def _cost_tables(self):
        return (
            self._table("### Option 1 Cost Profile (Site-to-Site VPN)"),
            self._table("### Option 2 Cost Profile (Public API over Internet)"),
        )

    def test_fixed_monthly_costs_follow_hourly_rates_and_endpoint_counts(self):
        self.assertIn("730-hour month", self.content)
        vpn, public_api = self._cost_tables()
        # The VPN has two billed tunnel addresses; the NAT gateway has one EIP.
        for row, count in ((vpn[0], 1), (vpn[1], 2),
                           (public_api[0], 1), (public_api[1], 1)):
            with self.subTest(component=row[0]):
                hourly = self._amounts(row[1], "$")[0]
                self.assertEqual(
                    self._amounts(row[2], "$"), [hourly * count * 730]
                )

    def test_table_currency_conversions_include_zero_and_range_endpoints(self):
        self.assertIn("1 USD = 4.50 MYR", self.content)
        for rows in self._cost_tables():
            for component, metric, usd, myr in rows:
                with self.subTest(component=component, metric=metric):
                    # Displayed estimates round half cents up (e.g. 16.425).
                    expected = [
                        (amount * Decimal("4.50")).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        ) for amount in self._amounts(usd, "$")
                    ]
                    self.assertEqual(self._amounts(myr, "RM"), expected)

    def test_baseline_totals_exclude_usage_based_charges(self):
        for rows in self._cost_tables():
            with self.subTest(component=rows[0][0]):
                total = sum(
                    self._amounts(row[2], "$")[0] for row in rows[:2]
                )
                self.assertIn("Excluding Bandwidth", rows[-1][0])
                self.assertEqual(self._amounts(rows[-1][2], "$"), [total])

    def test_nat_processing_cost_is_per_100_gb(self):
        rows = self._cost_tables()[1]
        matches = [row for row in rows if row[0] == "NAT Data Processing"]
        self.assertEqual(len(matches), 1)
        _, metric, usd, myr = matches[0]
        self.assertIn("/ GB", metric)
        self.assertIn("per 100 GB", usd)
        self.assertIn("per 100 GB", myr)
        self.assertEqual(
            self._amounts(usd, "$"), [self._amounts(metric, "$")[0] * 100]
        )

    def test_both_egress_estimates_apply_only_above_shared_allowance(self):
        for rows, label in zip(self._cost_tables(), (
            "Data Transfer OUT (AWS to On-Prem)", "Internet Egress (AWS to On-Prem)"
        )):
            with self.subTest(component=label):
                matches = [row for row in rows if row[0] == label]
                self.assertEqual(len(matches), 1)
                _, metric, usd, myr = matches[0]
                self.assertIn("shared 100 GB/mo", metric)
                for cell in (usd, myr):
                    self.assertIn("per 100 GB above shared allowance", cell)

    def test_recommendation_quotes_the_detailed_baselines(self):
        rows = self._table("## Technical Recommendation")
        matches = [row for row in rows if row[0] == "AWS Fixed Baseline Cost"]
        self.assertEqual(len(matches), 1)
        for summary, detail in zip(matches[0][1:], self._cost_tables()):
            with self.subTest(component=detail[0][0]):
                for currency, column in (("$", 2), ("RM", 3)):
                    self.assertEqual(
                        self._amounts(summary, currency)[0],
                        self._amounts(detail[-1][column], currency)[0],
                    )


class OnpremVpnVsFusioApiLlmExportsTestCase(unittest.TestCase):
    """Acceptance checks scoped to the new guide's four published exports."""

    @classmethod
    def setUpClass(cls):
        # Compute expected content independently of the asset stripping helper.
        cls.body = _read(DOC_PATH).split("---", 2)[2].strip()

    def _index_entry(self):
        parsed = generate_llms_assets.parse_llms_file(_read(LLMS_TXT_PATH))
        entries = [
            (section, link) for section, links in parsed.sections.items()
            for link in links if link["url"] == DOC_RELATIVE_PATH
        ]
        self.assertEqual(len(entries), 1)
        section, entry = entries[0]
        self.assertEqual(section, "Deployment, Automation, and Costing")
        self.assertTrue(entry["title"])
        self.assertTrue(entry["desc"])
        return section, entry

    def test_xml_exports_preserve_complete_body_and_index_metadata(self):
        section, entry = self._index_entry()
        for directory in (REPO_ROOT, os.path.join(REPO_ROOT, "docs")):
            with self.subTest(directory=directory):
                root = ET.parse(os.path.join(directory, "llms-context.xml")).getroot()
                nodes = root.findall(f".//document[@url='{DOC_RELATIVE_PATH}']")
                self.assertEqual(len(nodes), 1)
                node = nodes[0]
                self.assertEqual(node.get("title"), entry["title"])
                self.assertEqual(node.get("desc"), entry["desc"])
                self.assertEqual(len(node), 0, "Markdown must be escaped XML text")
                self.assertEqual(node.text.strip(), self.body)
                self.assertIn(node, root.findall(
                    f"./section[@title='{section}']/document"
                ))

    def test_full_text_exports_preserve_complete_body_without_front_matter(self):
        _, entry = self._index_entry()
        heading = f"## {entry['title']}\n"
        expected = f"{heading}*{entry['desc']}*\n\n{self.body}\n\n---"
        for directory in (REPO_ROOT, os.path.join(REPO_ROOT, "docs")):
            with self.subTest(directory=directory):
                content = _read(os.path.join(directory, "llms-full.txt"))
                self.assertEqual(content.count(heading), 1)
                self.assertIn(expected, content)


if __name__ == "__main__":
    unittest.main()
