#!/usr/bin/env python3
"""Unit tests for the "AWS Services vs. On-Premises Open-Source Comparison
Guide" documentation added in this PR.

This PR introduces a new documentation page
(``docs/engineering/aws-vs-onprem-comparison.md``) and wires it up from
several other files:

* ``docs/index.md``                     -- adds a bullet link pointing at
  ``engineering/aws-vs-onprem-comparison.html`` under the "Deployment &
  CI/CD" section.
* ``docs/sitemap.txt`` / ``sitemap.txt`` -- adds the GitHub Pages and
  GitBook URLs for the new page.
* ``docs/sitemap.xml`` / ``sitemap.xml`` -- adds a ``<url>`` entry for the
  new page.

These files are treated as plain text (rather than parsed with a YAML/HTML
library) to stay dependency free, following the pattern already used by
``tests/test_dr_options_evaluation_docs.py`` and
``tests/test_production_costing_docs.py``. The tests pin down the exact
cross-references between the changed files, validate the OKF front matter of
the new markdown document, and validate the structural/tabular content of
the new document itself.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_aws_vs_onprem_comparison_docs
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

import prepare_docs  # noqa: E402  (import after sys.path manipulation)
import generate_sitemaps  # noqa: E402

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
COMPARISON_DOC_PATH = os.path.join(
    REPO_ROOT, "docs", "engineering", "aws-vs-onprem-comparison.md"
)

DOCS_SITEMAP_TXT_PATH = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_TXT_PATH = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_XML_PATH = os.path.join(REPO_ROOT, "docs", "sitemap.xml")
ROOT_SITEMAP_XML_PATH = os.path.join(REPO_ROOT, "sitemap.xml")

EXPECTED_GH_URL = (
    "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
    "engineering/aws-vs-onprem-comparison.html"
)
EXPECTED_GB_URL = (
    "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/"
    "docs/engineering/aws-vs-onprem-comparison"
)

SITEMAP_XML_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class IndexMdAwsVsOnpremLinkTestCase(unittest.TestCase):
    """Tests for the new link added to docs/index.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)

    def test_index_file_exists(self):
        self.assertTrue(os.path.isfile(INDEX_PATH))

    def test_comparison_link_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\*\*\[AWS Services vs\. On-Premises Open-Source Comparison "
                r"Guide\]\(engineering/aws-vs-onprem-comparison\.html\):\*\*"
                r"\s*A comprehensive 12-layer mapping comparing cloud-native "
                r"services with self-hosted, on-premises open-source "
                r"solutions\."
            ),
        )

    def test_link_appears_after_github_detach_fork_link(self):
        detach_fork_idx = self.content.index(
            "[GitHub Repository Fork Detachment Guide]"
            "(engineering/github-detach-fork.html)"
        )
        comparison_idx = self.content.index(
            "[AWS Services vs. On-Premises Open-Source Comparison Guide]"
            "(engineering/aws-vs-onprem-comparison.html)"
        )
        self.assertLess(detach_fork_idx, comparison_idx)

    def test_link_appears_in_deployment_cicd_section(self):
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n### |\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[AWS Services vs. On-Premises Open-Source Comparison Guide]"
            "(engineering/aws-vs-onprem-comparison.html)",
            section_match.group(1),
        )

    def test_link_uses_relative_html_url_not_markdown_extension(self):
        self.assertIn(
            "(engineering/aws-vs-onprem-comparison.html)", self.content
        )
        self.assertNotIn(
            "(engineering/aws-vs-onprem-comparison.md)", self.content
        )

    def test_link_target_file_exists(self):
        self.assertTrue(os.path.isfile(COMPARISON_DOC_PATH))

    def test_link_appears_exactly_once(self):
        self.assertEqual(
            self.content.count(
                "[AWS Services vs. On-Premises Open-Source Comparison Guide]"
            ),
            1,
        )

    def test_deployment_cicd_section_bullets_are_not_numbered(self):
        """Regression: unlike the numbered "Executive Strategic Blueprints"
        and "Engineering & DevOps Implementation Guides" sections, the
        "Deployment & CI/CD" section uses plain markdown bullets (``-``), so
        the newly appended entry must follow that same convention rather
        than introducing a numbered list item."""
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n### |\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section_text = section_match.group(1)
        bullet_lines = [
            line for line in section_text.splitlines() if line.strip()
        ]
        for line in bullet_lines:
            self.assertTrue(
                line.strip().startswith("- **["),
                f"Expected plain bullet formatting, got: {line}",
            )


class AwsVsOnpremComparisonFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of
    docs/engineering/aws-vs-onprem-comparison.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(COMPARISON_DOC_PATH)
        stripped = cls.content.lstrip()
        parts = stripped.split("---", 2)
        # parts[0] is empty (before first ---), parts[1] is the front matter body.
        cls.front_matter_text = parts[1]
        cls.body_text = parts[2]
        cls.front_matter = prepare_docs.parse_yaml_front_matter(
            cls.front_matter_text
        )

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(COMPARISON_DOC_PATH))

    def test_starts_with_front_matter_delimiter(self):
        self.assertTrue(self.content.startswith("---\n"))

    def test_required_okf_fields_present(self):
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_okf_version_is_expected_value(self):
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_layout_is_default(self):
        self.assertEqual(self.front_matter["layout"], "default")

    def test_title_field_value(self):
        self.assertEqual(
            self.front_matter["title"],
            "AWS Services vs. On-Premises Open-Source Comparison Guide",
        )

    def test_type_matches_prepare_docs_inference(self):
        """docs/*.md files that aren't index.md or under docs/modules are
        inferred as 'Technical Reference Guide' by prepare_docs.py; the
        front matter of the new doc should match that convention."""
        inferred_type = prepare_docs.infer_okf_type(
            "docs/engineering/aws-vs-onprem-comparison.md"
        )
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_is_a_list_of_strings(self):
        topics = self.front_matter["topics"]
        self.assertIsInstance(topics, list)
        self.assertTrue(all(isinstance(t, str) for t in topics))

    def test_topics_have_expected_values(self):
        self.assertEqual(
            self.front_matter["topics"],
            ["aws", "3-tier", "on-premises", "comparison"],
        )

    def test_topics_have_no_duplicates(self):
        topics = self.front_matter["topics"]
        self.assertEqual(len(topics), len(set(topics)))

    def test_prepare_docs_preserves_manually_authored_topics(self):
        """Since the front matter already declares non-empty topics,
        prepare_docs.infer_okf_topics must treat them as authoritative and
        return them unchanged (it should not overwrite curated topics with
        its generic path-based inference)."""
        existing_topics = self.front_matter["topics"]
        result = prepare_docs.infer_okf_topics(
            "docs/engineering/aws-vs-onprem-comparison.md", existing_topics
        )
        self.assertEqual(result, existing_topics)

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        heading_text = heading_match.group(1).strip()
        self.assertEqual(heading_text, self.front_matter["title"])

    def test_timestamp_field_is_iso_formatted_with_timezone_offset(self):
        self.assertRegex(
            str(self.front_matter["timestamp"]),
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$",
        )


class AwsVsOnpremComparisonContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of
    docs/engineering/aws-vs-onprem-comparison.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(COMPARISON_DOC_PATH)

    def test_contains_devops_execution_marker(self):
        self.assertIn("**[DEVOPS EXECUTION]**", self.content)

    def test_contains_strategic_financial_marker(self):
        self.assertIn("**[STRATEGIC FINANCIAL]**", self.content)

    def test_contains_notice_and_disclaimer_heading(self):
        self.assertIn("## Notice & Disclaimer", self.content)

    def test_disclaimer_mentions_assumptions_and_training_purpose(self):
        self.assertIn("based entirely on assumptions", self.content)
        self.assertIn(
            "training, educational, and planning proposal purposes",
            self.content,
        )

    def test_contains_12_layer_stack_heading(self):
        self.assertIn(
            "## The 12-Layer Enterprise Infrastructure Stack", self.content
        )

    def test_contains_comprehensive_mapping_heading(self):
        self.assertIn(
            "## Comprehensive 12-Layer Architectural Mapping", self.content
        )

    def test_contains_strategic_summary_matrix_heading(self):
        self.assertIn("## Strategic Summary Matrix", self.content)

    def test_top_level_sections_appear_in_ascending_order(self):
        indices = [
            self.content.index("## Notice & Disclaimer"),
            self.content.index("## The 12-Layer Enterprise Infrastructure Stack"),
            self.content.index("## Comprehensive 12-Layer Architectural Mapping"),
            self.content.index("## Strategic Summary Matrix"),
        ]
        self.assertEqual(indices, sorted(indices))

    def test_ascii_diagram_lists_all_12_layers_in_order(self):
        layer_labels = [
            "1. Frontend (Web & Mobile UI Assets)",
            "2. APIs & Backend Logic (Business Engines)",
            "3. Database & Storage (Relational, Objects & Vectors)",
            "4. Auth & Permissions (Identity Providers)",
            "5. Hosting & Deployment (Orchestration & Runtimes)",
            "6. Cloud & Compute (Virtualisation & Hardware)",
            "7. CI/CD & Version Control (Delivery Pipelines)",
            "8. Security & RLS (Firewalls, IDS & Data Isolation)",
            "9. Rate Limiting (Traffic Protection & Throttling)",
            "10. Caching & CDN (Low-Latency Acceleration)",
            "11. Load Balancing & Scaling (High Availability)",
            "12. Error Tracking & Logs (Observability & Telemetry)",
        ]
        for label in layer_labels:
            self.assertIn(label, self.content)
        indices = [self.content.index(label) for label in layer_labels]
        self.assertEqual(indices, sorted(indices))

    def test_all_12_layer_headings_present_and_ordered(self):
        layer_headings = [
            "### Layer 1: Frontend",
            "### Layer 2: APIs & Backend Logic",
            "### Layer 3: Database & Storage",
            "### Layer 4: Auth & Permissions",
            "### Layer 5: Hosting & Deployment",
            "### Layer 6: Cloud & Compute",
            "### Layer 7: CI/CD & Version Control",
            "### Layer 8: Security & RLS",
            "### Layer 9: Rate Limiting",
            "### Layer 10: Caching & CDN",
            "### Layer 11: Load Balancing & Scaling",
            "### Layer 12: Error Tracking & Logs",
        ]
        for heading in layer_headings:
            self.assertIn(heading, self.content)
        indices = [self.content.index(h) for h in layer_headings]
        self.assertEqual(indices, sorted(indices))

    def test_exactly_12_layer_headings_exist(self):
        """Regression: guards against accidental duplication or removal of
        a layer heading (e.g. a copy/paste error that repeats a layer)."""
        matches = re.findall(r"^### Layer \d+: .+$", self.content, re.MULTILINE)
        self.assertEqual(len(matches), 12)

    def test_each_layer_section_has_aws_and_onprem_options(self):
        """Every '### Layer N: ...' section must contain both an AWS
        Cloud-Native Option block and an On-Premises Open-Source Option
        block, each with Services/Solutions, Architectural Behaviour, and
        Advantages bullets."""
        layer_blocks = re.split(r"### Layer \d+: .+\n", self.content)[1:]
        self.assertEqual(len(layer_blocks), 12)
        for block in layer_blocks:
            self.assertIn("**AWS Cloud-Native Option:**", block)
            self.assertIn("**On-Premises / Onsite Open-Source Option:**", block)
            self.assertIn("**Architectural Behaviour:**", block)
            self.assertIn("**Advantages:**", block)

    def test_aws_option_uses_services_label_not_solutions(self):
        layer_blocks = re.split(r"### Layer \d+: .+\n", self.content)[1:]
        for block in layer_blocks:
            aws_section = block.split("**On-Premises")[0]
            self.assertIn("**Services:**", aws_section)

    def test_onprem_option_uses_solutions_label_not_services(self):
        layer_blocks = re.split(r"### Layer \d+: .+\n", self.content)[1:]
        for block in layer_blocks:
            onprem_section = block.split("**On-Premises")[1]
            self.assertIn("**Solutions:**", onprem_section)

    def test_footer_contains_copyright_and_license(self):
        self.assertIn(
            "Copyright \u00a9 2005 - 2026 Harisfazillah Jamel", self.content
        )
        self.assertIn("GNU General Public License v3.0", self.content)

    def test_footer_contains_linuxmalaysia_link(self):
        self.assertIn("[linuxmalaysia.com](https://linuxmalaysia.com/)", self.content)


class AwsVsOnpremComparisonSummaryMatrixTestCase(unittest.TestCase):
    """Regression tests validating the internal structure of the
    'Strategic Summary Matrix' markdown table."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(COMPARISON_DOC_PATH)
        section_match = re.search(
            r"## Strategic Summary Matrix\n(.*?)(?=\n---|\Z)",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None, "Strategic Summary Matrix section not found"
        cls.section_text = section_match.group(1)
        # Extract the individual table data rows (skip header and separator rows).
        cls.rows = [
            line
            for line in cls.section_text.splitlines()
            if line.strip().startswith("| **")
        ]

    def test_table_header_lists_expected_columns(self):
        self.assertIn(
            "| Layer | AWS Cloud-Native Managed Stack | "
            "On-Premises Open-Source Solution | Key Decision Driver |",
            self.section_text,
        )

    def test_table_has_exactly_twelve_data_rows(self):
        self.assertEqual(len(self.rows), 12)

    def test_table_rows_reference_layers_one_through_twelve_in_order(self):
        for expected_num, row in enumerate(self.rows, start=1):
            self.assertIn(f"**{expected_num}.", row)

    def test_each_row_has_four_pipe_delimited_columns(self):
        for row in self.rows:
            # A well-formed markdown table row has N+1 pipe characters for
            # N columns (leading and trailing pipes included).
            columns = [c.strip() for c in row.strip().strip("|").split("|")]
            self.assertEqual(len(columns), 4, f"Malformed row (expected 4 cols): {row}")

    def test_first_row_matches_frontend_layer(self):
        self.assertIn("**1. Frontend**", self.rows[0])
        self.assertIn("S3 Website + CloudFront CDN", self.rows[0])

    def test_last_row_matches_error_tracking_layer(self):
        self.assertIn("**12. Error Tracking**", self.rows[-1])
        self.assertIn("CloudWatch Logs + AWS X-Ray", self.rows[-1])


class SitemapArtifactsAwsVsOnpremTestCase(unittest.TestCase):
    """Tests that the AWS vs. On-Premises comparison page URL is correctly
    present in the checked-in sitemap.txt / sitemap.xml artifacts (both in
    docs/ and at the repository root), and that regenerating the sitemaps
    via scripts/generate_sitemaps.py reproduces the same entries."""

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

    def test_gh_url_appears_directly_after_dr_options_evaluation_url_in_root_sitemap_txt(self):
        """Regression: pins the exact insertion point documented in the PR
        diff -- the new page is wired in right after
        'executive/dr-options-evaluation.html' and right before
        'engineering/developer-design-mapping.html'."""
        content = _read(ROOT_SITEMAP_TXT_PATH)
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        dr_eval_url = (
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
            "executive/dr-options-evaluation.html"
        )
        dev_design_url = (
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
            "engineering/developer-design-mapping.html"
        )
        dr_eval_idx = lines.index(dr_eval_url)
        comparison_idx = lines.index(EXPECTED_GH_URL)
        dev_design_idx = lines.index(dev_design_url)
        self.assertEqual(comparison_idx, dr_eval_idx + 1)
        self.assertEqual(dev_design_idx, comparison_idx + 1)

    def test_gb_url_appears_directly_after_dr_options_evaluation_url_in_root_sitemap_txt(self):
        content = _read(ROOT_SITEMAP_TXT_PATH)
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        dr_eval_gb_url = (
            "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/"
            "docs/executive/dr-options-evaluation"
        )
        dev_design_gb_url = (
            "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/"
            "docs/engineering/developer-design-mapping"
        )
        dr_eval_idx = lines.index(dr_eval_gb_url)
        comparison_idx = lines.index(EXPECTED_GB_URL)
        dev_design_idx = lines.index(dev_design_gb_url)
        self.assertEqual(comparison_idx, dr_eval_idx + 1)
        self.assertEqual(dev_design_idx, comparison_idx + 1)

    def test_url_node_present_in_docs_sitemap_xml_with_expected_metadata(self):
        tree = ET.parse(DOCS_SITEMAP_XML_PATH)
        root = tree.getroot()
        urls = root.findall(f"{SITEMAP_XML_NS}url")
        matching = [
            u for u in urls if u.find(f"{SITEMAP_XML_NS}loc").text == EXPECTED_GH_URL
        ]
        self.assertEqual(len(matching), 1, "Expected exactly one matching <url> node")
        node = matching[0]
        self.assertEqual(node.find(f"{SITEMAP_XML_NS}changefreq").text, "weekly")
        priority = float(node.find(f"{SITEMAP_XML_NS}priority").text)
        self.assertEqual(priority, 0.6)
        lastmod = node.find(f"{SITEMAP_XML_NS}lastmod").text
        self.assertRegex(lastmod, r"^\d{4}-\d{2}-\d{2}$")

    def test_url_node_present_in_root_sitemap_xml(self):
        tree = ET.parse(ROOT_SITEMAP_XML_PATH)
        root = tree.getroot()
        locs = [
            loc.text
            for loc in root.findall(f"{SITEMAP_XML_NS}url/{SITEMAP_XML_NS}loc")
        ]
        self.assertIn(EXPECTED_GH_URL, locs)

    def test_url_appears_exactly_once_in_root_sitemap_xml(self):
        tree = ET.parse(ROOT_SITEMAP_XML_PATH)
        root = tree.getroot()
        locs = [
            loc.text
            for loc in root.findall(f"{SITEMAP_XML_NS}url/{SITEMAP_XML_NS}loc")
        ]
        self.assertEqual(locs.count(EXPECTED_GH_URL), 1)

    def test_docs_and_root_sitemap_xml_are_identical(self):
        """docs/sitemap.xml and the root sitemap.xml are expected to be kept
        in sync (they are written together by generate_sitemaps.main())."""
        self.assertEqual(_read(DOCS_SITEMAP_XML_PATH), _read(ROOT_SITEMAP_XML_PATH))

    def test_docs_and_root_sitemap_txt_are_identical(self):
        self.assertEqual(_read(DOCS_SITEMAP_TXT_PATH), _read(ROOT_SITEMAP_TXT_PATH))

    def test_regenerating_sitemaps_reproduces_the_comparison_page_urls(self):
        """Integration/regression test: regenerate sitemap.txt and
        sitemap.xml from the current docs/ tree (mirroring the pattern used
        in tests/test_sitemaps.py) and confirm the AWS vs. On-Premises
        comparison page is (re)discovered by the crawler that walks
        docs/engineering/."""
        generate_sitemaps.main()

        regenerated_txt = _read(ROOT_SITEMAP_TXT_PATH)
        regenerated_txt_lines = [
            line.strip() for line in regenerated_txt.splitlines() if line.strip()
        ]
        self.assertIn(EXPECTED_GH_URL, regenerated_txt_lines)
        self.assertIn(EXPECTED_GB_URL, regenerated_txt_lines)

        regenerated_docs_txt = _read(DOCS_SITEMAP_TXT_PATH)
        regenerated_docs_txt_lines = [
            line.strip() for line in regenerated_docs_txt.splitlines() if line.strip()
        ]
        self.assertIn(EXPECTED_GH_URL, regenerated_docs_txt_lines)
        self.assertIn(EXPECTED_GB_URL, regenerated_docs_txt_lines)

        regenerated_xml = ET.parse(ROOT_SITEMAP_XML_PATH).getroot()
        regenerated_locs = [
            loc.text
            for loc in regenerated_xml.findall(f"{SITEMAP_XML_NS}url/{SITEMAP_XML_NS}loc")
        ]
        self.assertIn(EXPECTED_GH_URL, regenerated_locs)


if __name__ == "__main__":
    unittest.main()