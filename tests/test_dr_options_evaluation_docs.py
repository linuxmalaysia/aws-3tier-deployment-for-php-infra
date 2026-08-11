#!/usr/bin/env python3
"""Unit tests for the "Disaster Recovery Options & Regional Strategy
Evaluation" documentation added in this PR.

This PR introduces a new documentation page
(``docs/executive/dr-options-evaluation.md``) and wires it up from several
other files:

* ``docs/_config.yml``   -- adds a navbar entry pointing at
  ``/executive/dr-options-evaluation.html``.
* ``docs/index.md``      -- adds a numbered bullet link pointing at
  ``executive/dr-options-evaluation.html``.
* ``llms.txt``            -- adds an AI-agent index entry pointing at
  ``docs/executive/dr-options-evaluation.md``.
* ``docs/sitemap.txt`` / ``sitemap.txt``   -- adds the GitHub Pages and
  GitBook URLs for the new page.
* ``docs/sitemap.xml`` / ``sitemap.xml``   -- adds a ``<url>`` entry for the
  new page.

These files are treated as plain text (rather than parsed with a YAML/HTML
library) to stay dependency free, following the pattern already used by
``tests/test_production_costing_docs.py``. The tests pin down the exact
cross-references between the changed files, validate the OKF front matter of
the new markdown document, and validate the structural/tabular content of
the new document itself.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_dr_options_evaluation_docs
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

CONFIG_PATH = os.path.join(REPO_ROOT, "docs", "_config.yml")
INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
DR_EVAL_PATH = os.path.join(REPO_ROOT, "docs", "executive", "dr-options-evaluation.md")

DOCS_SITEMAP_TXT_PATH = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_TXT_PATH = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_XML_PATH = os.path.join(REPO_ROOT, "docs", "sitemap.xml")
ROOT_SITEMAP_XML_PATH = os.path.join(REPO_ROOT, "sitemap.xml")

EXPECTED_GH_URL = (
    "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
    "executive/dr-options-evaluation.html"
)
EXPECTED_GB_URL = (
    "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/"
    "docs/executive/dr-options-evaluation"
)

SITEMAP_XML_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class ConfigYamlNavbarTestCase(unittest.TestCase):
    """Tests for the new navbar entry in docs/_config.yml."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(CONFIG_PATH)

    def test_config_file_exists(self):
        self.assertTrue(os.path.isfile(CONFIG_PATH))

    def test_dr_evaluation_navbar_entry_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r'-\s*title:\s*"DR Evaluation"\s*\n\s*url:\s*"/executive/dr-options-evaluation\.html"'
            ),
        )

    def test_navbar_entry_placed_directly_after_disaster_recovery_entry(self):
        """Regression: the new entry should be inserted right after the
        existing 'Disaster Recovery' entry, not appended somewhere
        unrelated."""
        match = re.search(
            r'-\s*title:\s*"Disaster Recovery"\s*\n\s*url:\s*"/executive/dr-options\.html"\s*\n'
            r'\s*-\s*title:\s*"DR Evaluation"\s*\n\s*url:\s*"/executive/dr-options-evaluation\.html"',
            self.content,
        )
        self.assertIsNotNone(
            match, "Expected 'DR Evaluation' entry directly after 'Disaster Recovery'"
        )

    def test_navbar_entry_placed_before_rds_vs_percona_entry(self):
        dr_eval_idx = self.content.index('title: "DR Evaluation"')
        rds_idx = self.content.index('title: "RDS vs Percona"')
        self.assertLess(dr_eval_idx, rds_idx)

    def test_navbar_title_appears_exactly_once(self):
        self.assertEqual(self.content.count('"DR Evaluation"'), 1)

    def test_navbar_url_appears_exactly_once(self):
        self.assertEqual(
            self.content.count("/executive/dr-options-evaluation.html"), 1
        )

    def test_navbar_url_points_to_existing_doc_file(self):
        """The navbar entry URL should resolve to an actual markdown source
        file that Jekyll can build into dr-options-evaluation.html."""
        self.assertTrue(os.path.isfile(DR_EVAL_PATH))

    def test_existing_dr_options_entry_untouched(self):
        """Ensure the pre-existing 'Disaster Recovery' navbar entry was not
        accidentally clobbered by the new addition."""
        self.assertIn('title: "Disaster Recovery"', self.content)
        self.assertIn('url: "/executive/dr-options.html"', self.content)


class IndexMdDrOptionsEvaluationLinkTestCase(unittest.TestCase):
    """Tests for the new link added to docs/index.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)

    def test_index_file_exists(self):
        self.assertTrue(os.path.isfile(INDEX_PATH))

    def test_dr_evaluation_link_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\*\*\[AWS Disaster Recovery \(DR\) Strategy & Options Evaluation\]"
                r"\(executive/dr-options-evaluation\.html\):\*\*"
                r"\s*Strategic evaluation of 3\+1 disaster recovery options"
            ),
        )

    def test_link_appears_after_dr_options_link(self):
        dr_options_idx = self.content.index(
            "[Disaster Recovery Options & National Sovereignty Guide](executive/dr-options.html)"
        )
        dr_eval_idx = self.content.index(
            "[AWS Disaster Recovery (DR) Strategy & Options Evaluation]"
            "(executive/dr-options-evaluation.html)"
        )
        self.assertLess(dr_options_idx, dr_eval_idx)

    def test_link_appears_before_costing_estimate_link(self):
        dr_eval_idx = self.content.index(
            "[AWS Disaster Recovery (DR) Strategy & Options Evaluation]"
            "(executive/dr-options-evaluation.html)"
        )
        costing_idx = self.content.index("[Costing Estimate](executive/costing.html)")
        self.assertLess(dr_eval_idx, costing_idx)

    def test_link_appears_in_executive_blueprints_section(self):
        section_match = re.search(
            r"### Executive Strategic Blueprints\n(.*?)(?=\n### |\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[AWS Disaster Recovery (DR) Strategy & Options Evaluation]"
            "(executive/dr-options-evaluation.html)",
            section_match.group(1),
        )

    def test_link_uses_relative_html_url_not_markdown_extension(self):
        self.assertIn("(executive/dr-options-evaluation.html)", self.content)
        self.assertNotIn("(executive/dr-options-evaluation.md)", self.content)

    def test_link_target_file_exists(self):
        self.assertTrue(os.path.isfile(DR_EVAL_PATH))

    def test_link_appears_exactly_once(self):
        self.assertEqual(
            self.content.count(
                "[AWS Disaster Recovery (DR) Strategy & Options Evaluation]"
            ),
            1,
        )

    def test_executive_blueprints_list_is_renumbered_sequentially(self):
        """Regression: inserting the new item at position 3 should bump
        every subsequent numbered item (Costing Estimate becomes 4,
        Production Costing 5, Hybrid Cloud 6) rather than leaving gaps or
        duplicate numbers."""
        section_match = re.search(
            r"### Executive Strategic Blueprints\n(.*?)(?=\n### |\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section_text = section_match.group(1)
        numbers = [int(n) for n in re.findall(r"^(\d+)\.\s+\*\*\[", section_text, re.MULTILINE)]
        self.assertEqual(numbers, [1, 2, 3, 4, 5, 6])

    def test_costing_estimate_is_now_item_four(self):
        match = re.search(
            r"^4\.\s+\*\*\[Costing Estimate\]\(executive/costing\.html\)",
            self.content,
            re.MULTILINE,
        )
        self.assertIsNotNone(match)

    def test_hybrid_cloud_is_now_item_six(self):
        match = re.search(
            r"^6\.\s+\*\*\[Hybrid Cloud Integration Guide\]\(executive/hybrid-onprem\.html\)",
            self.content,
            re.MULTILINE,
        )
        self.assertIsNotNone(match)


class LlmsTxtDrOptionsEvaluationEntryTestCase(unittest.TestCase):
    """Tests for the new entry added to llms.txt."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LLMS_PATH)

    def test_llms_txt_file_exists(self):
        self.assertTrue(os.path.isfile(LLMS_PATH))

    def test_dr_evaluation_entry_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\[Disaster Recovery Options Evaluation\]"
                r"\(docs/executive/dr-options-evaluation\.md\)\s*:"
                r"\s*Strategic evaluation of the 3\+1 disaster recovery options"
            ),
        )

    def test_entry_under_strategic_blueprints_section_heading(self):
        section_match = re.search(
            r"## Core Strategic Blueprints \(Executive\)\n(.*?)(?=\n## |\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[Disaster Recovery Options Evaluation](docs/executive/dr-options-evaluation.md)",
            section_match.group(1),
        )

    def test_entry_appears_directly_after_dr_sovereignty_entry(self):
        dr_sov_idx = self.content.index(
            "[Disaster Recovery & Sovereignty](docs/executive/dr-options.md)"
        )
        dr_eval_idx = self.content.index(
            "[Disaster Recovery Options Evaluation](docs/executive/dr-options-evaluation.md)"
        )
        self.assertLess(dr_sov_idx, dr_eval_idx)
        # Nothing else should be sandwiched between the two entries.
        between = self.content[dr_sov_idx:dr_eval_idx]
        self.assertEqual(between.count("\n"), 1)
        self.assertNotIn("\n- [", between.strip("\n"))

    def test_entry_appears_before_hybrid_cloud_entry(self):
        dr_eval_idx = self.content.index(
            "[Disaster Recovery Options Evaluation](docs/executive/dr-options-evaluation.md)"
        )
        hybrid_idx = self.content.index(
            "[Hybrid Cloud Connectivity](docs/executive/hybrid-onprem.md)"
        )
        self.assertLess(dr_eval_idx, hybrid_idx)

    def test_entry_target_file_exists(self):
        self.assertTrue(os.path.isfile(DR_EVAL_PATH))

    def test_entry_follows_bullet_link_colon_description_format(self):
        match = re.search(
            r"^- \[Disaster Recovery Options Evaluation\]"
            r"\(docs/executive/dr-options-evaluation\.md\) : .+$",
            self.content,
            re.MULTILINE,
        )
        self.assertIsNotNone(
            match, "Entry does not follow the '- [Title](path) : description' format"
        )

    def test_entry_appears_exactly_once(self):
        self.assertEqual(
            self.content.count("[Disaster Recovery Options Evaluation]"), 1
        )


class CrossFileReferenceConsistencyTestCase(unittest.TestCase):
    """Verifies the slug used for dr-options-evaluation is consistent across
    docs/_config.yml, docs/index.md, and llms.txt."""

    @classmethod
    def setUpClass(cls):
        cls.config_content = _read(CONFIG_PATH)
        cls.index_content = _read(INDEX_PATH)
        cls.llms_content = _read(LLMS_PATH)

    def test_html_slug_consistent_between_navbar_and_index(self):
        self.assertIn("/executive/dr-options-evaluation.html", self.config_content)
        self.assertIn("(executive/dr-options-evaluation.html)", self.index_content)

    def test_markdown_path_consistent_between_llms_txt_and_filesystem(self):
        match = re.search(
            r"\[Disaster Recovery Options Evaluation\]\((docs/executive/dr-options-evaluation\.md)\)",
            self.llms_content,
        )
        self.assertIsNotNone(match)
        referenced_path = os.path.join(REPO_ROOT, match.group(1))
        self.assertTrue(os.path.isfile(referenced_path))
        self.assertEqual(os.path.normpath(referenced_path), DR_EVAL_PATH)

    def test_slug_does_not_collide_with_existing_dr_options_slug(self):
        """The new page's slug must be distinct from the pre-existing
        'dr-options' slug (i.e. not simply a substring collision that would
        route to the wrong page)."""
        self.assertNotEqual("dr-options", "dr-options-evaluation")
        self.assertIn("/executive/dr-options.html", self.config_content)
        self.assertIn("/executive/dr-options-evaluation.html", self.config_content)


class DrOptionsEvaluationMarkdownFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of
    docs/executive/dr-options-evaluation.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(DR_EVAL_PATH)
        stripped = cls.content.lstrip()
        parts = stripped.split("---", 2)
        # parts[0] is empty (before first ---), parts[1] is the front matter body.
        cls.front_matter_text = parts[1]
        cls.body_text = parts[2]
        cls.front_matter = prepare_docs.parse_yaml_front_matter(cls.front_matter_text)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(DR_EVAL_PATH))

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
            "Disaster Recovery Options & Regional Strategy Evaluation",
        )

    def test_type_matches_prepare_docs_inference(self):
        """docs/*.md files that aren't index.md or under docs/modules are
        inferred as 'Technical Reference Guide' by prepare_docs.py; the
        front matter of the new doc should match that convention."""
        inferred_type = prepare_docs.infer_okf_type(
            "docs/executive/dr-options-evaluation.md"
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
            ["aws", "3-tier", "disaster-recovery", "compliance"],
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
            "docs/executive/dr-options-evaluation.md", existing_topics
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


class DrOptionsEvaluationContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of
    docs/executive/dr-options-evaluation.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(DR_EVAL_PATH)

    def test_contains_strategic_financial_marker(self):
        self.assertIn("**[STRATEGIC FINANCIAL]**", self.content)

    def test_contains_core_concepts_heading(self):
        self.assertIn(
            "## 1. Core Disaster Recovery Concepts & AWS Whitepaper Alignment",
            self.content,
        )

    def test_contains_project_specific_options_heading(self):
        self.assertIn("## 2. Project-Specific DR Options Under Discussion", self.content)

    def test_contains_decision_matrix_heading(self):
        self.assertIn("## 3. Disaster Recovery Strategic Decision Matrix", self.content)

    def test_contains_recommendations_heading(self):
        self.assertIn(
            "## 4. Key Recommendations and Implementation Blueprint", self.content
        )

    def test_top_level_sections_appear_in_ascending_numeric_order(self):
        indices = [
            self.content.index("## 1. Core Disaster Recovery Concepts"),
            self.content.index("## 2. Project-Specific DR Options"),
            self.content.index("## 3. Disaster Recovery Strategic Decision Matrix"),
            self.content.index("## 4. Key Recommendations"),
        ]
        self.assertEqual(indices, sorted(indices))

    def test_contains_data_plane_vs_control_plane_subsection(self):
        self.assertIn("### Data Plane vs Control Plane Resilience", self.content)

    def test_contains_four_classic_strategies_subsection(self):
        self.assertIn("### The Four Classic Cloud DR Strategies", self.content)

    def test_contains_ascii_dr_strategy_diagram(self):
        self.assertIn("```text", self.content)
        self.assertIn("AWS Disaster Recovery Options", self.content)
        self.assertIn("Backup and Restore", self.content)
        self.assertIn("Pilot Light (Off-site Standby Core)", self.content)
        self.assertIn("Warm Standby (Scaled-down Active-Active)", self.content)
        self.assertIn("Multi-Site Active/Active", self.content)

    def test_four_option_subsections_present_and_ordered(self):
        option_headings = [
            "### Option 1: Region besides Malaysia and a Separate AWS Account",
            "### Option 2: Malaysia Region and a Separate AWS Account",
            "### Option 3: Malaysia Region and the Same AWS Account (Different VPC)",
            "### Option 4: Backup and Restore",
        ]
        for heading in option_headings:
            self.assertIn(heading, self.content)
        indices = [self.content.index(h) for h in option_headings]
        self.assertEqual(indices, sorted(indices))

    def test_each_option_has_dr_strategy_pros_and_cons(self):
        option_blocks = re.split(r"### Option \d: .+\n", self.content)[1:]
        self.assertEqual(len(option_blocks), 4)
        for block in option_blocks:
            self.assertIn("**DR Strategy:**", block)
            self.assertIn("- **Pros:**", block)
            self.assertIn("- **Cons:**", block)

    def test_pdpa_section_129_referenced(self):
        self.assertIn("PDPA Section 129", self.content)

    def test_ap_southeast_5_region_referenced(self):
        self.assertIn("`ap-southeast-5`", self.content)

    def test_ap_southeast_1_singapore_referenced_as_dr_region(self):
        self.assertIn("Singapore `ap-southeast-1`", self.content)

    def test_phased_roadmap_present_and_ordered(self):
        phases = [
            "1. **Phase 1 (Immediate - Active/Passive Backup & Restore):**",
            "2. **Phase 2 (Medium Term - In-Region Account Isolation):**",
            "3. **Phase 3 (Enterprise Target - Cross-Region Pilot Light):**",
        ]
        for phase in phases:
            self.assertIn(phase, self.content)
        indices = [self.content.index(p) for p in phases]
        self.assertEqual(indices, sorted(indices))


class DrOptionsEvaluationDecisionMatrixTestCase(unittest.TestCase):
    """Regression tests validating the internal structure and relative
    ordering of the '3. Disaster Recovery Strategic Decision Matrix'
    markdown table."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(DR_EVAL_PATH)
        section_match = re.search(
            r"## 3\. Disaster Recovery Strategic Decision Matrix\n(.*?)(?=\n---|\Z)",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None, "Decision matrix section not found"
        cls.section_text = section_match.group(1)
        # Extract the individual table data rows (skip header and separator rows).
        cls.rows = [
            line
            for line in cls.section_text.splitlines()
            if line.strip().startswith("| **Option")
        ]

    def test_table_header_lists_expected_columns(self):
        self.assertIn(
            "| DR Option Evaluated | Account Boundary | Regional Boundary | "
            "Network Isolation | Target RTO | Target RPO | Relative Cost Index | "
            "PDPA Compliance Basis |",
            self.section_text,
        )

    def test_table_has_exactly_four_data_rows(self):
        self.assertEqual(len(self.rows), 4)

    def test_table_rows_reference_options_one_through_four_in_order(self):
        for expected_num, row in enumerate(self.rows, start=1):
            self.assertIn(f"**Option {expected_num}:", row)

    def test_each_row_has_eight_pipe_delimited_columns(self):
        for row in self.rows:
            # A well-formed markdown table row has N+1 pipe characters for
            # N columns (leading and trailing pipes included).
            columns = [c.strip() for c in row.strip().strip("|").split("|")]
            self.assertEqual(len(columns), 8, f"Malformed row (expected 8 cols): {row}")

    def test_relative_cost_index_star_ratings_decrease_monotonically(self):
        """Option 1 (highest complexity/cost) should have the most filled
        stars, decreasing down to Option 4 (lowest cost)."""
        star_counts = [row.count("\u2605") for row in self.rows]
        self.assertEqual(star_counts, [4, 3, 2, 1])

    def test_relative_cost_index_labels_match_expected_order(self):
        expected_labels = ["(High)", "(Medium)", "(Low)", "(Minimal)"]
        for row, label in zip(self.rows, expected_labels):
            self.assertIn(label, row)

    def test_target_rto_values_present_for_all_rows(self):
        expected_rtos = ["< 15 Minutes", "< 30 Minutes", "< 60 Minutes", "2 - 4 Hours"]
        for row, rto in zip(self.rows, expected_rtos):
            self.assertIn(rto, row)

    def test_target_rpo_values_present_for_all_rows(self):
        expected_rpos = ["< 5 Seconds", "< 1 Minute", "< 5 Minutes", "< 24 Hours"]
        for row, rpo in zip(self.rows, expected_rpos):
            self.assertIn(rpo, row)


class SitemapArtifactsDrOptionsEvaluationTestCase(unittest.TestCase):
    """Tests that the DR Evaluation page URL is correctly present in the
    checked-in sitemap.txt / sitemap.xml artifacts (both in docs/ and at the
    repository root), and that regenerating the sitemaps via
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

    def test_url_present_after_dr_options_url_in_root_sitemap_txt(self):
        content = _read(ROOT_SITEMAP_TXT_PATH)
        dr_options_idx = content.index(
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
            "executive/dr-options.html"
        )
        dr_eval_idx = content.index(EXPECTED_GH_URL)
        self.assertLess(dr_options_idx, dr_eval_idx)

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

    def test_regenerating_sitemaps_reproduces_the_dr_evaluation_urls(self):
        """Integration/regression test: regenerate sitemap.txt and
        sitemap.xml from the current docs/ tree (mirroring the pattern used
        in tests/test_sitemaps.py) and confirm the DR Evaluation page is
        (re)discovered by the crawler that walks docs/executive/."""
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