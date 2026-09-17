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

import json
import os
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_EVEN

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
ROOT_LLMS_FULL_PATH = os.path.join(REPO_ROOT, "llms-full.txt")
DOCS_LLMS_FULL_PATH = os.path.join(REPO_ROOT, "docs", "llms-full.txt")
ROOT_LLMS_XML_PATH = os.path.join(REPO_ROOT, "llms-context.xml")
DOCS_LLMS_XML_PATH = os.path.join(REPO_ROOT, "docs", "llms-context.xml")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _table_after_heading(content, heading):
    """Return a Markdown table as a list of header-keyed row dictionaries."""
    section = content.split(heading, 1)[1]
    table_lines = []
    for line in section.splitlines():
        if line.startswith("|"):
            table_lines.append(line)
        elif table_lines:
            break

    if len(table_lines) < 3:
        raise AssertionError(f"No Markdown table found after {heading!r}")

    def cells(line):
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    headers = cells(table_lines[0])
    return [dict(zip(headers, cells(line))) for line in table_lines[2:]]


def _decimal(value):
    """Extract the first signed decimal value from a formatted table cell."""
    match = re.search(r"(?P<sign>-)?(?:\$|RM\s*)?(?P<number>[\d,]+(?:\.\d+)?)", value)
    if match is None:
        raise AssertionError(f"No numeric value found in {value!r}")
    number = Decimal(match.group("number").replace(",", ""))
    return -number if match.group("sign") else number


def _money_values(value):
    """Extract all currency amounts from a Markdown table cell."""
    return [Decimal(item.replace(",", "")) for item in re.findall(r"[\d,]+\.\d{2}", value)]


def _currency_values(value):
    """Extract USD amounts, including whole-dollar ranges."""
    return [
        Decimal(item.replace(",", ""))
        for item in re.findall(r"\$([\d,]+(?:\.\d+)?)", value)
    ]


def _myr(usd):
    return (usd * Decimal("4.50")).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


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
        self.assertEqual(content.count("{% raw %}"), 1)
        self.assertEqual(content.count("{% endraw %}"), 1)
        raw_block_match = re.search(r"\{%\s*raw\s*%\}.*?\{%\s*endraw\s*%\}", content, re.DOTALL)
        self.assertIsNotNone(raw_block_match)

    def test_cloudwatch_agent_configuration_is_valid_and_complete(self):
        """The documented agent profile must stay valid JSON and retain all billed metrics."""
        content = _read(RUM_MD_PATH)
        match = re.search(
            r"\{% raw %\}\s*```json\n(?P<config>.*?)\n```\s*\{% endraw %\}",
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(match, "CloudWatch agent JSON block is missing or unprotected")
        config = json.loads(match.group("config"))

        self.assertEqual(config["agent"], {"metrics_collection_interval": 60, "run_as_user": "cwagent"})
        metrics = config["metrics"]
        self.assertEqual(metrics["namespace"], "CWAgent")
        self.assertEqual(
            metrics["append_dimensions"],
            {
                "AutoScalingGroupName": "${aws:AutoScalingGroupName}",
                "InstanceId": "${aws:InstanceId}",
            },
        )
        self.assertEqual(
            metrics["metrics_collected"]["mem"]["measurement"],
            ["mem_used_percent", "mem_available"],
        )
        self.assertEqual(
            metrics["metrics_collected"]["disk"],
            {"measurement": ["disk_used_percent", "disk_free"], "resources": ["/"]},
        )
        self.assertEqual(
            metrics["metrics_collected"]["net"],
            {
                "measurement": ["bytes_sent", "bytes_recv", "drop_in", "drop_out"],
                "resources": ["*"],
            },
        )

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
        self.assertIn("1,000,000 events", content)
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
            self.assertIn("reference data from another project", content, f"Reference-data source missing in {path}")
            self.assertRegex(
                content,
                r"rather than representing actual (?:historical spend|past expenditure) of this repository",
                f"Repository-spend boundary missing in {path}",
            )

    def test_rum_projection_table_calculations(self):
        """Steady-state, trial-month, and MYR projections must follow the declared rates."""
        content = _read(RUM_MD_PATH)
        rows = _table_after_heading(content, "### 3.2 Monthly Workload Projections")
        self.assertEqual(len(rows), 3)

        for row in rows:
            sessions = int(_decimal(row["Estimated Monthly Sessions"]))
            events = int(_decimal(row["Monthly Events Captured"]))
            usd, trial_usd = _money_values(row["CloudWatch RUM Cost (USD)"])
            myr, trial_myr = _money_values(row["Equivalent Cost (MYR @ 4.50)"])

            self.assertEqual(events, sessions * 10, row["Operational Scenario"])
            expected_usd = Decimal(events) / Decimal("100000")
            self.assertEqual(usd, expected_usd, row["Operational Scenario"])
            self.assertEqual(trial_usd, max(expected_usd - Decimal("10.00"), Decimal("0.00")))
            self.assertEqual(myr, _myr(usd), row["Operational Scenario"])
            self.assertEqual(trial_myr, _myr(trial_usd), row["Operational Scenario"])

    def test_custom_metric_projection_table_calculations_and_free_tier_boundary(self):
        """Every fleet row must apply the ten-metric free tier before billing at $0.30."""
        content = _read(RUM_MD_PATH)
        rows = _table_after_heading(content, "### 6.3 Financial Estimation: Custom Infrastructure Metrics")
        self.assertEqual(len(rows), 5)

        for row in rows:
            nodes = int(_decimal(row["Active Fleet Scope"]))
            metrics_per_node = int(_decimal(row["Profile Telemetry Scope"]))
            total_metrics_match = re.search(r"\((\d+) metrics\)", row["Profile Telemetry Scope"])
            self.assertIsNotNone(total_metrics_match)
            total_metrics = int(total_metrics_match.group(1))
            billed_metrics = int(_decimal(row["Billed Metrics (after 10 free)"]))
            usd = _decimal(row["Monthly Cost (USD)"])
            myr = _decimal(row["Equivalent Cost (MYR @ 4.50)"])

            self.assertEqual(total_metrics, nodes * metrics_per_node, row["Active Fleet Scope"])
            self.assertEqual(billed_metrics, max(total_metrics - 10, 0), row["Active Fleet Scope"])
            self.assertEqual(usd, Decimal(billed_metrics) * Decimal("0.30"), row["Active Fleet Scope"])
            self.assertEqual(myr, _myr(usd), row["Active Fleet Scope"])

        # Regression boundary: the smallest documented fleet has exactly ten
        # chargeable metrics after the free tier, not zero or twenty.
        self.assertEqual(int(_decimal(rows[0]["Billed Metrics (after 10 free)"])), 10)

    def test_tco_reduction_range_matches_documented_cost_endpoints(self):
        """The advertised savings range must be derived from the worst and best cost pairings."""
        content = _read(RUM_MD_PATH)
        row = _table_after_heading(content, "### 3.3 Comparative TCO")[1]
        dynatrace_low, dynatrace_high = _currency_values(row["Dynatrace OneAgent (on AWS)"])
        rum_low, rum_high = _currency_values(row["Amazon CloudWatch RUM"])
        reductions = [Decimal(value) for value in re.findall(r"\d+\.\d", row["Architectural Advantage"])]

        worst_case = ((Decimal("1") - rum_high / dynatrace_low) * 100).quantize(Decimal("0.1"))
        best_case = ((Decimal("1") - rum_low / dynatrace_high) * 100).quantize(Decimal("0.1"))
        self.assertEqual(reductions, [worst_case, best_case])

    def test_tracing_logging_and_privacy_requirements_are_not_overstated(self):
        """Regression coverage for prerequisites and optional-cost/privacy boundaries."""
        content = _read(RUM_MD_PATH)
        for requirement in [
            "`addXRayTraceIdHeader: true`",
            "`enableW3CTraceId: true`",
            "`X-Amzn-Trace-Id` CORS header",
            "AWS Distro for OpenTelemetry (ADOT) collector",
            "application SDK instrumentation",
            "standard CloudWatch Logs ingestion ($0.50/GB)",
            "storage ($0.03/GB-month)",
            "`TelemetryConfig: { anonymizeIP: true }`",
            "user consent management flows",
        ]:
            self.assertIn(requirement, content)
        self.assertIn("ALB header propagation alone does not generate application-level trace segments", content)

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

    def test_cost_explorer_annual_breakdown_reconciles_to_total(self):
        """The changed empirical service rows must reconcile, including the negative adjustment."""
        content = _read(COSTING_MD_PATH)
        rows = _table_after_heading(content, "#### A. 12-Month Historical Service Breakdown")
        self.assertGreater(len(rows), 1)
        line_items, total = rows[:-1], rows[-1]

        usd_sum = sum((_decimal(row["12-Month Spend (USD)"]) for row in line_items), Decimal("0"))
        share_sum = sum((_decimal(row["Percentage Share"]) for row in line_items), Decimal("0"))
        total_usd = _decimal(total["12-Month Spend (USD)"])
        total_myr = _decimal(total["12-Month Spend (MYR @ 4.50)"])

        self.assertEqual(total["Service Category"], "**TOTAL 12-MONTH REFERENCE SPEND**")
        self.assertEqual(usd_sum, total_usd)
        self.assertEqual(total_myr, _myr(total_usd))
        self.assertLessEqual(abs(share_sum - Decimal("100.00")), Decimal("0.05"))
        self.assertTrue(any(_decimal(row["12-Month Spend (USD)"]) < 0 for row in line_items))

    def test_jules_skill_copies_and_knowledge_catalog_register_the_proposal(self):
        """The mirrored skill must not drift and both knowledge surfaces must point to the source doc."""
        agent_skill = _read(os.path.join(REPO_ROOT, ".agents", "skills", "jules-knowledge", "SKILL.md"))
        root_skill = _read(os.path.join(REPO_ROOT, "skills", "jules-knowledge", "SKILL.md"))
        knowledge = _read(os.path.join(REPO_ROOT, ".agents", "brain", "knowledge.md"))

        self.assertEqual(agent_skill, root_skill)
        for content in [agent_skill, knowledge]:
            self.assertIn("docs/executive/cloudwatch-rum-proposal.md", content)
            self.assertIn("$15.00 USD/mo for 15 instances", content)
            self.assertRegex(content, r"\$600(?:\.00)?[–-]\$1,800(?:\.00)? USD/mo")

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

    def test_generated_llms_assets_publish_the_complete_proposal_once(self):
        """Root/docs generated artifacts must agree and contain one complete proposal entry."""
        root_full = _read(ROOT_LLMS_FULL_PATH)
        docs_full = _read(DOCS_LLMS_FULL_PATH)
        self.assertEqual(root_full, docs_full)
        self.assertEqual(root_full.count("## CloudWatch RUM Proposal"), 1)
        self.assertEqual(root_full.count("Document Reference : PROP-OBS-2026-RUM-01"), 1)
        self.assertIn("**Total Observability Envelope:**", root_full)

        root_xml = _read(ROOT_LLMS_XML_PATH)
        docs_xml = _read(DOCS_LLMS_XML_PATH)
        self.assertEqual(root_xml, docs_xml)
        xml_root = ET.fromstring(root_xml)
        proposals = xml_root.findall(
            ".//document[@title='CloudWatch RUM Proposal']"
            "[@url='docs/executive/cloudwatch-rum-proposal.md']"
        )
        self.assertEqual(len(proposals), 1)
        self.assertIn("PROP-OBS-2026-RUM-01", "".join(proposals[0].itertext()))

    def test_sitemap_publication(self):
        """Verifies publication entries in both XML and TXT sitemaps prior to and after generation."""
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

        # First assert tracked committed sitemap artifacts contain expected entries
        for s_path in sitemaps_txt:
            content = _read(s_path)
            for url in expected_txt_urls:
                self.assertEqual(content.count(url), 1, f"Committed URL {url} missing or duplicated in {s_path}")

        for s_path in sitemaps_xml:
            content = _read(s_path)
            for url in expected_xml_urls:
                loc_tag = f"<loc>{url}</loc>"
                self.assertEqual(content.count(loc_tag), 1, f"Committed XML tag {loc_tag} missing or duplicated in {s_path}")

            root = ET.fromstring(content)
            entries = [
                node
                for node in root.findall(f"{SITEMAP_NS}url")
                if node.findtext(f"{SITEMAP_NS}loc") == expected_xml_urls[0]
            ]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].findtext(f"{SITEMAP_NS}lastmod"), "2026-08-12")

        # Regenerate sitemaps and re-verify
        generate_sitemaps.main()

        for s_path in sitemaps_txt:
            content = _read(s_path)
            for url in expected_txt_urls:
                self.assertEqual(content.count(url), 1, f"Regenerated URL {url} count is not 1 in {s_path}")

        for s_path in sitemaps_xml:
            content = _read(s_path)
            for url in expected_xml_urls:
                loc_tag = f"<loc>{url}</loc>"
                self.assertEqual(content.count(loc_tag), 1, f"Regenerated XML tag {loc_tag} count is not 1 in {s_path}")


if __name__ == "__main__":
    unittest.main()
