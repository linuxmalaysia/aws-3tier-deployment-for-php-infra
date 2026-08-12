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

ROOT_SITEMAP_TXT_PATH = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_TXT_PATH = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_XML_PATH = os.path.join(REPO_ROOT, "sitemap.xml")
DOCS_SITEMAP_XML_PATH = os.path.join(REPO_ROOT, "docs", "sitemap.xml")

EXPECTED_GH_URL = (
    "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
    "engineering/aws-cli-guide.html"
)
EXPECTED_GB_URL = (
    "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/"
    "docs/engineering/aws-cli-guide"
)

SITEMAP_XML_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
LASTMOD_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _read(path):
    """Read and return the UTF-8 text content of a file.
    
    Parameters:
    	path: Path to the file to read
    
    Returns:
    	str: The file's text content
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class IndexMdAwsCliGuideLinkTestCase(unittest.TestCase):
    """Tests for the new link added to docs/index.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)

    def test_index_file_exists(self):
        self.assertTrue(os.path.isfile(INDEX_PATH))

    def test_cli_guide_link_present(self):
        self.assertIn("(engineering/aws-cli-guide.html)", self.content)

    def test_link_appears_in_deployment_cicd_section(self):
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
    def setUpClass(cls):
        """Load and parse the AWS CLI guide's front matter and body for the test class."""
        cls.content = _read(CLI_GUIDE_PATH)
        stripped = cls.content.lstrip()
        parts = stripped.split("---", 2)
        cls.front_matter_text = parts[1]
        cls.body_text = parts[2]
        cls.front_matter = prepare_docs.parse_yaml_front_matter(
            cls.front_matter_text
        )

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(CLI_GUIDE_PATH))

    def test_required_okf_fields_present(self):
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_okf_version_is_expected_value(self):
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_layout_is_default(self):
        self.assertEqual(self.front_matter["layout"], "default")

    def test_topics_have_expected_values(self):
        self.assertEqual(
            self.front_matter["topics"],
            ["aws", "3-tier", "automation", "security"],
        )

    def test_type_is_technical_reference_guide(self):
        self.assertEqual(self.front_matter["type"], "Technical Reference Guide")

    def test_title_matches_expected_value(self):
        self.assertEqual(
            self.front_matter["title"],
            "AWS CLI Installation and Infrastructure Discovery Guide",
        )

    def test_timestamp_has_iso8601_format(self):
        self.assertRegex(
            self.front_matter["timestamp"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$",
        )


class AwsCliGuideContentStructureTestCase(unittest.TestCase):
    """Tests for the body content/structure of docs/engineering/aws-cli-guide.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(CLI_GUIDE_PATH)
        stripped = cls.content.lstrip()
        cls.body_text = stripped.split("---", 2)[2]
        cls.front_matter_text = stripped.split("---", 2)[1]
        cls.front_matter = prepare_docs.parse_yaml_front_matter(
            cls.front_matter_text
        )

    def test_h1_title_matches_front_matter_title(self):
        expected_h1 = "# " + self.front_matter["title"]
        self.assertIn(expected_h1, self.body_text)

    def test_expected_top_level_sections_present(self):
        expected_headings = [
            "## 1. Prerequisites",
            "## 2. Installing or Updating to the Latest AWS CLI Version 2",
            "## 3. Configuring the AWS CLI",
            "## 4. Querying and Discovering Our 3-Tier Infrastructure",
            "## 5. Troubleshooting AWS CLI Configuration Errors",
        ]
        for heading in expected_headings:
            self.assertIn(heading, self.body_text)

    def test_headings_appear_in_ascending_order(self):
        headings = [
            "## 1. Prerequisites",
            "## 2. Installing or Updating to the Latest AWS CLI Version 2",
            "## 3. Configuring the AWS CLI",
            "## 4. Querying and Discovering Our 3-Tier Infrastructure",
            "## 5. Troubleshooting AWS CLI Configuration Errors",
        ]
        positions = [self.body_text.index(h) for h in headings]
        self.assertEqual(positions, sorted(positions))

    def test_installation_platforms_covered(self):
        for platform_heading in [
            "### A. Linux (Ubuntu, Debian, RHEL, Rocky Linux, AlmaLinux)",
            "### B. macOS",
            "### C. Windows (PowerShell)",
            "### D. Alternative: Running via Docker",
        ]:
            self.assertIn(platform_heading, self.body_text)

    def test_discovery_subsections_cover_all_infra_layers(self):
        for subsection_heading in [
            "### A. Core Networking & VPC Discovery",
            "### B. Security Groups & Zero-Trust Firewall Audit",
            "### C. Compute Layer & Auto Scaling Groups (ASG)",
            "### D. Application Load Balancer (ALB) and Target Group Health",
            "### E. RDS MariaDB Database Cluster Configuration",
            "### F. ElastiCache Valkey Session Cluster Status",
        ]:
            self.assertIn(subsection_heading, self.body_text)

    def test_troubleshooting_subsections_present(self):
        for subsection_heading in [
            '### A. "ExpiredToken" or "SignatureDoesNotMatch"',
            '### B. "Could not connect to the endpoint URL"',
            '### C. "AccessDenied" or "UnauthorizedOperation"',
        ]:
            self.assertIn(subsection_heading, self.body_text)

    def test_target_region_referenced_throughout_document(self):
        # The guide should consistently instruct engineers to target the
        # Malaysia region rather than relying on a locally-configured default.
        self.assertGreaterEqual(
            self.body_text.count("ap-southeast-5"),
            5,
            "Expected the ap-southeast-5 region to be referenced multiple "
            "times throughout the guide's AWS CLI examples.",
        )

    def test_aws_cli_commands_use_expected_services(self):
        for service_command in [
            "aws ec2 describe-vpcs",
            "aws ec2 describe-subnets",
            "aws ec2 describe-security-groups",
            "aws autoscaling describe-auto-scaling-groups",
            "aws elbv2 describe-load-balancers",
            "aws rds describe-db-instances",
            "aws elasticache describe-replication-groups",
        ]:
            self.assertIn(service_command, self.body_text)

    def test_document_ends_without_trailing_blank_noise(self):
        # The last troubleshooting fix should be the final line of content.
        self.assertIn(
            "Attach the standard AWS-managed `ReadOnlyAccess` policy",
            self.body_text.strip().splitlines()[-1],
        )


class LlmsTxtAwsCliGuideEntryTestCase(unittest.TestCase):
    """Tests for the entry in llms.txt."""

    @classmethod
    def setUpClass(cls):
        """
        Load the llms.txt content for the test class.
        """
        cls.content = _read(LLMS_PATH)

    def test_llms_entry_present(self):
        self.assertIn("[AWS CLI Guide](docs/engineering/aws-cli-guide.md)", self.content)

    def test_llms_entry_appears_in_deployment_automation_costing_section(self):
        section_match = re.search(
            r"## Deployment, Automation, and Costing\n(.*?)(?=\n## |\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[AWS CLI Guide](docs/engineering/aws-cli-guide.md)",
            section_match.group(1),
        )

    def test_llms_entry_is_first_bullet_in_its_section(self):
        section_match = re.search(
            r"## Deployment, Automation, and Costing\n(.*?)(?=\n## |\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        bullet_lines = [
            line
            for line in section_match.group(1).splitlines()
            if line.strip().startswith("- ")
        ]
        self.assertTrue(bullet_lines)
        self.assertTrue(
            bullet_lines[0].startswith("- [AWS CLI Guide]"),
            f"Expected AWS CLI Guide to be the first bullet, got: {bullet_lines[0]!r}",
        )

    def test_llms_entry_occurs_exactly_once(self):
        self.assertEqual(
            self.content.count("[AWS CLI Guide](docs/engineering/aws-cli-guide.md)"),
            1,
        )


class SitemapTxtAwsCliGuideEntryTestCase(unittest.TestCase):
    """Tests for the plain-text sitemap entries covering the new guide."""

    @classmethod
    def setUpClass(cls):
        cls.root_lines = [
            line.strip() for line in _read(ROOT_SITEMAP_TXT_PATH).splitlines() if line.strip()
        ]
        cls.docs_lines = [
            line.strip() for line in _read(DOCS_SITEMAP_TXT_PATH).splitlines() if line.strip()
        ]

    def test_gh_url_present_in_root_sitemap_txt(self):
        self.assertIn(EXPECTED_GH_URL, self.root_lines)

    def test_gb_url_present_in_root_sitemap_txt(self):
        self.assertIn(EXPECTED_GB_URL, self.root_lines)

    def test_gh_url_present_in_docs_sitemap_txt(self):
        self.assertIn(EXPECTED_GH_URL, self.docs_lines)

    def test_gb_url_present_in_docs_sitemap_txt(self):
        self.assertIn(EXPECTED_GB_URL, self.docs_lines)

    def test_gh_url_occurs_exactly_once_in_root_sitemap(self):
        self.assertEqual(self.root_lines.count(EXPECTED_GH_URL), 1)

    def test_gb_url_occurs_exactly_once_in_root_sitemap(self):
        self.assertEqual(self.root_lines.count(EXPECTED_GB_URL), 1)

    def test_gh_url_ordered_between_sop_and_asimp_entries(self):
        sop_url = (
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
            "engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.html"
        )
        asimp_url = (
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
            "engineering/asimp-output.html"
        )
        self.assertIn(sop_url, self.root_lines)
        self.assertIn(asimp_url, self.root_lines)
        sop_idx = self.root_lines.index(sop_url)
        cli_idx = self.root_lines.index(EXPECTED_GH_URL)
        asimp_idx = self.root_lines.index(asimp_url)
        self.assertTrue(sop_idx < cli_idx < asimp_idx)

    def test_root_and_docs_sitemap_txt_are_identical(self):
        self.assertEqual(self.root_lines, self.docs_lines)


class SitemapXmlAwsCliGuideEntryTestCase(unittest.TestCase):
    """Tests for the XML sitemap entry covering the new guide."""

    @classmethod
    def setUpClass(cls):
        cls.root_tree = ET.parse(ROOT_SITEMAP_XML_PATH)
        cls.docs_tree = ET.parse(DOCS_SITEMAP_XML_PATH)

    @staticmethod
    def _find_url_entry(tree, loc_value):
        root = tree.getroot()
        for url_el in root.findall(f"{SITEMAP_XML_NS}url"):
            loc_el = url_el.find(f"{SITEMAP_XML_NS}loc")
            if loc_el is not None and loc_el.text == loc_value:
                return url_el
        return None

    def test_url_entry_present_in_root_sitemap_xml(self):
        url_el = self._find_url_entry(self.root_tree, EXPECTED_GH_URL)
        self.assertIsNotNone(url_el, "aws-cli-guide URL missing from root sitemap.xml")

        lastmod = url_el.find(f"{SITEMAP_XML_NS}lastmod")
        changefreq = url_el.find(f"{SITEMAP_XML_NS}changefreq")
        priority = url_el.find(f"{SITEMAP_XML_NS}priority")

        self.assertIsNotNone(lastmod)
        self.assertRegex(lastmod.text, LASTMOD_DATE_RE)
        self.assertEqual(changefreq.text, "weekly")
        self.assertEqual(priority.text, "0.6")

    def test_url_entry_present_in_docs_sitemap_xml(self):
        url_el = self._find_url_entry(self.docs_tree, EXPECTED_GH_URL)
        self.assertIsNotNone(url_el, "aws-cli-guide URL missing from docs/sitemap.xml")

        changefreq = url_el.find(f"{SITEMAP_XML_NS}changefreq")
        priority = url_el.find(f"{SITEMAP_XML_NS}priority")
        self.assertEqual(changefreq.text, "weekly")
        self.assertEqual(priority.text, "0.6")

    def test_url_entry_appears_exactly_once_in_root_sitemap_xml(self):
        root = self.root_tree.getroot()
        matches = [
            url_el
            for url_el in root.findall(f"{SITEMAP_XML_NS}url")
            if url_el.find(f"{SITEMAP_XML_NS}loc") is not None
            and url_el.find(f"{SITEMAP_XML_NS}loc").text == EXPECTED_GH_URL
        ]
        self.assertEqual(len(matches), 1)

    def test_root_and_docs_sitemap_xml_locs_match(self):
        root_locs = [
            loc.text
            for loc in self.root_tree.getroot().findall(f"{SITEMAP_XML_NS}url/{SITEMAP_XML_NS}loc")
        ]
        docs_locs = [
            loc.text
            for loc in self.docs_tree.getroot().findall(f"{SITEMAP_XML_NS}url/{SITEMAP_XML_NS}loc")
        ]
        self.assertEqual(root_locs, docs_locs)
        self.assertIn(EXPECTED_GH_URL, root_locs)


if __name__ == "__main__":
    unittest.main()
