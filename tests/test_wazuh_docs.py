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
from typing import Any, Dict, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import prepare_docs  # noqa: E402
import generate_sitemaps  # noqa: E402
import generate_llms_assets  # noqa: E402

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
SUMMARY_PATH = os.path.join(REPO_ROOT, "SUMMARY.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
WAZUH_DOC_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "wazuh-installation.md")
ROOT_SITEMAP_TXT = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_TXT = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_XML = os.path.join(REPO_ROOT, "sitemap.xml")
DOCS_SITEMAP_XML = os.path.join(REPO_ROOT, "docs", "sitemap.xml")
ROOT_LLMS_FULL = os.path.join(REPO_ROOT, "llms-full.txt")
DOCS_LLMS_FULL = os.path.join(REPO_ROOT, "docs", "llms-full.txt")
ROOT_LLMS_XML = os.path.join(REPO_ROOT, "llms-context.xml")
DOCS_LLMS_XML = os.path.join(REPO_ROOT, "docs", "llms-context.xml")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

GH_BASE = "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
GB_BASE = "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/"

GH_URL = GH_BASE + "engineering/wazuh-installation.html"
GB_URL = GB_BASE + "engineering/wazuh-installation"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _parse_front_matter(content: str) -> Tuple[Dict[str, Any], str]:
    if not content.startswith("---\n"):
        raise ValueError("Document does not start with opening front matter delimiter '---\\n'")

    # Find the closing delimiter anchored at the start of a line
    closing_idx = content.find("\n---\n", 4)
    if closing_idx == -1:
        # Check if closing marker is at end of file
        if content.endswith("\n---"):
            closing_idx = len(content) - 4
        else:
            raise ValueError("Document missing closing front matter delimiter '\\n---\\n'")

    front_matter_text = content[4:closing_idx]
    body_text = content[closing_idx + 5:] if content[closing_idx:].startswith("\n---\n") else content[closing_idx + 4:]

WAZUH_TITLE = "Wazuh SIEM & XDR Deployment Guide: AWS Cloud, On-Premises AlmaLinux 10 & WSL2 Demo"
WAZUH_SHORT_TITLE = "Wazuh SIEM & XDR Deployment Guide"
WAZUH_DESC = (
    "Comprehensive guide detailing Wazuh deployment options across AWS Cloud "
    "(ap-southeast-5 Graviton), On-Premises AlmaLinux 10, and local WSL2 Windows 11 "
    "demo environments with Podman."
)
WAZUH_MD_URL = "docs/engineering/wazuh-installation.md"


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
    def setUpClass(cls) -> None:
        cls.content = _read(WAZUH_DOC_PATH)
        cls.front_matter, cls.body_text = _parse_front_matter(cls.content)

    def test_file_exists(self) -> None:
        self.assertTrue(os.path.isfile(WAZUH_DOC_PATH))

    def test_starts_with_front_matter_delimiter(self) -> None:
        self.assertTrue(self.content.startswith("---\n"))

    def test_required_okf_fields_present(self) -> None:
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_layout_is_default(self) -> None:
        self.assertEqual(self.front_matter["layout"], "default")

    def test_okf_version_is_expected_value(self) -> None:
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_title_field_value(self) -> None:
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

    def test_type_matches_prepare_docs_inference(self) -> None:
    def test_type_matches_prepare_docs_inference(self):
        inferred_type = prepare_docs.infer_okf_type(
            "docs/engineering/wazuh-installation.md"
        )
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_contain_expected_keywords(self) -> None:
    def test_topics_contain_expected_keywords(self):
        expected_topics = ["wazuh", "siem", "xdr", "aws", "almalinux10", "wsl2", "podman", "security"]
        for topic in expected_topics:
            self.assertIn(topic, self.front_matter["topics"])

    def test_topics_exact_match(self):
        self.assertEqual(
            self.front_matter["topics"],
            ["wazuh", "siem", "xdr", "aws", "almalinux10", "wsl2", "podman", "security"],
        )

    def test_timestamp_matches_iso8601_with_offset(self):
        self.assertRegex(
            self.front_matter["timestamp"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$",
        )
        self.assertTrue(self.front_matter["timestamp"].startswith("2026-08-13T"))

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        self.assertEqual(heading_match.group(1).strip(), self.front_matter["title"])

    def test_front_matter_has_exactly_six_keys(self):
        # Guards against accidental extra/duplicate keys being introduced.
        self.assertEqual(
            sorted(self.front_matter.keys()),
            sorted(["layout", "okf_version", "type", "title", "timestamp", "topics"]),
        )


class WazuhDocContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of docs/engineering/wazuh-installation.md."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.content = _read(WAZUH_DOC_PATH)

    def test_contains_top_level_heading(self) -> None:
    def setUpClass(cls):
        cls.content = _read(WAZUH_DOC_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn(
            "# Wazuh SIEM & XDR Deployment Guide: AWS Cloud, On-Premises AlmaLinux 10 & WSL2 Demo",
            self.content,
        )

    def test_sections_present(self) -> None:
        headings = [
            "## 🏛️ 1. Wazuh Architecture & Sizing Guidelines",
            "## 💸 2. On Cloud Plan: AWS Malaysia (`ap-southeast-5`)",
            "## 🏢 3. On-Premises Plan: AlmaLinux 10 / Enterprise RHEL 10",
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

    def test_mentions_wsl2_and_almalinux(self) -> None:
    def test_mentions_wsl2_and_almalinux(self):
        self.assertIn("AlmaLinux 10", self.content)
        self.assertIn("WSL2", self.content)
        self.assertIn("vm.max_map_count=262144", self.content)
        self.assertIn("Podman", self.content)

    def test_security_compliance_tag_precedes_heading(self):
        tag_index = self.content.find("**[SECURITY & COMPLIANCE]**")
        heading_index = self.content.find(f"# {WAZUH_TITLE}")
        self.assertNotEqual(tag_index, -1)
        self.assertNotEqual(heading_index, -1)
        self.assertLess(tag_index, heading_index)

    def test_hardware_sizing_table_contains_all_tiers(self):
        for tier in [
            "Development / Demo (WSL2)",
            "Light Production / Branch",
            "Standard Enterprise",
            "High Throughput Cluster",
        ]:
            with self.subTest(tier=tier):
                self.assertIn(tier, self.content)

    def test_security_group_ports_table_contains_all_ports(self):
        for port in ["`22`", "`443`", "`1514`", "`1515`", "`55000`"]:
            with self.subTest(port=port):
                self.assertIn(port, self.content)

    def test_cost_breakdown_table_totals_present(self):
        for total in [
            "**$34.68 / RM 156.07**",
            "**$65.71 / RM 295.70**",
            "**$40.52 / RM 182.35**",
            "**$153.16 / RM 689.23**",
        ]:
            with self.subTest(total=total):
                self.assertIn(total, self.content)

    def test_agent_enrollment_targets_present(self):
        self.assertIn("### Linux Target (Debian / Ubuntu):", self.content)
        self.assertIn("### Linux Target (AlmaLinux / RHEL / Rocky):", self.content)
        self.assertIn("### Windows Target (PowerShell):", self.content)

    def test_default_dashboard_credentials_documented(self):
        self.assertIn("**Username:** `admin`", self.content)
        self.assertIn("SecretPassword1!", self.content)

    def test_markdown_code_fences_are_balanced(self):
        fence_count = self.content.count("```")
        self.assertEqual(fence_count % 2, 0, "Unbalanced ``` code fence markers found")
        self.assertGreater(fence_count, 0)

    def test_footer_attribution_present(self):
        self.assertIn(
            "*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-13*",
            self.content,
        )


class IndexAndSummaryIntegrationTestCase(unittest.TestCase):
    """Tests for index.md, SUMMARY.md, and llms.txt integration."""

    def test_index_md_link_present(self) -> None:
    def test_index_md_link_present(self):
        content = _read(INDEX_PATH)
        self.assertIn(
            "[Wazuh SIEM & XDR Deployment Guide](engineering/wazuh-installation.html)",
            content,
        )

    def test_summary_md_link_present(self) -> None:
    def test_summary_md_link_present(self):
        content = _read(SUMMARY_PATH)
        self.assertIn(
            "[Wazuh SIEM & XDR Deployment Guide](docs/engineering/wazuh-installation.md)",
            content,
        )

    def test_llms_txt_link_present(self) -> None:
    def test_llms_txt_link_present(self):
        content = _read(LLMS_PATH)
        self.assertIn(
            "[Wazuh SIEM & XDR Deployment Guide](docs/engineering/wazuh-installation.md)",
            content,
        )

    def test_index_md_entry_in_deployment_cicd_section_with_full_description(self):
        content = _read(INDEX_PATH)
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n### |\n---|\Z)",
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        expected_bullet = (
            f"- **[{WAZUH_SHORT_TITLE}](engineering/wazuh-installation.html):** {WAZUH_DESC}"
        )
        self.assertIn(expected_bullet, section_match.group(1))

    def test_index_md_wazuh_listed_before_asimp(self):
        content = _read(INDEX_PATH)
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n### |\n---|\Z)",
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section = section_match.group(1)
        wazuh_index = section.find("wazuh-installation.html")
        asimp_index = section.find("asimp-for-ai-agents.html")
        self.assertNotEqual(wazuh_index, -1)
        self.assertNotEqual(asimp_index, -1)
        self.assertLess(wazuh_index, asimp_index)

    def test_summary_md_entry_in_deployment_section(self):
        content = _read(SUMMARY_PATH)
        section_match = re.search(
            r"## Deployment, Automation, and Costing\n\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            f"* [{WAZUH_SHORT_TITLE}]({WAZUH_MD_URL})",
            section_match.group(1),
        )

    def test_summary_md_wazuh_listed_before_asimp(self):
        content = _read(SUMMARY_PATH)
        section_match = re.search(
            r"## Deployment, Automation, and Costing\n\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section = section_match.group(1)
        wazuh_index = section.find("wazuh-installation.md")
        asimp_index = section.find("asimp-for-ai-agents.md")
        self.assertNotEqual(wazuh_index, -1)
        self.assertNotEqual(asimp_index, -1)
        self.assertLess(wazuh_index, asimp_index)

    def test_llms_txt_entry_in_deployment_section_with_full_description(self):
        content = _read(LLMS_PATH)
        section_match = re.search(
            r"## Deployment, Automation, and Costing\n\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        expected_entry = f"- [{WAZUH_SHORT_TITLE}]({WAZUH_MD_URL}) : {WAZUH_DESC}"
        self.assertIn(expected_entry, section_match.group(1))

    def test_no_duplicate_entries_across_index_summary_llms(self):
        index_content = _read(INDEX_PATH)
        summary_content = _read(SUMMARY_PATH)
        llms_content = _read(LLMS_PATH)

        self.assertEqual(index_content.count("wazuh-installation.html"), 1)
        self.assertEqual(summary_content.count("wazuh-installation.md"), 1)
        self.assertEqual(llms_content.count("wazuh-installation.md"), 1)


class SitemapIntegrationTestCase(unittest.TestCase):
    """Tests for sitemaps txt/xml integration."""

    def test_text_sitemaps_contain_expected_urls(self) -> None:
    def test_text_sitemaps_contain_expected_urls(self):
        for path in [DOCS_SITEMAP_TXT, ROOT_SITEMAP_TXT]:
            with self.subTest(path=path):
                content = _read(path)
                self.assertIn(GH_URL, content)
                self.assertIn(GB_URL, content)

    def test_xml_sitemaps_contain_expected_locs(self) -> None:
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

    def test_xml_sitemap_entry_metadata_values(self):
        for path in [DOCS_SITEMAP_XML, ROOT_SITEMAP_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                found = False
                for url_node in root.findall(f"{SITEMAP_NS}url"):
                    loc_node = url_node.find(f"{SITEMAP_NS}loc")
                    if loc_node is not None and loc_node.text == GH_URL:
                        found = True
                        lastmod_node = url_node.find(f"{SITEMAP_NS}lastmod")
                        changefreq_node = url_node.find(f"{SITEMAP_NS}changefreq")
                        priority_node = url_node.find(f"{SITEMAP_NS}priority")
                        self.assertIsNotNone(lastmod_node)
                        self.assertIsNotNone(changefreq_node)
                        self.assertIsNotNone(priority_node)
                        self.assertEqual(lastmod_node.text, "2026-08-13")
                        self.assertEqual(changefreq_node.text, "weekly")
                        self.assertEqual(priority_node.text, "0.6")
                        break
                self.assertTrue(found, f"Wazuh sitemap entry not found in {path}")

    def test_priority_matches_generate_sitemaps_logic(self):
        # Nested (non-root) documentation pages should be assigned priority 0.6,
        # matching generate_sitemaps.generate_sitemap_urls's priority rule.
        gh_urls, gb_urls = generate_sitemaps.generate_sitemap_urls(
            ["engineering/wazuh-installation.md"],
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra",
            "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra",
            os.path.join(REPO_ROOT, "docs"),
            REPO_ROOT,
        )
        # gh_urls[0] is always the homepage; gh_urls[1] is the Wazuh entry.
        wazuh_entry = gh_urls[1]
        self.assertEqual(wazuh_entry["url"], GH_URL)
        self.assertEqual(wazuh_entry["priority"], "0.6")
        self.assertEqual(wazuh_entry["changefreq"], "weekly")
        # gb_urls[0] is the homepage, gb_urls[1] is the Wazuh entry (root README/
        # AGENTS/CHANGELOG/HISTORY entries, if present, are appended afterwards).
        self.assertEqual(
            gb_urls[0],
            "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/",
        )
        self.assertEqual(gb_urls[1], GB_URL)

    def test_no_duplicate_sitemap_entries(self):
        for path in [DOCS_SITEMAP_TXT, ROOT_SITEMAP_TXT]:
            with self.subTest(path=path):
                lines = [line.strip() for line in _read(path).splitlines() if line.strip()]
                self.assertEqual(lines.count(GH_URL), 1)
                self.assertEqual(lines.count(GB_URL), 1)

        for path in [DOCS_SITEMAP_XML, ROOT_SITEMAP_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                locs = [
                    loc.text
                    for loc in root.findall(f"{SITEMAP_NS}url/{SITEMAP_NS}loc")
                ]
                self.assertEqual(locs.count(GH_URL), 1)


class LlmsCompiledAssetsIntegrationTestCase(unittest.TestCase):
    """Tests for the compiled llms-full.txt and llms-context.xml assets."""

    def test_root_and_docs_llms_full_txt_are_identical(self):
        self.assertEqual(_read(ROOT_LLMS_FULL), _read(DOCS_LLMS_FULL))

    def test_root_and_docs_llms_context_xml_are_identical(self):
        self.assertEqual(_read(ROOT_LLMS_XML), _read(DOCS_LLMS_XML))

    def test_llms_full_txt_contains_wazuh_section_heading_and_desc(self):
        for path in [ROOT_LLMS_FULL, DOCS_LLMS_FULL]:
            with self.subTest(path=path):
                content = _read(path)
                self.assertIn(f"## {WAZUH_SHORT_TITLE}", content)
                self.assertIn(f"*{WAZUH_DESC}*", content)
                self.assertIn(f"# {WAZUH_TITLE}", content)

    def test_llms_full_txt_wazuh_section_appears_once(self):
        for path in [ROOT_LLMS_FULL, DOCS_LLMS_FULL]:
            with self.subTest(path=path):
                content = _read(path)
                self.assertEqual(content.count(f"## {WAZUH_SHORT_TITLE}"), 1)

    def test_llms_context_xml_is_well_formed(self):
        for path in [ROOT_LLMS_XML, DOCS_LLMS_XML]:
            with self.subTest(path=path):
                try:
                    ET.parse(path)
                except ET.ParseError as e:
                    self.fail(f"{path} is not valid XML: {e}")

    def test_llms_context_xml_document_node_attributes(self):
        for path in [ROOT_LLMS_XML, DOCS_LLMS_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                doc_nodes = root.findall(f".//document[@url='{WAZUH_MD_URL}']")
                self.assertEqual(len(doc_nodes), 1, f"Expected exactly one Wazuh document node in {path}")
                doc_node = doc_nodes[0]
                self.assertEqual(doc_node.attrib.get("title"), WAZUH_SHORT_TITLE)
                self.assertEqual(doc_node.attrib.get("desc"), WAZUH_DESC)

    def test_llms_context_xml_document_content_matches_source_body(self):
        with open(WAZUH_DOC_PATH, "r", encoding="utf-8") as f:
            raw_md = f.read()
        expected_body = generate_llms_assets.strip_front_matter(raw_md).strip()

        for path in [ROOT_LLMS_XML, DOCS_LLMS_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                doc_node = root.find(f".//document[@url='{WAZUH_MD_URL}']")
                self.assertIsNotNone(doc_node)
                self.assertEqual(doc_node.text.strip(), expected_body)

    def test_llms_context_xml_document_appears_within_deployment_section(self):
        for path in [ROOT_LLMS_XML, DOCS_LLMS_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                deployment_section = None
                for section in root.findall("section"):
                    if section.attrib.get("title") == "Deployment, Automation, and Costing":
                        deployment_section = section
                        break
                self.assertIsNotNone(deployment_section, f"Deployment section missing in {path}")
                doc_node = deployment_section.find(f"document[@url='{WAZUH_MD_URL}']")
                self.assertIsNotNone(doc_node, f"Wazuh document not nested in the Deployment section of {path}")


if __name__ == "__main__":
    unittest.main()
