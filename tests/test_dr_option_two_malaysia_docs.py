#!/usr/bin/env python3
"""Unit and integration tests for the Disaster Recovery Option Two Malaysia documentation.

This test suite validates that the newly introduced documentation file:
* ``docs/executive/dr-option-two-malaysia.md``

adheres fully to the Open Knowledge Format (OKF) v0.1 YAML front matter contract,
includes standard footer copyright/license references, is mapped correctly from
the docs index and llms.txt, and is successfully published in the sitemaps.
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

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
DR_OPT_TWO_MD_PATH = os.path.join(REPO_ROOT, "docs", "executive", "dr-option-two-malaysia.md")
LAYOUT_PATH = os.path.join(REPO_ROOT, "docs", "_layouts", "default.html")

CONFIG_PATH = os.path.join(REPO_ROOT, "docs", "_config.yml")
DR_OPT_TWO_MD_PATH = os.path.join(REPO_ROOT, "docs", "executive", "dr-option-two-malaysia.md")
LAYOUT_PATH = os.path.join(REPO_ROOT, "docs", "_layouts", "default.html")

DOCS_SITEMAP_TXT_PATH = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_TXT_PATH = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_XML_PATH = os.path.join(REPO_ROOT, "docs", "sitemap.xml")
ROOT_SITEMAP_XML_PATH = os.path.join(REPO_ROOT, "sitemap.xml")

EXPECTED_GH_URL = (
    "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
    "executive/dr-option-two-malaysia.html"
)
EXPECTED_GB_URL = (
    "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/"
    "docs/executive/dr-option-two-malaysia"
)

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _read(path):
    """Utility helper to read a file from a specified path in UTF-8 format."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class DrOptionTwoMalaysiaTestCase(unittest.TestCase):
    """Comprehensive test case for checking OKF front matter, footer metadata,

    content structure, and index/sitemap publication for Option Two documentation.
    """

    def test_files_exist(self):
        """Verifies that the requested Option Two documentation file is present."""
        self.assertTrue(os.path.isfile(DR_OPT_TWO_MD_PATH))

    def test_front_matter_okf_dr_option_two(self):
        """Validates the OKF v0.1 front matter rules for dr-option-two-malaysia.md."""
        content = _read(DR_OPT_TWO_MD_PATH)
        self.assertTrue(content.startswith("---\n"))
        parts = content.split("---", 2)
        fm = prepare_docs.parse_yaml_front_matter(parts[1])
        self.assertEqual(fm["layout"], "default")
        self.assertEqual(fm["okf_version"], "0.1")
        self.assertEqual(fm["type"], "Technical Reference Guide")
        self.assertEqual(
            fm["title"],
            "DR Option Two: Malaysia Region & Cross-Account Replication Strategy",
        )
        self.assertEqual(fm["topics"], ["aws", "3-tier", "disaster-recovery", "pricing"])
        self.assertEqual(fm["timestamp"], "2026-08-11T12:00:00+08:00")

        # Assert timestamp exists and is unquoted in the raw file according to rules
        raw_lines = parts[1].splitlines()
        timestamp_line = [l.strip() for l in raw_lines if l.strip().startswith("timestamp:")]
        self.assertTrue(len(timestamp_line) > 0)
        self.assertEqual(timestamp_line[0], 'timestamp: 2026-08-11T12:00:00+08:00')

    def test_footer_standard_compliance(self):
        """Verifies that the new document adheres fully to the footer standards

        by containing proper Deep State of Mind (DSOM) tags, copyright lines, and GPLv3 licenses.
        """
        content = _read(DR_OPT_TWO_MD_PATH)
        self.assertIn("Deep State of Mind (DSOM) For My AI Protocol", content)
        self.assertTrue(
            "Copyright &copy; 2005 - 2026 Harisfazillah Jamel" in content or
            "Copyright © 2005 - 2026 Harisfazillah Jamel" in content,
            "Copyright line not found in dr-option-two-malaysia.md"
        )
        self.assertIn("GNU General Public License v3.0", content)
        self.assertIn("[linuxmalaysia.com](https://linuxmalaysia.com/)", content)

    def test_links_in_index(self):
        """Verifies that the new documentation page is correctly linked in docs/index.md."""
        index = _read(INDEX_PATH)
        self.assertIn("[DR Option Two Malaysia and Account Separation Guide](executive/dr-option-two-malaysia.html)", index)

    def test_indexed_in_llms_txt(self):
        """Verifies that the new documentation page is correctly indexed in llms.txt."""
        llms = _read(LLMS_PATH)
        self.assertIn("[DR Option Two Malaysia](docs/executive/dr-option-two-malaysia.md)", llms)

    def test_sitemap_publication(self):
        """Verifies publication entries in both XML sitemaps and text sitemaps."""
        sitemaps_txt = [
            os.path.join(REPO_ROOT, "sitemap.txt"),
            os.path.join(REPO_ROOT, "docs", "sitemap.txt")
        ]
        sitemaps_xml = [
            os.path.join(REPO_ROOT, "sitemap.xml"),
            os.path.join(REPO_ROOT, "docs", "sitemap.xml")
        ]

        expected_txt_urls = [
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/executive/dr-option-two-malaysia.html",
            "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/executive/dr-option-two-malaysia"
        ]

        expected_xml_urls = [
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/executive/dr-option-two-malaysia.html"
        ]

        for s_path in sitemaps_txt:
            content = _read(s_path)
            for url in expected_txt_urls:
                self.assertEqual(content.count(url), 1, f"URL {url} count is not 1 in {s_path}")

        import datetime
        for s_path in sitemaps_xml:
            content = _read(s_path)
            for url in expected_xml_urls:
                loc_tag = f"<loc>{url}</loc>"
                self.assertEqual(content.count(loc_tag), 1, f"XML tag {loc_tag} count is not 1 in {s_path}")

            # Parse XML and validate lastmod format and values
            tree = ET.parse(s_path)
            root = tree.getroot()
            for url in expected_xml_urls:
                url_node = None
                for u in root.findall(f"{SITEMAP_NS}url"):
                    loc = u.find(f"{SITEMAP_NS}loc")
                    if loc is not None and loc.text == url:
                        url_node = u
                        break
                self.assertIsNotNone(url_node, f"URL {url} node not found in {s_path}")
                lastmod = url_node.find(f"{SITEMAP_NS}lastmod").text
                self.assertRegex(lastmod, r"^\d{4}-\d{2}-\d{2}$")
                try:
                    datetime.date.fromisoformat(lastmod)
                except ValueError as e:
                    self.fail(f"Invalid lastmod date {lastmod} in {s_path}: {e}")


class ConfigYamlNavbarDrOptionTwoTestCase(unittest.TestCase):
    """Tests for the new navbar entry added to docs/_config.yml."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(CONFIG_PATH)

    def test_config_file_exists(self):
        """Verifies docs/_config.yml is present on disk."""
        self.assertTrue(os.path.isfile(CONFIG_PATH))

    def test_navbar_entry_present(self):
        """Validates the new navbar title/url pair is well-formed."""
        self.assertRegex(
            self.content,
            re.compile(
                r'-\s*title:\s*"DR Option Two Malaysia"\s*\n'
                r'\s*url:\s*"/executive/dr-option-two-malaysia\.html"'
            ),
        )

    def test_navbar_entry_placed_directly_after_dr_evaluation_entry(self):
        """Regression: the new entry must be inserted immediately after the
        existing 'DR Evaluation' entry, matching the PR diff insertion
        point, rather than appended at an arbitrary position."""
        match = re.search(
            r'-\s*title:\s*"DR Evaluation"\s*\n\s*url:\s*"/executive/dr-options-evaluation\.html"\s*\n'
            r'\s*-\s*title:\s*"DR Option Two Malaysia"\s*\n\s*url:\s*"/executive/dr-option-two-malaysia\.html"',
            self.content,
        )
        self.assertIsNotNone(
            match,
            "Expected 'DR Option Two Malaysia' entry directly after 'DR Evaluation'",
        )

    def test_navbar_entry_placed_before_rds_vs_percona_entry(self):
        """The new entry should come before the pre-existing 'RDS vs
        Percona' entry rather than after it."""
        dr_opt_two_idx = self.content.index('title: "DR Option Two Malaysia"')
        rds_idx = self.content.index('title: "RDS vs Percona"')
        self.assertLess(dr_opt_two_idx, rds_idx)

    def test_navbar_title_appears_exactly_once(self):
        self.assertEqual(self.content.count('"DR Option Two Malaysia"'), 1)

    def test_navbar_url_appears_exactly_once(self):
        self.assertEqual(
            self.content.count("/executive/dr-option-two-malaysia.html"), 1
        )

    def test_navbar_url_points_to_existing_doc_file(self):
        """The navbar entry URL should resolve to an actual markdown source
        file that Jekyll can build into dr-option-two-malaysia.html."""
        self.assertTrue(os.path.isfile(DR_OPT_TWO_MD_PATH))

    def test_existing_dr_evaluation_entry_untouched(self):
        """Ensure the pre-existing 'DR Evaluation' navbar entry was not
        accidentally clobbered by the new addition."""
        self.assertIn('title: "DR Evaluation"', self.content)
        self.assertIn('url: "/executive/dr-options-evaluation.html"', self.content)

    def test_existing_rds_vs_percona_entry_untouched(self):
        """Ensure the entry that follows was not accidentally clobbered."""
        self.assertIn('title: "RDS vs Percona"', self.content)
        self.assertIn('url: "/engineering/postgresql-comparison.html"', self.content)


class IndexMdDrOptionTwoLinkPositionTestCase(unittest.TestCase):
    """Tests for exactly where/how the new link was wired into
    docs/index.md (as distinct from simple presence, already covered by
    ``test_links_in_index`` above)."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)

    def test_link_uses_relative_html_url_not_markdown_extension(self):
        self.assertIn("(executive/dr-option-two-malaysia.html)", self.content)
        self.assertNotIn("(executive/dr-option-two-malaysia.md)", self.content)

    def test_link_appears_exactly_once(self):
        self.assertEqual(
            self.content.count("[DR Option Two Malaysia and Account Separation Guide]"),
            1,
        )

    def test_link_appears_in_deployment_cicd_section(self):
        """Regression: per the PR diff, the link is appended to the
        '### Deployment & CI/CD' section (alongside the AWS vs. On-Prem
        comparison guide), not the 'Executive Strategic Blueprints'
        section, despite the target page living under executive/."""
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n### |\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[DR Option Two Malaysia and Account Separation Guide]"
            "(executive/dr-option-two-malaysia.html)",
            section_match.group(1),
        )

    def test_link_appears_after_comparison_guide_link(self):
        comparison_idx = self.content.index(
            "[AWS Services vs. On-Premises Open-Source Comparison Guide]"
            "(engineering/aws-vs-onprem-comparison.html)"
        )
        dr_opt_two_idx = self.content.index(
            "[DR Option Two Malaysia and Account Separation Guide]"
            "(executive/dr-option-two-malaysia.html)"
        )
        self.assertLess(comparison_idx, dr_opt_two_idx)

    def test_link_appears_before_strategic_review_link(self):
        dr_opt_two_idx = self.content.index(
            "[DR Option Two Malaysia and Account Separation Guide]"
            "(executive/dr-option-two-malaysia.html)"
        )
        review_idx = self.content.index(
            "[Strategic Comparative Review: AWS-Native Managed Platform vs. "
            "Self-Hosted Custom Stack](aws-vs-self-hosted-review.html)"
        )
        self.assertLess(dr_opt_two_idx, review_idx)

    def test_link_target_file_exists(self):
        self.assertTrue(os.path.isfile(DR_OPT_TWO_MD_PATH))


class LlmsTxtDrOptionTwoEntryPositionTestCase(unittest.TestCase):
    """Tests for exactly where/how the new entry was wired into llms.txt
    (as distinct from simple presence, already covered by
    ``test_indexed_in_llms_txt`` above)."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LLMS_PATH)

    def test_entry_under_strategic_blueprints_section_heading(self):
        section_match = re.search(
            r"## Core Strategic Blueprints \(Executive\)\n(.*?)(?=\n## |\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[DR Option Two Malaysia](docs/executive/dr-option-two-malaysia.md)",
            section_match.group(1),
        )

    def test_entry_appears_directly_after_dr_evaluation_entry(self):
        dr_eval_idx = self.content.index(
            "[Disaster Recovery Options Evaluation]"
            "(docs/executive/dr-options-evaluation.md)"
        )
        dr_opt_two_idx = self.content.index(
            "[DR Option Two Malaysia](docs/executive/dr-option-two-malaysia.md)"
        )
        self.assertLess(dr_eval_idx, dr_opt_two_idx)
        # Nothing else should be sandwiched between the two entries.
        between = self.content[dr_eval_idx:dr_opt_two_idx]
        self.assertEqual(between.count("\n"), 1)
        self.assertNotIn("\n- [", between.strip("\n"))

    def test_entry_appears_before_hybrid_cloud_entry(self):
        dr_opt_two_idx = self.content.index(
            "[DR Option Two Malaysia](docs/executive/dr-option-two-malaysia.md)"
        )
        hybrid_idx = self.content.index(
            "[Hybrid Cloud Connectivity](docs/executive/hybrid-onprem.md)"
        )
        self.assertLess(dr_opt_two_idx, hybrid_idx)

    def test_entry_follows_bullet_link_colon_description_format(self):
        match = re.search(
            r"^- \[DR Option Two Malaysia\]"
            r"\(docs/executive/dr-option-two-malaysia\.md\) : .+$",
            self.content,
            re.MULTILINE,
        )
        self.assertIsNotNone(
            match, "Entry does not follow the '- [Title](path) : description' format"
        )

    def test_entry_appears_exactly_once(self):
        self.assertEqual(self.content.count("[DR Option Two Malaysia]"), 1)


class CrossFileReferenceConsistencyDrOptionTwoTestCase(unittest.TestCase):
    """Verifies the slug used for dr-option-two-malaysia is consistent
    across docs/_config.yml, docs/index.md, llms.txt, and the filesystem."""

    @classmethod
    def setUpClass(cls):
        cls.config_content = _read(CONFIG_PATH)
        cls.index_content = _read(INDEX_PATH)
        cls.llms_content = _read(LLMS_PATH)

    def test_html_slug_consistent_between_navbar_and_index(self):
        self.assertIn(
            "/executive/dr-option-two-malaysia.html", self.config_content
        )
        self.assertIn(
            "(executive/dr-option-two-malaysia.html)", self.index_content
        )

    def test_markdown_path_consistent_between_llms_txt_and_filesystem(self):
        match = re.search(
            r"\[DR Option Two Malaysia\]\((docs/executive/dr-option-two-malaysia\.md)\)",
            self.llms_content,
        )
        self.assertIsNotNone(match)
        referenced_path = os.path.join(REPO_ROOT, match.group(1))
        self.assertTrue(os.path.isfile(referenced_path))
        self.assertEqual(os.path.normpath(referenced_path), DR_OPT_TWO_MD_PATH)

    def test_slug_does_not_collide_with_existing_dr_options_slugs(self):
        """The new page's slug must be distinct from the pre-existing
        'dr-options' and 'dr-options-evaluation' slugs (i.e. not simply a
        substring collision that would route to the wrong page)."""
        self.assertNotEqual("dr-options-evaluation", "dr-option-two-malaysia")
        self.assertIn("/executive/dr-options.html", self.config_content)
        self.assertIn("/executive/dr-options-evaluation.html", self.config_content)
        self.assertIn("/executive/dr-option-two-malaysia.html", self.config_content)


class DrOptionTwoMalaysiaContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of
    docs/executive/dr-option-two-malaysia.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(DR_OPT_TWO_MD_PATH)

    def test_contains_devops_execution_marker(self):
        self.assertIn("**[DEVOPS EXECUTION]**", self.content)

    def test_contains_h1_title_matching_front_matter(self):
        self.assertIn(
            "# DR Option Two: Malaysia Region & Cross-Account Replication Strategy",
            self.content,
        )

    def test_top_level_numbered_sections_present_and_ordered(self):
        headings = [
            "## 1. DR Option Two Architecture & Sovereignty",
            "## 2. Copying the Production Stack: Step-by-Step Mechanisms",
            "## 3. AWS CLI Infrastructure Discovery Commands",
            "## 4. Disaster Recovery Strategies under Account Separation",
            "## 5. AWS Pricing Calculator Parameters (Copy-Paste Ready)",
            "## 6. Implementation Summary",
        ]
        for heading in headings:
            self.assertIn(heading, self.content)
        indices = [self.content.index(h) for h in headings]
        self.assertEqual(indices, sorted(indices))

    def test_exactly_six_top_level_numbered_sections_exist(self):
        """Regression: guards against accidental duplication or removal of
        a top-level section heading."""
        matches = re.findall(r"^## \d+\. .+$", self.content, re.MULTILINE)
        self.assertEqual(len(matches), 6)

    def test_ap_southeast_5_region_referenced(self):
        self.assertIn("`ap-southeast-5`", self.content)

    def test_pdpa_reference_present(self):
        self.assertIn("Personal Data Protection Act (PDPA)", self.content)

    def test_pdpa_section_129_referenced_for_option_one_contrast(self):
        self.assertIn("PDPA Section 129", self.content)

    def test_contains_cross_account_copying_flow_ascii_diagram(self):
        self.assertIn("```text", self.content)
        self.assertIn("Cross-Account Same-Region Copying Flow", self.content)
        self.assertIn("Primary AWS Account", self.content)
        self.assertIn("Standby DR AWS Account", self.content)

    def test_section_two_subsections_present_and_ordered(self):
        subheadings = [
            "### A. Infrastructure as Code (IaC) Replication",
            "### B. Machine Image Copying (Golden AMIs)",
            "### C. Database Replication (MariaDB RDS)",
            "### D. Object Storage Replication (Amazon S3)",
            "### E. Shared Configurations & Code (Amazon EFS)",
        ]
        for heading in subheadings:
            self.assertIn(heading, self.content)
        indices = [self.content.index(h) for h in subheadings]
        self.assertEqual(indices, sorted(indices))

    def test_database_replication_subsection_lists_three_strategies(self):
        section_match = re.search(
            r"### C\. Database Replication \(MariaDB RDS\)\n(.*?)(?=\n### D\.)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section_text = section_match.group(1)
        self.assertIn("**AWS Backup Cross-Account Copy:**", section_text)
        self.assertIn(
            "**RDS Snapshot Sharing and Restore (RTO: 1-2 Hours, RPO: Daily):**",
            section_text,
        )
        self.assertIn(
            "**GTID-based Binlog replication over VPC Peering (RTO: < 15 Mins, RPO: Seconds):**",
            section_text,
        )

    def test_gtid_replication_sql_commands_present(self):
        self.assertIn("CALL mysql.rds_set_external_master_gtid(", self.content)
        self.assertIn("CALL mysql.rds_start_replication;", self.content)

    def test_ami_sharing_cli_command_present(self):
        self.assertIn("aws ec2 modify-image-attribute", self.content)
        self.assertIn("--launch-permission", self.content)

    def test_section_three_subsections_present_and_ordered(self):
        subheadings = [
            "### A. Network & Security Discovery",
            "### B. Compute & ASG Discovery",
            "### C. Load Balancer & WAF Discovery",
            "### D. Database & Cache Discovery",
        ]
        for heading in subheadings:
            self.assertIn(heading, self.content)
        indices = [self.content.index(h) for h in subheadings]
        self.assertEqual(indices, sorted(indices))

    def test_discovery_commands_target_ap_southeast_5_region(self):
        section_match = re.search(
            r"## 3\. AWS CLI Infrastructure Discovery Commands\n(.*?)(?=\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section_text = section_match.group(1)
        # Every discovery command block should target the sovereign region.
        self.assertGreaterEqual(section_text.count("--region ap-southeast-5"), 5)

    def test_section_four_subsections_present_and_ordered(self):
        subheadings = [
            "### A. Pilot Light (Sized-to-Zero Compute)",
            "### B. Warm Standby (Scaled-down Compute)",
            "### C. Active/Active (Read-Local, Write-Global)",
        ]
        for heading in subheadings:
            self.assertIn(heading, self.content)
        indices = [self.content.index(h) for h in subheadings]
        self.assertEqual(indices, sorted(indices))

    def test_each_dr_strategy_subsection_has_database_compute_and_failover(self):
        strategy_blocks = re.split(
            r"### [ABC]\. (?:Pilot Light|Warm Standby|Active/Active).+\n",
            self.content,
        )[1:4]
        self.assertEqual(len(strategy_blocks), 3)
        for block in strategy_blocks:
            self.assertIn("**Database Strategy:**", block)
            self.assertIn("**Compute Strategy:**", block)
            self.assertIn("**Failover Protocol:**", block)
            self.assertIn("**RTO:**", block)
            self.assertIn("**RPO:**", block)

    def test_pricing_calculator_link_present(self):
        self.assertIn("[AWS Pricing Calculator](https://calculator.aws)", self.content)

    def test_usd_myr_conversion_rate_stated(self):
        self.assertIn("1 USD = 4.50 MYR", self.content)

    def test_pricing_tiers_present_and_ordered(self):
        tier_headings = [
            "### Tier 1: Baseline Cost-Optimized Plan",
            "### Tier 2: High-Performance Enterprise Plan",
        ]
        for heading in tier_headings:
            self.assertIn(heading, self.content)
        indices = [self.content.index(h) for h in tier_headings]
        self.assertEqual(indices, sorted(indices))

    def test_pricing_tables_have_expected_header_columns(self):
        expected_header = (
            "| AWS Service | Configuration Parameter | Value to Input | "
            "Monthly Cost (USD) |"
        )
        self.assertEqual(self.content.count(expected_header), 2)

    def test_tier_one_total_cost_summary_present(self):
        self.assertIn(
            "*Baseline Standby Total Cost: **~$85.00 USD / month** "
            "(RM 382.50 MYR) when configured as a Pilot Light strategy.*",
            self.content,
        )

    def test_tier_two_total_cost_summary_present(self):
        self.assertIn(
            "*High-Performance Standby Total Cost: **~$321.98 USD / month** "
            "(RM 1,448.91 MYR) when configured as a running Warm Standby "
            "strategy.*",
            self.content,
        )

    def test_implementation_summary_is_a_five_item_numbered_list(self):
        section_match = re.search(
            r"## 6\. Implementation Summary\n.*?\n(1\..*?)(?=\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        numbers = re.findall(r"^(\d+)\.\s+", section_match.group(1), re.MULTILINE)
        self.assertEqual([int(n) for n in numbers], [1, 2, 3, 4, 5])


class DrOptionTwoMalaysiaPricingTableStructureTestCase(unittest.TestCase):
    """Regression tests validating the internal structure of the two
    'AWS Pricing Calculator Parameters' markdown tables."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(DR_OPT_TWO_MD_PATH)

    def _rows_for_tier(self, tier_heading, next_heading):
        section_match = re.search(
            re.escape(tier_heading) + r"\n(.*?)(?=" + re.escape(next_heading) + r"|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match, f"Section '{tier_heading}' not found")
        section_text = section_match.group(1)
        return [
            line
            for line in section_text.splitlines()
            if line.strip().startswith("|") and not line.strip().startswith("| :---")
        ]

    def test_tier_one_table_rows_have_four_pipe_delimited_columns(self):
        rows = self._rows_for_tier(
            "### Tier 1: Baseline Cost-Optimized Plan (Estimate: $462.09 USD / month, ~RM 2,079.41 MYR)",
            "### Tier 2: High-Performance Enterprise Plan",
        )
        data_rows = [r for r in rows if "AWS Service" not in r]
        self.assertGreater(len(data_rows), 0)
        for row in data_rows:
            columns = [c.strip() for c in row.strip().strip("|").split("|")]
            self.assertEqual(len(columns), 4, f"Malformed row (expected 4 cols): {row}")

    def test_tier_two_table_rows_have_four_pipe_delimited_columns(self):
        rows = self._rows_for_tier(
            "### Tier 2: High-Performance Enterprise Plan (Estimate: $3,115.96 USD / month, ~RM 14,021.82 MYR)",
            "## 6. Implementation Summary",
        )
        data_rows = [r for r in rows if "AWS Service" not in r]
        self.assertGreater(len(data_rows), 0)
        for row in data_rows:
            columns = [c.strip() for c in row.strip().strip("|").split("|")]
            self.assertEqual(len(columns), 4, f"Malformed row (expected 4 cols): {row}")

    def test_tier_two_rds_instance_class_is_larger_than_tier_one(self):
        """Sanity/regression check that Tier 2 (enterprise) uses a larger
        RDS instance class than Tier 1 (baseline), reflecting the
        cost-scaling narrative of the document."""
        tier1_idx = self.content.index("`db.t4g.micro`")
        tier2_idx = self.content.index("`db.t4g.medium`")
        self.assertLess(tier1_idx, tier2_idx)


class SitemapArtifactsDrOptionTwoTestCase(unittest.TestCase):
    """Tests that the DR Option Two Malaysia page URL is correctly present
    in the checked-in sitemap.txt / sitemap.xml artifacts (both in docs/
    and at the repository root), and that regenerating the sitemaps via
    scripts/generate_sitemaps.py reproduces the same entries."""

    def test_gh_url_present_in_docs_sitemap_txt(self):
        content = _read(DOCS_SITEMAP_TXT_PATH)
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        self.assertIn(EXPECTED_GH_URL, lines)

    def test_gb_url_present_in_docs_sitemap_txt(self):
        content = _read(DOCS_SITEMAP_TXT_PATH)
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        self.assertIn(EXPECTED_GB_URL, lines)

    def test_gh_url_present_in_root_sitemap_txt(self):
        content = _read(ROOT_SITEMAP_TXT_PATH)
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        self.assertIn(EXPECTED_GH_URL, lines)

    def test_gb_url_present_in_root_sitemap_txt(self):
        content = _read(ROOT_SITEMAP_TXT_PATH)
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        self.assertIn(EXPECTED_GB_URL, lines)

    def test_url_present_after_dr_options_evaluation_url_in_root_sitemap_txt(self):
        content = _read(ROOT_SITEMAP_TXT_PATH)
        dr_eval_idx = content.index(
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
            "executive/dr-options-evaluation.html"
        )
        dr_opt_two_idx = content.index(EXPECTED_GH_URL)
        self.assertLess(dr_eval_idx, dr_opt_two_idx)

    def test_url_present_before_comparison_url_in_root_sitemap_txt(self):
        content = _read(ROOT_SITEMAP_TXT_PATH)
        dr_opt_two_idx = content.index(EXPECTED_GH_URL)
        comparison_idx = content.index(
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
            "engineering/aws-vs-onprem-comparison.html"
        )
        self.assertLess(dr_opt_two_idx, comparison_idx)

    def test_url_node_present_in_docs_sitemap_xml_with_expected_metadata(self):
        tree = ET.parse(DOCS_SITEMAP_XML_PATH)
        root = tree.getroot()
        urls = root.findall(f"{SITEMAP_NS}url")
        matching = [
            u for u in urls if u.find(f"{SITEMAP_NS}loc").text == EXPECTED_GH_URL
        ]
        self.assertEqual(len(matching), 1, "Expected exactly one matching <url> node")
        node = matching[0]
        self.assertEqual(node.find(f"{SITEMAP_NS}changefreq").text, "weekly")
        priority = float(node.find(f"{SITEMAP_NS}priority").text)
        self.assertEqual(priority, 0.6)

    def test_url_appears_exactly_once_in_root_sitemap_xml(self):
        tree = ET.parse(ROOT_SITEMAP_XML_PATH)
        root = tree.getroot()
        locs = [
            loc.text for loc in root.findall(f"{SITEMAP_NS}url/{SITEMAP_NS}loc")
        ]
        self.assertEqual(locs.count(EXPECTED_GH_URL), 1)

    def test_docs_and_root_sitemap_txt_are_identical(self):
        """docs/sitemap.txt and the root sitemap.txt are expected to be
        kept in sync (they are written together by
        generate_sitemaps.main())."""
        self.assertEqual(_read(DOCS_SITEMAP_TXT_PATH), _read(ROOT_SITEMAP_TXT_PATH))

    def test_docs_and_root_sitemap_xml_are_identical(self):
        self.assertEqual(_read(DOCS_SITEMAP_XML_PATH), _read(ROOT_SITEMAP_XML_PATH))

    def test_regenerating_sitemaps_reproduces_the_dr_option_two_urls(self):
        """Integration/regression test: regenerate sitemap.txt and
        sitemap.xml from the current docs/ tree and confirm the DR Option
        Two Malaysia page is (re)discovered by the crawler that walks
        docs/executive/.

        generate_sitemaps.main() writes directly to the on-disk sitemap
        files, and scripts/generate_sitemaps.py crawls docs/ via os.walk()
        without sorting, so the regenerated line ordering is not
        guaranteed to match the checked-in files. The original file
        contents are snapshotted and restored afterwards so this test
        cannot pollute the position-based assertions in the other tests
        of this class regardless of unittest's alphabetical execution
        order."""
        SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
        if SCRIPTS_DIR not in sys.path:
            sys.path.insert(0, SCRIPTS_DIR)
        import generate_sitemaps

        snapshot_paths = [
            DOCS_SITEMAP_TXT_PATH,
            ROOT_SITEMAP_TXT_PATH,
            DOCS_SITEMAP_XML_PATH,
            ROOT_SITEMAP_XML_PATH,
        ]
        original_contents = {path: _read(path) for path in snapshot_paths}
        try:
            generate_sitemaps.main()

            regenerated_txt = _read(ROOT_SITEMAP_TXT_PATH)
            regenerated_txt_lines = [
                line.strip() for line in regenerated_txt.splitlines() if line.strip()
            ]
            self.assertIn(EXPECTED_GH_URL, regenerated_txt_lines)
            self.assertIn(EXPECTED_GB_URL, regenerated_txt_lines)

            regenerated_xml = ET.parse(ROOT_SITEMAP_XML_PATH).getroot()
            regenerated_locs = [
                loc.text for loc in regenerated_xml.findall(f"{SITEMAP_NS}url/{SITEMAP_NS}loc")
            ]
            self.assertIn(EXPECTED_GH_URL, regenerated_locs)
        finally:
            for path, content in original_contents.items():
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)


if __name__ == "__main__":
    unittest.main()
