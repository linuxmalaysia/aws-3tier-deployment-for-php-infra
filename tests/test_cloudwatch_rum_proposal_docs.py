#!/usr/bin/env python3
"""Unit and integration tests for the CloudWatch RUM Proposal & Justification documentation.

This test suite validates that:
* ``docs/executive/cloudwatch-rum-proposal.md`` adheres to OKF v0.1 YAML front matter contracts,
* Jinja/JSON configuration snippets are properly protected with Liquid {% raw %} tags,
* Estimation context and reference data disclaimers are present,
* Cost Explorer reference data and observability consolidation updates in ``docs/executive/costing.md``
  and ``docs/executive/production-costing.md`` are consistent,
* Document registrations across ``docs/index.md``, ``docs/SUMMARY.md``, ``SUMMARY.md``, ``llms.txt``,
  and sitemaps are verified.
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
DOCS_SUMMARY_PATH = os.path.join(REPO_ROOT, "docs", "SUMMARY.md")
ROOT_SUMMARY_PATH = os.path.join(REPO_ROOT, "SUMMARY.md")
RUM_MD_PATH = os.path.join(REPO_ROOT, "docs", "executive", "cloudwatch-rum-proposal.md")
COSTING_MD_PATH = os.path.join(REPO_ROOT, "docs", "executive", "costing.md")
PROD_COSTING_MD_PATH = os.path.join(REPO_ROOT, "docs", "executive", "production-costing.md")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class CloudWatchRumProposalDocsTestCase(unittest.TestCase):
    """Comprehensive test case for CloudWatch RUM Proposal documentation and Costing updates."""

    def test_file_exists(self):
        """Verifies that the CloudWatch RUM proposal markdown file exists."""
        self.assertTrue(os.path.isfile(RUM_MD_PATH))

    def test_front_matter_okf_v01(self):
        """Validates the OKF v0.1 front matter contract for cloudwatch-rum-proposal.md."""
        content = _read(RUM_MD_PATH)
        self.assertTrue(content.startswith("---\n"))
        parts = content.split("---", 2)
        fm = prepare_docs.parse_yaml_front_matter(parts[1])
        self.assertEqual(fm["layout"], "default")
        self.assertEqual(fm["okf_version"], "0.1")
        self.assertEqual(fm["type"], "Technical Proposal & Financial Justification")
        self.assertEqual(
            fm["title"],
            "CloudWatch RUM Integration & Observability Consolidation Proposal",
        )
        self.assertEqual(fm["topics"], ["aws", "cloudwatch", "rum", "finops", "apm"])
        self.assertEqual(fm["timestamp"], "2026-08-12T00:00:00+08:00")

    def test_liquid_raw_block_protection(self):
        """Verifies that JSON/Jinja configuration snippets are wrapped with Liquid raw tags."""
        content = _read(RUM_MD_PATH)
        self.assertIn("{% raw %}", content)
        self.assertIn("{% endraw %}", content)
        raw_block_match = re.search(r"\{%\s*raw\s*%\}.*?\{%\s*endraw\s*%\}", content, re.DOTALL)
        self.assertIsNotNone(raw_block_match)

    def test_document_structure_and_pricing_elements(self):
        """Verifies key structural sections and exact pricing parameters in the proposal."""
        content = _read(RUM_MD_PATH)
        self.assertIn("PROP-OBS-2026-RUM-01", content)
        self.assertIn("## Executive Summary", content)
        self.assertIn("## 1. Problem Statement: The Cost & Overhead of AWS-Hosted Dynatrace", content)
        self.assertIn("## 2. Technical Architecture: Amazon CloudWatch RUM", content)
        self.assertIn("## 3. Financial Modeling & Sizing Estimation", content)
        self.assertIn("## 4. Architectural Justification & Strategic Benefits", content)
        self.assertIn("## 5. Implementation Roadmap & Migration Plan", content)
        self.assertIn("## 6. Operational Delivery: EC2 Unified CloudWatch Agent", content)
        self.assertIn("## 7. Consolidated Observability Sizing Summary", content)
        self.assertIn("## 8. Estimation Context & Reference Data Disclaimer", content)

        # Exact pricing checks
        self.assertIn("$1.00 USD per 100,000 data events", content)
        self.assertIn("1,000,000 events/month", content)
        self.assertIn("$0.30 USD per metric/month", content)
        self.assertIn("amazon-cloudwatch-agent", content)

    def test_estimation_disclaimer_present(self):
        """Verifies that the reference data estimation disclaimer is present in all costing/proposal docs."""
        for path in [RUM_MD_PATH, COSTING_MD_PATH, PROD_COSTING_MD_PATH]:
            content = _read(path)
            self.assertIn(
                "Estimation Context & Reference Data Disclaimer",
                content,
                f"Disclaimer missing in {path}",
            )

    def test_costing_md_empirical_sections(self):
        """Verifies that docs/executive/costing.md contains the required empirical Cost Explorer subsections."""
        content = _read(COSTING_MD_PATH)
        self.assertIn("3.6 Unified Observability & Full-Stack Metrics Calibration", content)
        self.assertIn("3.7 Real-World Cost Calibration & Analysis (AWS Malaysia `ap-southeast-5`)", content)
        self.assertIn("A. 12-Month Historical Service Breakdown (Sept 2025 – Aug 2026)", content)
        self.assertIn("B. June 2026 Daily & Monthly Run-Rate Audit", content)
        self.assertIn("C. August 2026 Instance-Type Cost Allocation", content)
        self.assertIn("D. August 2026 Daily Telemetry Overview", content)

        # Figures check
        self.assertIn("$61,400.47", content)
        self.assertIn("RM 276,302.12", content)
        self.assertIn("$19,174.98", content)
        self.assertIn("$6,113.60", content)
        self.assertIn("$6,505.72", content)

    def test_links_in_index(self):
        """Verifies that the CloudWatch RUM Proposal is correctly linked in docs/index.md."""
        index = _read(INDEX_PATH)
        self.assertIn(
            "[CloudWatch RUM Integration & Observability Consolidation Proposal](executive/cloudwatch-rum-proposal.html)",
            index,
        )

    def test_indexed_in_llms_txt(self):
        """Verifies that the proposal is correctly indexed in llms.txt."""
        llms = _read(LLMS_PATH)
        self.assertIn(
            "[CloudWatch RUM Proposal](docs/executive/cloudwatch-rum-proposal.md)",
            llms,
        )

    def test_summary_files_registration(self):
        """Verifies that the proposal is registered in both docs/SUMMARY.md and root SUMMARY.md."""
        docs_summary = _read(DOCS_SUMMARY_PATH)
        root_summary = _read(ROOT_SUMMARY_PATH)
        self.assertIn("[CloudWatch RUM Proposal](executive/cloudwatch-rum-proposal.md)", docs_summary)
        self.assertIn("[CloudWatch RUM Proposal](docs/executive/cloudwatch-rum-proposal.md)", root_summary)

    def test_sitemap_publication(self):
        """Verifies publication entries in both XML and TXT sitemaps."""
        generate_sitemaps.main()

        sitemaps_txt = [
            os.path.join(REPO_ROOT, "sitemap.txt"),
            os.path.join(REPO_ROOT, "docs", "sitemap.txt"),
        ]
        sitemaps_xml = [
            os.path.join(REPO_ROOT, "sitemap.xml"),
            os.path.join(REPO_ROOT, "docs", "sitemap.xml"),
        ]

        expected_txt_urls = [
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/executive/cloudwatch-rum-proposal.html",
            "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/executive/cloudwatch-rum-proposal",
        ]

        expected_xml_urls = [
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/executive/cloudwatch-rum-proposal.html",
        ]

        for s_path in sitemaps_txt:
            content = _read(s_path)
            for url in expected_txt_urls:
                self.assertEqual(content.count(url), 1, f"URL {url} count is not 1 in {s_path}")

        for s_path in sitemaps_xml:
            content = _read(s_path)
            for url in expected_xml_urls:
                loc_tag = f"<loc>{url}</loc>"
                self.assertEqual(content.count(loc_tag), 1, f"XML tag {loc_tag} count is not 1 in {s_path}")


if __name__ == "__main__":
    unittest.main()
