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

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
DOCS_SUMMARY_PATH = os.path.join(REPO_ROOT, "docs", "SUMMARY.md")
ROOT_SUMMARY_PATH = os.path.join(REPO_ROOT, "SUMMARY.md")
CW_GUIDE_MD_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "cloudwatch-apm-rum-guide.md")
LLMS_FULL_PATHS = [
    os.path.join(REPO_ROOT, "llms-full.txt"),
    os.path.join(REPO_ROOT, "docs", "llms-full.txt"),
]
LLMS_CONTEXT_PATHS = [
    os.path.join(REPO_ROOT, "llms-context.xml"),
    os.path.join(REPO_ROOT, "docs", "llms-context.xml"),
]
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
GUIDE_SOURCE_URL = "docs/engineering/cloudwatch-apm-rum-guide.md"
GUIDE_PAGES_URL = (
    "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
    "engineering/cloudwatch-apm-rum-guide.html"
)


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _agent_profile(content):
    """Extract the Jekyll-protected CloudWatch Agent JSON profile."""
    match = re.search(
        r"\{%\s*raw\s*%\}\s*```json\s*(\{.*?\})\s*```\s*\{%\s*endraw\s*%\}",
        content,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError("CloudWatch Agent profile is not a Liquid-protected JSON block")
    return json.loads(match.group(1))


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

    def test_cloudwatch_agent_profile_is_valid_and_collects_required_metrics(self):
        """Validates the exact guest-metric profile rather than only its code fence."""
        profile = _agent_profile(_read(CW_GUIDE_MD_PATH))

        self.assertEqual(profile["agent"], {
            "metrics_collection_interval": 60,
            "run_as_user": "cwagent",
        })
        self.assertEqual(profile["metrics"]["namespace"], "CWAgent")
        self.assertEqual(profile["metrics"]["append_dimensions"], {
            "AutoScalingGroupName": "${aws:AutoScalingGroupName}",
            "InstanceId": "${aws:InstanceId}",
        })

        collected = profile["metrics"]["metrics_collected"]
        self.assertEqual(collected["mem"]["measurement"], ["mem_used_percent", "mem_available"])
        self.assertEqual(collected["disk"]["measurement"], ["disk_used_percent", "disk_free"])
        self.assertEqual(collected["disk"]["resources"], ["/"])
        self.assertEqual(
            collected["net"]["measurement"],
            ["bytes_sent", "bytes_recv", "drop_in", "drop_out"],
        )
        self.assertEqual(collected["net"]["resources"], ["*"])

    def test_rum_trace_correlation_requires_client_and_backend_controls(self):
        """Regression: propagation alone must not be presented as end-to-end tracing."""
        content = _read(CW_GUIDE_MD_PATH)
        for requirement in [
            "enableXRay: true",
            "addXRayTraceIdHeader: true",
            "X-Amzn-Trace-Id` CORS header",
            "Backend instrumentation",
            "client header propagation alone does not create server-side trace segments",
        ]:
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, content)

    def test_custom_metric_cost_examples_apply_the_free_tier_boundary(self):
        """Ensure the 4- and 8-metric cluster examples retain correct billed counts."""
        content = _read(CW_GUIDE_MD_PATH)
        monthly_costs = {4: 15.00, 8: 33.00}

        for metrics_per_node, expected_cost in monthly_costs.items():
            with self.subTest(metrics_per_node=metrics_per_node):
                total_metrics = 15 * metrics_per_node
                billed_metrics = total_metrics - 10
                self.assertEqual(billed_metrics * 0.30, expected_cost)
                self.assertRegex(
                    content,
                    rf"{total_metrics} time series \({billed_metrics} billed after 10 free\).*?"
                    rf"\$({expected_cost:.2f}) USD / month",
                )

    def test_public_information_statement_contains_no_private_network_addresses(self):
        """Regression: the public guide must not accidentally publish private IP data."""
        content = _read(CW_GUIDE_MD_PATH)
        self.assertIn("Public Information & Educational Notice", content)
        private_address_patterns = [
            r"\b10(?:\.\d{1,3}){3}\b",
            r"\b192\.168(?:\.\d{1,3}){2}\b",
            r"\b172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2}\b",
        ]
        for pattern in private_address_patterns:
            with self.subTest(pattern=pattern):
                self.assertNotRegex(content, pattern)

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
        guide_front_matter = prepare_docs.parse_yaml_front_matter(
            _read(CW_GUIDE_MD_PATH).split("---", 2)[1]
        )
        expected_lastmod = guide_front_matter["timestamp"].split("T", 1)[0]
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
            GUIDE_PAGES_URL,
        ]

        for s_path in sitemaps_txt:
            content = _read(s_path)
            for url in expected_txt_urls:
                self.assertEqual(content.count(url), 1, f"Committed URL {url} missing or duplicated in {s_path}")

        for s_path in sitemaps_xml:
            root = ET.parse(s_path).getroot()
            for url in expected_xml_urls:
                matches = [
                    node
                    for node in root.findall(f"{SITEMAP_NS}url")
                    if node.findtext(f"{SITEMAP_NS}loc") == url
                ]
                self.assertEqual(len(matches), 1, f"Committed URL {url} missing or duplicated in {s_path}")
                self.assertEqual(
                    matches[0].findtext(f"{SITEMAP_NS}lastmod"),
                    expected_lastmod,
                    f"Sitemap lastmod for {url} must follow the guide's OKF timestamp",
                )

    def test_compiled_llm_assets_publish_the_complete_cloudwatch_guide(self):
        """Verify both generated formats expose one complete discoverable guide."""
        for path in LLMS_FULL_PATHS:
            with self.subTest(path=path):
                content = _read(path)
                self.assertIn("PAP-APM-2026-CW-02", content)
                self.assertIn(
                    "client header propagation alone does not create server-side trace segments",
                    content,
                )

        for path in LLMS_CONTEXT_PATHS:
            with self.subTest(path=path):
                root = ET.parse(path).getroot()
                documents = [
                    node
                    for node in root.findall(".//document")
                    if node.get("url") == GUIDE_SOURCE_URL
                ]
                self.assertEqual(len(documents), 1)
                self.assertIn("PAP-APM-2026-CW-02", documents[0].text)
                self.assertIn(
                    "client header propagation alone does not create server-side trace segments",
                    documents[0].text,
                )


if __name__ == "__main__":
    unittest.main()
