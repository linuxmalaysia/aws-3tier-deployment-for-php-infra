#!/usr/bin/env python3
"""Unit and integration tests for the CloudWatch APM, RUM & Telemetry Architecture Guide.

This test suite validates that:
* ``docs/engineering/cloudwatch-apm-rum-guide.md`` adheres to OKF v0.1 YAML front matter contracts,
* Required headers, classification parameters, and document references exist,
* JSON/Jinja configuration snippets are properly protected with Liquid {% raw %} tags,
* Pricing parameters ($1.50/1M signals, $0.35/GB trace, $1.00/100k events) and TPS crossover tables are present,
* Public/anonymized information disclaimers are enforced,
* Document registrations across ``docs/index.md``, ``docs/SUMMARY.md``, ``SUMMARY.md``, ``llms.txt``,
  and sitemaps are verified.
"""

import os
import re
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import prepare_docs
import generate_sitemaps

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
DOCS_SUMMARY_PATH = os.path.join(REPO_ROOT, "docs", "SUMMARY.md")
ROOT_SUMMARY_PATH = os.path.join(REPO_ROOT, "SUMMARY.md")
CW_GUIDE_MD_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "cloudwatch-apm-rum-guide.md")


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class CloudWatchApmRumDocsTestCase(unittest.TestCase):
    """Comprehensive test case for CloudWatch APM, RUM & Telemetry Architecture documentation."""

    def test_file_exists(self):
        """Verifies that the CloudWatch APM, RUM & Telemetry guide markdown file exists."""
        self.assertTrue(os.path.isfile(CW_GUIDE_MD_PATH))

    def test_front_matter_okf_v01(self):
        """Validates the OKF v0.1 front matter contract for cloudwatch-apm-rum-guide.md."""
        content = _read(CW_GUIDE_MD_PATH)
        self.assertTrue(content.startswith("---\n"))
        parts = content.split("---", 2)
        fm = prepare_docs.parse_yaml_front_matter(parts[1])
        self.assertEqual(fm["layout"], "default")
        self.assertEqual(fm["okf_version"], "0.1")
        self.assertEqual(fm["type"], "Technical Justification & Engineering Guide")
        self.assertEqual(
            fm["title"],
            "Amazon CloudWatch APM, RUM & Infrastructure Telemetry Architecture Guide",
        )
        self.assertEqual(fm["topics"], ["aws", "cloudwatch", "apm", "rum", "telemetry"])
        self.assertEqual(fm["timestamp"], "2026-08-12T00:00:00+08:00")

    def test_liquid_raw_block_protection(self):
        """Verifies that JSON configuration snippets are wrapped with Liquid raw tags."""
        content = _read(CW_GUIDE_MD_PATH)
        self.assertIn("{% raw %}", content)
        self.assertIn("{% endraw %}", content)
        raw_block_match = re.search(r"\{%\s*raw\s*%\}.*?\{%\s*endraw\s*%\}", content, re.DOTALL)
        self.assertIsNotNone(raw_block_match)

    def test_document_structure_and_pricing_elements(self):
        """Verifies key structural sections, reference codes, and exact pricing parameters."""
        content = _read(CW_GUIDE_MD_PATH)
        self.assertIn("PAP-APM-2026-CW-02", content)
        self.assertIn("## Executive Summary", content)
        self.assertIn("## 1. Why Change: Limitations of the Current Dynatrace Model", content)
        self.assertIn("## 2. Architectural Comparison Matrix", content)
        self.assertIn("## 3. How CloudWatch Application Signals (APM) Is Priced", content)
        self.assertIn("## 4. CloudWatch Real User Monitoring (RUM) Client-Side Architecture", content)
        self.assertIn("## 5. Capability & Infrastructure Telemetry Matrix", content)
        self.assertIn("## 6. Unified CloudWatch Agent Configuration", content)
        self.assertIn("## 7. High-Volume / Payment-Critical Cost Risk & TPS Crossover Analysis", content)
        self.assertIn("## 8. Total Consolidated Observability Stack (15-Node Cluster)", content)
        self.assertIn("## 9. Implementation Roadmap & Migration Plan", content)
        self.assertIn("## 10. Public Information & Data Anonymization Statement", content)

        # Exact pricing checks
        self.assertIn("$1.50 USD per 1 million signals", content)
        self.assertIn("$0.35 USD per GB", content)
        self.assertIn("$1.00 USD per 100,000 data events", content)
        self.assertIn("$0.30 USD per metric/month", content)
        self.assertIn("amazon-cloudwatch-agent", content)

    def test_links_in_index(self):
        """Verifies that the CloudWatch guide is correctly linked in docs/index.md."""
        index = _read(INDEX_PATH)
        self.assertIn(
            "[Amazon CloudWatch APM, RUM & Infrastructure Telemetry Architecture Guide](engineering/cloudwatch-apm-rum-guide.html)",
            index,
        )

    def test_indexed_in_llms_txt(self):
        """Verifies that the guide is correctly indexed in llms.txt."""
        llms = _read(LLMS_PATH)
        self.assertIn(
            "[CloudWatch APM, RUM & Telemetry Architecture Guide](docs/engineering/cloudwatch-apm-rum-guide.md)",
            llms,
        )

    def test_summary_files_registration(self):
        """Verifies that the guide is registered in both docs/SUMMARY.md and root SUMMARY.md."""
        docs_summary = _read(DOCS_SUMMARY_PATH)
        root_summary = _read(ROOT_SUMMARY_PATH)
        self.assertIn("[CloudWatch APM, RUM & Telemetry Architecture Guide](engineering/cloudwatch-apm-rum-guide.md)", docs_summary)
        self.assertIn("[CloudWatch APM, RUM & Telemetry Architecture Guide](docs/engineering/cloudwatch-apm-rum-guide.md)", root_summary)

    def test_sitemap_publication(self):
        """Verifies publication entries in both XML and TXT sitemaps."""
        sitemaps_txt = [
            os.path.join(REPO_ROOT, "sitemap.txt"),
            os.path.join(REPO_ROOT, "docs", "sitemap.txt"),
        ]
        sitemaps_xml = [
            os.path.join(REPO_ROOT, "sitemap.xml"),
            os.path.join(REPO_ROOT, "docs", "sitemap.xml"),
        ]

        expected_txt_urls = [
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/engineering/cloudwatch-apm-rum-guide.html",
            "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/engineering/cloudwatch-apm-rum-guide",
        ]

        expected_xml_urls = [
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/engineering/cloudwatch-apm-rum-guide.html",
        ]

        for s_path in sitemaps_txt:
            content = _read(s_path)
            for url in expected_txt_urls:
                self.assertEqual(content.count(url), 1, f"Committed URL {url} missing or duplicated in {s_path}")

        for s_path in sitemaps_xml:
            content = _read(s_path)
            for url in expected_xml_urls:
                loc_tag = f"<loc>{url}</loc>"
                self.assertEqual(content.count(loc_tag), 1, f"Committed XML tag {loc_tag} missing or duplicated in {s_path}")


if __name__ == "__main__":
    unittest.main()
