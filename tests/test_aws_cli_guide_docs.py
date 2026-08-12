#!/usr/bin/env python3
"""Unit tests for the "AWS CLI Installation and Infrastructure Discovery Guide" documentation.

This introduces a new documentation page (``docs/engineering/aws-cli-guide.md``)
and wires it up in several other files:
* ``docs/index.md`` -- adds a bullet link under "Deployment & CI/CD"
* ``llms.txt``        -- adds an AI-agent entry under "Deployment, Automation, and Costing"
* ``sitemap.txt``     -- adds GitHub Pages and GitBook URLs
* ``sitemap.xml``     -- adds a URL entry
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
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
CLI_GUIDE_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "aws-cli-guide.md")

DOCS_SITEMAP_TXT_PATH = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_TXT_PATH = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_XML_PATH = os.path.join(REPO_ROOT, "docs", "sitemap.xml")
ROOT_SITEMAP_XML_PATH = os.path.join(REPO_ROOT, "sitemap.xml")

EXPECTED_GH_URL = (
    "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
    "engineering/aws-cli-guide.html"
)
EXPECTED_GB_URL = (
    "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/"
    "docs/engineering/aws-cli-guide"
)

SITEMAP_XML_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class IndexMdAwsCliGuideLinkTestCase(unittest.TestCase):
    """Tests for the new link added to docs/index.md."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.content = _read(INDEX_PATH)

    def test_index_file_exists(self) -> None:
        self.assertTrue(os.path.isfile(INDEX_PATH))

    def test_cli_guide_link_present(self) -> None:
        self.assertIn("(engineering/aws-cli-guide.html)", self.content)

    def test_link_appears_in_deployment_cicd_section(self) -> None:
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n### |\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[AWS CLI Installation and Infrastructure Discovery Guide]"
            "(engineering/aws-cli-guide.html)",
            section_match.group(1),
        )


class AwsCliGuideFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of docs/engineering/aws-cli-guide.md."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.content = _read(CLI_GUIDE_PATH)
        # Validate that the unmodified cls.content begins at line 1, column 1 with the YAML delimiter
        if not cls.content.startswith("---\n"):
            raise AssertionError("Document must begin exactly at line 1, column 1 with '---'")
        parts = cls.content.split("---", 2)
        cls.front_matter_text = parts[1]
        cls.body_text = parts[2]
        cls.front_matter = prepare_docs.parse_yaml_front_matter(
            cls.front_matter_text
        )

    def test_file_exists(self) -> None:
        self.assertTrue(os.path.isfile(CLI_GUIDE_PATH))

    def test_required_okf_fields_present(self) -> None:
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_okf_version_is_expected_value(self) -> None:
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_layout_is_default(self) -> None:
        self.assertEqual(self.front_matter["layout"], "default")

    def test_topics_have_expected_values(self) -> None:
        self.assertEqual(
            self.front_matter["topics"],
            ["aws", "3-tier", "automation", "security"],
        )


class LlmsTxtAwsCliGuideEntryTestCase(unittest.TestCase):
    """Tests for the entry in llms.txt."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.content = _read(LLMS_PATH)

    def test_llms_entry_present(self) -> None:
        self.assertIn("[AWS CLI Guide](docs/engineering/aws-cli-guide.md)", self.content)


class SitemapIntegrationTestCase(unittest.TestCase):
    """Integration tests asserting both text and XML sitemaps include the AWS CLI guide."""

    def test_text_sitemaps_contain_expected_urls(self) -> None:
        for path in [DOCS_SITEMAP_TXT_PATH, ROOT_SITEMAP_TXT_PATH]:
            with self.subTest(path=path):
                content = _read(path)
                lines = [line.strip() for line in content.splitlines() if line.strip()]
                self.assertIn(EXPECTED_GH_URL, lines)
                self.assertIn(EXPECTED_GB_URL, lines)

    def test_xml_sitemaps_contain_expected_locs(self) -> None:
        for path in [DOCS_SITEMAP_XML_PATH, ROOT_SITEMAP_XML_PATH]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                locs = [
                    loc.text
                    for loc in root.findall(f"{SITEMAP_XML_NS}url/{SITEMAP_XML_NS}loc")
                ]
                self.assertIn(EXPECTED_GH_URL, locs)


if __name__ == "__main__":
    unittest.main()
