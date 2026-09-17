#!/usr/bin/env python3
"""Unit and integration tests for the CloudWatch APM, RUM & Telemetry Architecture Guide.

This test suite validates that:
* ``docs/engineering/cloudwatch-apm-rum-guide.md`` adheres to OKF v0.1 YAML front matter contracts,
* Required headers, classification parameters, and document references exist,
* Overview of CloudWatch, Application Signals (APM), and RUM are detailed,
* Dynatrace comparison matrices (Tables 3.1, 3.2, and 3.3) exist,
* Comprehensive catalog of 7 available operational/financial reports and benefits exist,
* Supporting tools, instrumentation frameworks, and automated PDF export workflow exist,
* JSON/Jinja configuration snippets are properly protected with Liquid {% raw %} tags,
* Pricing parameters ($1.50/1M signals, $0.35/GB trace, $1.00/100k events) and TPS crossover tables are present,
* Public/anonymized information disclaimers are enforced,
* Document registrations across ``docs/index.md``, ``docs/SUMMARY.md``, ``SUMMARY.md``, ``llms.txt``,
  and sitemaps are verified.
"""

import json
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
import generate_llms_assets

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
DOCS_SUMMARY_PATH = os.path.join(REPO_ROOT, "docs", "SUMMARY.md")
ROOT_SUMMARY_PATH = os.path.join(REPO_ROOT, "SUMMARY.md")
CW_GUIDE_MD_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "cloudwatch-apm-rum-guide.md")
PDF_WORKFLOW_PATH = os.path.join(REPO_ROOT, ".github", "workflows", "pdf-generation.yml")


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _numbered_section(content, number):
    match = re.search(
        rf"^## {number}\..*?\n(.*?)(?=^## \d+\.|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"Numbered section {number} is missing")
    return match.group(1)


def _markdown_table(section, header):
    lines = section[section.index(header) :].splitlines()
    rows = []
    for line in lines:
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip().strip("*") for cell in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def _money_range(cell):
    steady_state = cell.split("(", 1)[0]
    values = [
        float(value.replace(",", ""))
        for value in re.findall(r"\$(\d[\d,]*(?:\.\d+)?)", steady_state)
    ]
    if not values:
        raise AssertionError(f"No USD amount found in {cell!r}")
    return values[0], values[-1]


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
        self.assertIn("## 2. Overview of CloudWatch, CloudWatch APM (Application Signals) & CloudWatch RUM", content)
        self.assertIn("## 3. Architectural Comparison Matrix: CloudWatch APM + RUM vs. Dynatrace", content)
        self.assertIn("## 4. Comprehensive Catalog of Available Reports & Strategic Benefits", content)
        self.assertIn("## 5. Supporting Tools, Instrumentation Frameworks & PDF Generation Workflow", content)
        self.assertIn("## 6. How CloudWatch Application Signals (APM) Is Priced", content)
        self.assertIn("## 7. CloudWatch Real User Monitoring (RUM) Client-Side Architecture", content)
        self.assertIn("## 8. Capability & Infrastructure Telemetry Matrix", content)
        self.assertIn("## 9. Unified CloudWatch Agent Configuration", content)
        self.assertIn("## 10. High-Volume / Payment-Critical Cost Risk & TPS Crossover Analysis", content)
        self.assertIn("## 11. Total Consolidated Observability Stack", content)
        self.assertIn("## 12. Implementation Roadmap & Migration Plan", content)
        self.assertIn("## 13. Public Information & Data Anonymization Statement", content)

        # Exact pricing checks
        self.assertIn("$1.50 USD per 1 million signals", content)
        self.assertIn("$0.35 USD per GB", content)
        self.assertIn("$1.00 USD per 100,000 data events", content)
        self.assertIn("$0.30 USD per metric/month", content)
        self.assertIn("amazon-cloudwatch-agent", content)

    def test_comparison_tables_and_reports(self):
        """Verifies comparison tables and catalog of 7 reports in the guide."""
        content = _read(CW_GUIDE_MD_PATH)
        # Check comparison tables
        self.assertIn("### Table 3.1: Architecture, Footprint, and Technical Standards", content)
        self.assertIn("### Table 3.2: Observability Features, Capabilities, and Data Governance", content)
        self.assertIn("### Table 3.3: Financial, Pricing & Commercial Models", content)

        # Check reports
        self.assertIn("### Report 1: Service Health & Dependency Map Report", content)
        self.assertIn("### Report 2: Service Level Objective (SLO) & Error Budget Burn-Rate Report", content)
        self.assertIn("### Report 3: Distributed Trace Waterfall & Transaction Latency Report", content)
        self.assertIn("### Report 4: Real User Performance & Core Web Vitals Report", content)
        self.assertIn("### Report 5: Client-Side Errors & JavaScript Exception Analytics Report", content)
        self.assertIn("### Report 6: Infrastructure Resource Utilization & Capacity Planning Report", content)
        self.assertIn("### Report 7: FinOps Observability Cost & Telemetry Usage Report", content)

        # Check supporting tools & PDF workflow section
        self.assertIn("### 5.1 Supporting Tools & Agent Ecosystem", content)
        self.assertIn("### 5.2 Automated PDF Document Export Workflow", content)
        self.assertIn("`output.pdf`", content)

    def test_numbered_sections_are_complete_unique_and_ordered(self):
        """Prevents section renumbering gaps or duplicates after the guide expansion."""
        content = _read(CW_GUIDE_MD_PATH)
        section_numbers = [int(number) for number in re.findall(r"^## (\d+)\.", content, re.MULTILINE)]
        self.assertEqual(section_numbers, list(range(1, 14)))

    def test_overview_covers_each_observability_layer(self):
        """Verifies that the new overview distinguishes core, server-side, and client-side telemetry."""
        overview = _numbered_section(_read(CW_GUIDE_MD_PATH), 2)
        expected_subsections = {
            "2.1": ("Amazon CloudWatch (Core Platform)", "CloudWatch Alarms", "EventBridge"),
            "2.2": ("CloudWatch Application Signals (APM)", "OpenTelemetry", "Service Level Objectives"),
            "2.3": ("CloudWatch Real User Monitoring (RUM)", "Core Web Vitals", "JavaScript"),
        }
        for subsection, required_terms in expected_subsections.items():
            self.assertEqual(len(re.findall(rf"^### {re.escape(subsection)}\b", overview, re.MULTILINE)), 1)
            for term in required_terms:
                self.assertIn(term, overview)

    def test_report_catalog_is_complete_and_each_report_is_actionable(self):
        """Verifies the seven-report boundary and the required structure of every report."""
        catalog = _numbered_section(_read(CW_GUIDE_MD_PATH), 4)
        headings = re.findall(r"^### Report (\d+): (.+)$", catalog, re.MULTILINE)
        self.assertEqual([int(number) for number, _ in headings], list(range(1, 8)))
        self.assertEqual(len({title for _, title in headings}), 7)

        report_bodies = re.split(r"^### Report \d+: .+$", catalog, flags=re.MULTILINE)[1:]
        self.assertEqual(len(report_bodies), 7)
        for report_number, body in enumerate(report_bodies, start=1):
            with self.subTest(report=report_number):
                self.assertEqual(body.count("**Telemetry Source:**"), 1)
                self.assertEqual(body.count("**Report Contents:**"), 1)
                self.assertEqual(body.count("**Benefits:**"), 1)

    def test_rum_trace_modes_and_privacy_controls_are_explicit(self):
        """Guards the reviewed trace-header alternatives and compliance caveat."""
        rum = _numbered_section(_read(CW_GUIDE_MD_PATH), 7)
        for term in (
            "`addXRayTraceIdHeader: true`",
            "`X-Amzn-Trace-Id`",
            "`enableW3CTraceId: true`",
            "`traceparent`",
            "CORS",
            "OpenTelemetry PHP zero-code instrumentation",
            "does not inherently guarantee regulatory or privacy compliance",
            "`allowCookies: false`",
            "`recordResourceUrl: false`",
        ):
            self.assertIn(term, rum)
        self.assertRegex(rum, r"configuring either .*addXRayTraceIdHeader.* or .*enableW3CTraceId")
        self.assertNotIn("Native IP masking is supported", rum)

    def test_cloudwatch_agent_json_is_valid_and_matches_metric_sizing(self):
        """Parses the documented agent configuration and checks the priced metric dimensions."""
        content = _read(CW_GUIDE_MD_PATH)
        match = re.search(r"\{% raw %\}\s*```json\s*(.*?)\s*```\s*\{% endraw %\}", content, re.DOTALL)
        self.assertIsNotNone(match)
        config = json.loads(match.group(1))
        self.assertEqual(config["agent"]["run_as_user"], "cwagent")
        self.assertEqual(config["agent"]["metrics_collection_interval"], 60)

        collected = config["metrics"]["metrics_collected"]
        self.assertEqual(set(collected), {"mem", "disk", "net"})
        self.assertEqual(collected["mem"]["measurement"], ["mem_used_percent", "mem_available"])
        self.assertEqual(collected["disk"]["measurement"], ["disk_used_percent", "disk_free"])
        self.assertEqual(collected["net"]["measurement"], ["bytes_sent", "bytes_recv", "drop_in", "drop_out"])

        sizing = _numbered_section(content, 9)
        os_metrics = len(collected["mem"]["measurement"]) + len(collected["disk"]["measurement"])
        network_metrics = len(collected["net"]["measurement"])
        for interfaces, documented_series, documented_cost in ((1, 120, 33.0), (2, 180, 51.0)):
            total_series = 15 * (os_metrics + interfaces * network_metrics)
            billable_series = total_series - 10
            self.assertEqual(total_series, documented_series)
            self.assertEqual(billable_series * 0.30, documented_cost)
            self.assertIn(f"{documented_series} series", sizing)
            self.assertIn(f"${documented_cost:.2f} USD", sizing)

    def test_rum_cost_table_covers_low_and_high_event_boundaries(self):
        """Checks both ends of the documented 10-to-20-events-per-session range."""
        rum = _numbered_section(_read(CW_GUIDE_MD_PATH), 7)
        rows = _markdown_table(rum, "| Monthly Sessions |")
        by_profile = {row[0]: row for row in rows[1:]}
        scenarios = (("250,000 sessions", 250_000), ("1,000,000 sessions", 1_000_000))
        for label, sessions in scenarios:
            with self.subTest(sessions=sessions):
                low, high = _money_range(by_profile[label][2])
                self.assertEqual(low, sessions * 10 / 100_000)
                self.assertEqual(high, sessions * 20 / 100_000)

    def test_consolidated_cost_range_equals_component_ranges(self):
        """Regression check: the reproducible total must equal its component cost boundaries."""
        consolidated = _numbered_section(_read(CW_GUIDE_MD_PATH), 11)
        rows = _markdown_table(consolidated, "| Observability Layer |")
        costs = {row[0]: _money_range(row[2]) for row in rows[1:]}
        component_names = (
            "CloudWatch RUM",
            "Application Signals (APM)",
            "Host Metrics (Agent)",
            "Native AWS Metrics",
            "Alarms & Dashboards",
        )
        expected_total = tuple(sum(costs[name][bound] for name in component_names) for bound in (0, 1))
        self.assertEqual(costs["Total CloudWatch Suite"], expected_total)

    def test_pdf_workflow_matches_the_documented_export_contract(self):
        """Verifies that the workflow referenced by the new guide can produce the named artifact."""
        self.assertTrue(os.path.isfile(PDF_WORKFLOW_PATH))
        workflow = _read(PDF_WORKFLOW_PATH)
        self.assertRegex(workflow, r"uses:\s*actions/setup-node@\S+\s+# v4")
        self.assertRegex(workflow, r"node-version:\s*['\"]?22['\"]?")
        self.assertIn("misaelnieto/web_to_pdf_action@v0.3.1", workflow)
        self.assertIn("docs/assets/output.pdf", workflow)
        self.assertIn("name: page-pdf", workflow)

    def test_generated_llm_assets_embed_the_exact_guide_body(self):
        """Ensures all four changed generated assets are synchronized with the Markdown source."""
        expected_body = generate_llms_assets.strip_front_matter(_read(CW_GUIDE_MD_PATH)).strip()
        for relative_path in ("llms-full.txt", os.path.join("docs", "llms-full.txt")):
            with self.subTest(asset=relative_path):
                self.assertEqual(_read(os.path.join(REPO_ROOT, relative_path)).count(expected_body), 1)

        for relative_path in ("llms-context.xml", os.path.join("docs", "llms-context.xml")):
            with self.subTest(asset=relative_path):
                root = ET.parse(os.path.join(REPO_ROOT, relative_path)).getroot()
                matches = root.findall(".//document[@url='docs/engineering/cloudwatch-apm-rum-guide.md']")
                self.assertEqual(len(matches), 1)
                self.assertEqual((matches[0].text or "").strip(), expected_body)

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
