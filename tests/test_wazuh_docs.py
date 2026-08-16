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

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import prepare_docs  # noqa: E402
import generate_llms_assets  # noqa: E402

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
SUMMARY_PATH = os.path.join(REPO_ROOT, "SUMMARY.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
WAZUH_DOC_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "wazuh-installation.md")
ROOT_SITEMAP_TXT = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_TXT = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_XML = os.path.join(REPO_ROOT, "sitemap.xml")
DOCS_SITEMAP_XML = os.path.join(REPO_ROOT, "docs", "sitemap.xml")
ROOT_LLMS_CONTEXT_XML = os.path.join(REPO_ROOT, "llms-context.xml")
DOCS_LLMS_CONTEXT_XML = os.path.join(REPO_ROOT, "docs", "llms-context.xml")
ROOT_LLMS_FULL_TXT = os.path.join(REPO_ROOT, "llms-full.txt")
DOCS_LLMS_FULL_TXT = os.path.join(REPO_ROOT, "docs", "llms-full.txt")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

GH_BASE = "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
GB_BASE = "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/"

GH_URL = GH_BASE + "engineering/wazuh-installation.html"
GB_URL = GB_BASE + "engineering/wazuh-installation"

WAZUH_TITLE = "Wazuh SIEM & XDR Deployment Guide: AWS Cloud, On-Premises AlmaLinux 10 & WSL2 Demo"
WAZUH_SUMMARY_TITLE = "Wazuh SIEM & XDR Deployment Guide"
WAZUH_DESC = (
    "Comprehensive guide detailing Wazuh deployment options across AWS Cloud "
    "(ap-southeast-5 Graviton), On-Premises AlmaLinux 10, and local WSL2 "
    "Windows 11 demo environments with Podman."
)


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

    def test_type_matches_prepare_docs_inference(self):
        inferred_type = prepare_docs.infer_okf_type(
            "docs/engineering/wazuh-installation.md"
        )
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_contain_expected_keywords(self):
        expected_topics = ["wazuh", "siem", "xdr", "aws", "almalinux10", "wsl2", "podman", "security"]
        for topic in expected_topics:
            self.assertIn(topic, self.front_matter["topics"])

    def test_topics_match_authored_values_exactly(self):
        self.assertEqual(
            self.front_matter["topics"],
            ["wazuh", "siem", "xdr", "aws", "almalinux10", "wsl2", "podman", "security"],
        )

    def test_timestamp_matches_iso8601_with_offset(self):
        self.assertRegex(
            self.front_matter["timestamp"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$",
        )

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        self.assertEqual(heading_match.group(1).strip(), self.front_matter["title"])


class WazuhDocContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of docs/engineering/wazuh-installation.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(WAZUH_DOC_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn(
            "# Wazuh SIEM & XDR Deployment Guide: AWS Cloud, On-Premises AlmaLinux 10 & WSL2 Demo",
            self.content,
        )

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

    def test_mentions_wsl2_and_almalinux(self):
        self.assertIn("AlmaLinux 10", self.content)
        self.assertIn("WSL2", self.content)
        self.assertIn("vm.max_map_count=262144", self.content)
        self.assertIn("Podman", self.content)


class IndexAndSummaryIntegrationTestCase(unittest.TestCase):
    """Tests for index.md, SUMMARY.md, and llms.txt integration."""

    def test_index_md_link_present(self):
        content = _read(INDEX_PATH)
        self.assertIn(
            "[Wazuh SIEM & XDR Deployment Guide](engineering/wazuh-installation.html)",
            content,
        )

    def test_index_md_link_includes_description(self):
        content = _read(INDEX_PATH)
        self.assertIn(
            "[Wazuh SIEM & XDR Deployment Guide](engineering/wazuh-installation.html):** "
            + WAZUH_DESC,
            content,
        )

    def test_index_md_appears_in_deployment_cicd_section_first(self):
        content = _read(INDEX_PATH)
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n### |\n---|\Z)",
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section_body = section_match.group(1)
        self.assertIn(
            "[Wazuh SIEM & XDR Deployment Guide](engineering/wazuh-installation.html)",
            section_body,
        )
        # The Wazuh entry was inserted as the first bullet in this section,
        # ahead of the pre-existing ASIMP for AI Agents entry.
        wazuh_pos = section_body.find("Wazuh SIEM & XDR Deployment Guide")
        asimp_pos = section_body.find("ASIMP for AI Agents")
        self.assertNotEqual(wazuh_pos, -1)
        self.assertNotEqual(asimp_pos, -1)
        self.assertLess(wazuh_pos, asimp_pos)

    def test_summary_md_link_present(self):
        content = _read(SUMMARY_PATH)
        self.assertIn(
            "[Wazuh SIEM & XDR Deployment Guide](docs/engineering/wazuh-installation.md)",
            content,
        )

    def test_summary_md_appears_in_deployment_section_first(self):
        content = _read(SUMMARY_PATH)
        section_match = re.search(
            r"## Deployment, Automation, and Costing\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section_body = section_match.group(1)
        wazuh_pos = section_body.find("Wazuh SIEM & XDR Deployment Guide")
        asimp_pos = section_body.find("ASIMP for AI Agents")
        self.assertNotEqual(wazuh_pos, -1)
        self.assertNotEqual(asimp_pos, -1)
        self.assertLess(wazuh_pos, asimp_pos)

    def test_llms_txt_link_present(self):
        content = _read(LLMS_PATH)
        self.assertIn(
            "[Wazuh SIEM & XDR Deployment Guide](docs/engineering/wazuh-installation.md)",
            content,
        )

    def test_llms_txt_link_includes_description(self):
        content = _read(LLMS_PATH)
        self.assertIn(
            "[Wazuh SIEM & XDR Deployment Guide](docs/engineering/wazuh-installation.md) : "
            + WAZUH_DESC,
            content,
        )

    def test_llms_txt_parses_wazuh_entry_via_generate_llms_assets(self):
        content = _read(LLMS_PATH)
        parsed = generate_llms_assets.parse_llms_file(content)
        self.assertIn("Deployment, Automation, and Costing", parsed.sections)
        section_links = parsed.sections["Deployment, Automation, and Costing"]
        wazuh_links = [
            link for link in section_links
            if link["url"] == "docs/engineering/wazuh-installation.md"
        ]
        self.assertEqual(len(wazuh_links), 1)
        self.assertEqual(wazuh_links[0]["title"], WAZUH_SUMMARY_TITLE)
        self.assertEqual(wazuh_links[0]["desc"], WAZUH_DESC)
        # Confirm it is the first entry in the section (matches diff ordering).
        self.assertEqual(section_links[0]["url"], "docs/engineering/wazuh-installation.md")


class SitemapIntegrationTestCase(unittest.TestCase):
    """Tests for sitemaps txt/xml integration."""

    def test_text_sitemaps_contain_expected_urls(self):
        for path in [DOCS_SITEMAP_TXT, ROOT_SITEMAP_TXT]:
            with self.subTest(path=path):
                content = _read(path)
                self.assertIn(GH_URL, content)
                self.assertIn(GB_URL, content)

    def test_text_sitemaps_urls_immediately_follow_summary_entry(self):
        for path in [DOCS_SITEMAP_TXT, ROOT_SITEMAP_TXT]:
            with self.subTest(path=path):
                lines = [line.strip() for line in _read(path).splitlines() if line.strip()]
                gh_summary = GH_BASE + "SUMMARY.html"
                gb_summary = GB_BASE + "SUMMARY"
                self.assertIn(gh_summary, lines)
                self.assertIn(gb_summary, lines)
                self.assertEqual(lines[lines.index(gh_summary) + 1], GH_URL)
                self.assertEqual(lines[lines.index(gb_summary) + 1], GB_URL)

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

    def test_xml_sitemaps_url_entry_has_expected_fields(self):
        for path in [DOCS_SITEMAP_XML, ROOT_SITEMAP_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                matched = None
                for url_el in root.findall(f"{SITEMAP_NS}url"):
                    loc_el = url_el.find(f"{SITEMAP_NS}loc")
                    if loc_el is not None and loc_el.text == GH_URL:
                        matched = url_el
                        break
                self.assertIsNotNone(matched, f"No <url> entry found for {GH_URL} in {path}")

                lastmod = matched.find(f"{SITEMAP_NS}lastmod")
                changefreq = matched.find(f"{SITEMAP_NS}changefreq")
                priority = matched.find(f"{SITEMAP_NS}priority")

                self.assertIsNotNone(lastmod)
                self.assertIsNotNone(changefreq)
                self.assertIsNotNone(priority)

                self.assertEqual(lastmod.text, "2026-08-13")
                self.assertEqual(changefreq.text, "weekly")
                self.assertEqual(priority.text, "0.6")

    def test_root_and_docs_sitemap_txt_are_identical(self):
        self.assertEqual(_read(ROOT_SITEMAP_TXT), _read(DOCS_SITEMAP_TXT))

    def test_root_and_docs_sitemap_xml_are_identical(self):
        self.assertEqual(_read(ROOT_SITEMAP_XML), _read(DOCS_SITEMAP_XML))


class LlmsContextXmlIntegrationTestCase(unittest.TestCase):
    """Tests for llms-context.xml / docs/llms-context.xml integration."""

    @classmethod
    def setUpClass(cls):
        cls.root_content = _read(ROOT_LLMS_CONTEXT_XML)
        cls.docs_content = _read(DOCS_LLMS_CONTEXT_XML)

    def test_files_exist(self):
        self.assertTrue(os.path.isfile(ROOT_LLMS_CONTEXT_XML))
        self.assertTrue(os.path.isfile(DOCS_LLMS_CONTEXT_XML))

    def test_root_and_docs_copies_are_identical(self):
        self.assertEqual(self.root_content, self.docs_content)

    def test_documents_are_well_formed_xml(self):
        for content, label in [(self.root_content, "root"), (self.docs_content, "docs")]:
            with self.subTest(label=label):
                try:
                    ET.fromstring(content)
                except ET.ParseError as e:
                    self.fail(f"{label} llms-context.xml is not valid XML: {e}")

    def test_wazuh_document_tag_present_with_expected_attributes(self):
        expected_tag = (
            '<document title="Wazuh SIEM &amp; XDR Deployment Guide" '
            'url="docs/engineering/wazuh-installation.md" '
            f'desc="{generate_llms_assets.escape_xml_text(WAZUH_DESC)}">'
        )
        for content, label in [(self.root_content, "root"), (self.docs_content, "docs")]:
            with self.subTest(label=label):
                self.assertIn(expected_tag, content)

    def test_wazuh_document_precedes_asimp_document_in_deployment_section(self):
        for content, label in [(self.root_content, "root"), (self.docs_content, "docs")]:
            with self.subTest(label=label):
                section_match = re.search(
                    r'<section title="Deployment, Automation, and Costing">(.*?)</section>',
                    content,
                    re.DOTALL,
                )
                self.assertIsNotNone(section_match)
                section_body = section_match.group(1)
                wazuh_pos = section_body.find('title="Wazuh SIEM &amp; XDR Deployment Guide"')
                asimp_pos = section_body.find('title="ASIMP for AI Agents"')
                self.assertNotEqual(wazuh_pos, -1)
                self.assertNotEqual(asimp_pos, -1)
                self.assertLess(wazuh_pos, asimp_pos)

    def test_wazuh_document_body_contains_key_content(self):
        for content, label in [(self.root_content, "root"), (self.docs_content, "docs")]:
            with self.subTest(label=label):
                self.assertIn("vm.max_map_count=262144", content)
                self.assertIn("AlmaLinux 10", content)


class LlmsFullTxtIntegrationTestCase(unittest.TestCase):
    """Tests for llms-full.txt / docs/llms-full.txt integration."""

    @classmethod
    def setUpClass(cls):
        cls.root_content = _read(ROOT_LLMS_FULL_TXT)
        cls.docs_content = _read(DOCS_LLMS_FULL_TXT)

    def test_files_exist(self):
        self.assertTrue(os.path.isfile(ROOT_LLMS_FULL_TXT))
        self.assertTrue(os.path.isfile(DOCS_LLMS_FULL_TXT))

    def test_root_and_docs_copies_are_identical(self):
        self.assertEqual(self.root_content, self.docs_content)

    def test_wazuh_section_heading_and_description_present(self):
        for content, label in [(self.root_content, "root"), (self.docs_content, "docs")]:
            with self.subTest(label=label):
                self.assertIn(f"## {WAZUH_SUMMARY_TITLE}", content)
                self.assertIn(f"*{WAZUH_DESC}*", content)

    def test_wazuh_section_precedes_asimp_section(self):
        for content, label in [(self.root_content, "root"), (self.docs_content, "docs")]:
            with self.subTest(label=label):
                wazuh_pos = content.find(f"## {WAZUH_SUMMARY_TITLE}")
                asimp_pos = content.find("## ASIMP for AI Agents")
                self.assertNotEqual(wazuh_pos, -1)
                self.assertNotEqual(asimp_pos, -1)
                self.assertLess(wazuh_pos, asimp_pos)

    def test_wazuh_section_contains_full_document_body(self):
        for content, label in [(self.root_content, "root"), (self.docs_content, "docs")]:
            with self.subTest(label=label):
                self.assertIn(
                    "# Wazuh SIEM & XDR Deployment Guide: AWS Cloud, "
                    "On-Premises AlmaLinux 10 & WSL2 Demo",
                    content,
                )
                self.assertIn("podman-compose up -d", content)


class GeneratedAssetsRegenerationConsistencyTestCase(unittest.TestCase):
    """Regression test ensuring the checked-in generated assets match what
    ``generate_llms_assets`` would produce from the current ``llms.txt``.

    This guards against the Wazuh entry (or any future entry) being added to
    ``llms.txt`` without regenerating ``llms-full.txt`` and
    ``llms-context.xml`` (in both the repository root and ``docs/``).
    """

    def test_llms_full_and_context_match_regenerated_output(self):
        llms_content = _read(LLMS_PATH)
        expected_full = generate_llms_assets.compile_llms_full(llms_content, base_dir=REPO_ROOT)
        expected_xml = generate_llms_assets.create_ctx(llms_content, optional=True, base_dir=REPO_ROOT)

        self.assertEqual(_read(ROOT_LLMS_FULL_TXT), expected_full)
        self.assertEqual(_read(DOCS_LLMS_FULL_TXT), expected_full)
        self.assertEqual(_read(ROOT_LLMS_CONTEXT_XML), expected_xml)
        self.assertEqual(_read(DOCS_LLMS_CONTEXT_XML), expected_xml)


if __name__ == "__main__":
    unittest.main()
