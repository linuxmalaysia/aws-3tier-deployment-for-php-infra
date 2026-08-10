#!/usr/bin/env python3
"""Unit tests for the "Load Testing & Performance Analysis" documentation
added in this PR.

This PR introduces a new documentation page
(``docs/performance-analysis.md``) and wires it up from two other files:

* ``docs/index.md`` -- adds a bullet link pointing at
  ``performance-analysis.html``, directly after the existing
  "Performance Testing & Scaling Roadmap" link.
* ``llms.txt``       -- adds an AI-agent index entry pointing at
  ``docs/performance-analysis.md``, directly after the existing
  "Performance Testing and Scaling Roadmap" entry.

These files are treated as plain text (rather than parsed with a YAML/HTML
library) to stay dependency free, following the pattern already used by
``tests/test_performance_testing_docs.py``. The tests pin down the exact
cross-references between the changed files and validate the internal
structural/numeric consistency of the new report, including its
cross-referencing of cost figures back to ``docs/performance-testing.md``.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_performance_analysis_docs
"""
import os
import re
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import prepare_docs  # noqa: E402  (import after sys.path manipulation)

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
PERF_ANALYSIS_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "performance-analysis.md")
PERF_TESTING_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "performance-testing.md")

# The six Virtual User (VU) tiers documented in the new page, in the order
# they are expected to appear. These match the "Ujian Prestasi <tier> VU"
# headings (the tier text may be followed by extra descriptive suffixes,
# e.g. "(Critical Transition Point)").
VU_TIERS = ["100 VU", "500 VU", "1,000 VU", "2,500 VU", "5,000 VU", "10,000 VU"]

# Monthly USD totals expected for each tier -- these must stay in sync with
# the equivalent totals quoted in docs/performance-testing.md.
EXPECTED_USD_BY_TIER = {
    "100 VU": "141.47",
    "500 VU": "403.93",
    "1,000 VU": "539.17",
    "2,500 VU": "1,236.03",
    "5,000 VU": "1,948.12",
    "10,000 VU": "3,808.88",
}


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class IndexMdPerformanceAnalysisLinkTestCase(unittest.TestCase):
    """Tests for the new link added to docs/index.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)

    def test_index_file_exists(self):
        self.assertTrue(os.path.isfile(INDEX_PATH))

    def test_performance_analysis_link_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\*\*\[Load Testing & Performance Analysis\]\(engineering/performance-analysis\.html\):\*\*"
                r"\s*In-depth evaluation of load tests under 100 VU, 500 VU, 1,000 VU, 2,500 VU, 5,000 VU, and 10,000 VU loads"
            ),
        )

    def test_link_appears_after_performance_testing_link(self):
        perf_testing_idx = self.content.index(
            "[Performance Testing & Scaling Roadmap](engineering/performance-testing.html)"
        )
        perf_analysis_idx = self.content.index(
            "[Load Testing & Performance Analysis](engineering/performance-analysis.html)"
        )
        self.assertLess(perf_testing_idx, perf_analysis_idx)

    def test_link_appears_directly_after_performance_testing_link(self):
        """Regression: the new bullet must be inserted immediately after the
        Performance Testing & Scaling Roadmap bullet, with no other list
        item sandwiched in between."""
        perf_testing_idx = self.content.index(
            "[Performance Testing & Scaling Roadmap](engineering/performance-testing.html)"
        )
        perf_analysis_idx = self.content.index(
            "[Load Testing & Performance Analysis](engineering/performance-analysis.html)"
        )
        between = self.content[perf_testing_idx:perf_analysis_idx]
        self.assertEqual(between.count("\n"), 1)
        self.assertNotIn("\n- **[", between.strip("\n"))

    def test_link_appears_in_deployment_cicd_section(self):
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n---|\Z)", self.content, re.DOTALL
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[Load Testing & Performance Analysis](engineering/performance-analysis.html)",
            section_match.group(1),
        )

    def test_link_uses_relative_html_url_not_markdown_extension(self):
        self.assertIn("(engineering/performance-analysis.html)", self.content)
        self.assertNotIn("(engineering/performance-analysis.md)", self.content)

    def test_link_target_file_exists(self):
        self.assertTrue(os.path.isfile(PERF_ANALYSIS_PATH))

    def test_link_appears_exactly_once(self):
        self.assertEqual(
            self.content.count("[Load Testing & Performance Analysis]"), 1
        )


class LlmsTxtPerformanceAnalysisEntryTestCase(unittest.TestCase):
    """Tests for the new entry added to llms.txt."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LLMS_PATH)

    def test_llms_txt_file_exists(self):
        self.assertTrue(os.path.isfile(LLMS_PATH))

    def test_performance_analysis_entry_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\[Load Testing and Performance Analysis\]\(docs/engineering/performance-analysis\.md\)\s*:"
                r"\s*In-depth evaluation of load tests under 100 VU, 500 VU, 1,000 VU, 2,500 VU, 5,000 VU, and 10,000 VU loads"
            ),
        )

    def test_entry_under_costing_section_heading(self):
        section_match = re.search(
            r"## Deployment, Automation, and Costing\n(.*?)(?=\n## |\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[Load Testing and Performance Analysis](docs/engineering/performance-analysis.md)",
            section_match.group(1),
        )

    def test_entry_appears_directly_after_performance_testing_entry(self):
        perf_testing_idx = self.content.index(
            "[Performance Testing and Scaling Roadmap](docs/engineering/performance-testing.md)"
        )
        perf_analysis_idx = self.content.index(
            "[Load Testing and Performance Analysis](docs/engineering/performance-analysis.md)"
        )
        self.assertLess(perf_testing_idx, perf_analysis_idx)
        between = self.content[perf_testing_idx:perf_analysis_idx]
        self.assertEqual(between.count("\n"), 1)
        self.assertNotIn("\n- [", between.strip("\n"))

    def test_entry_target_file_exists(self):
        self.assertTrue(os.path.isfile(PERF_ANALYSIS_PATH))

    def test_entry_follows_bullet_link_colon_description_format(self):
        match = re.search(
            r"^- \[Load Testing and Performance Analysis\]\(docs/engineering/performance-analysis\.md\) : .+$",
            self.content,
            re.MULTILINE,
        )
        self.assertIsNotNone(
            match, "Entry does not follow the '- [Title](path) : description' format"
        )

    def test_entry_appears_exactly_once(self):
        self.assertEqual(
            self.content.count("[Load Testing and Performance Analysis]"), 1
        )


class CrossFileReferenceConsistencyTestCase(unittest.TestCase):
    """Verifies the slug used for performance-analysis is consistent across
    docs/index.md and llms.txt."""

    @classmethod
    def setUpClass(cls):
        cls.index_content = _read(INDEX_PATH)
        cls.llms_content = _read(LLMS_PATH)

    def test_html_slug_used_in_index(self):
        self.assertIn("(engineering/performance-analysis.html)", self.index_content)

    def test_markdown_path_consistent_between_llms_txt_and_filesystem(self):
        match = re.search(
            r"\[Load Testing and Performance Analysis\]\((docs/engineering/performance-analysis\.md)\)",
            self.llms_content,
        )
        self.assertIsNotNone(match)
        referenced_path = os.path.join(REPO_ROOT, match.group(1))
        self.assertTrue(os.path.isfile(referenced_path))
        self.assertEqual(os.path.normpath(referenced_path), PERF_ANALYSIS_PATH)


class PerformanceAnalysisMarkdownFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of docs/performance-analysis.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_ANALYSIS_PATH)
        stripped = cls.content.lstrip()
        parts = stripped.split("---", 2)
        # parts[0] is empty (before first ---), parts[1] is the front matter body.
        cls.front_matter_text = parts[1]
        cls.body_text = parts[2]
        cls.front_matter = prepare_docs.parse_yaml_front_matter(cls.front_matter_text)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(PERF_ANALYSIS_PATH))

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
            "AWS Secure App Performance Analysis & Load Testing Report",
        )

    def test_type_matches_prepare_docs_inference(self):
        """docs/*.md files that aren't index.md or under docs/modules are
        inferred as 'Technical Reference Guide' by prepare_docs.py; the
        front matter of the new doc should match that convention."""
        inferred_type = prepare_docs.infer_okf_type("docs/engineering/performance-analysis.md")
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_is_a_list_of_strings(self):
        topics = self.front_matter["topics"]
        self.assertIsInstance(topics, list)
        self.assertTrue(all(isinstance(t, str) for t in topics))

    def test_topics_include_performance_testing_tag(self):
        self.assertIn("performance-testing", self.front_matter["topics"])

    def test_topics_have_no_duplicates(self):
        topics = self.front_matter["topics"]
        self.assertEqual(len(topics), len(set(topics)))

    def test_timestamp_is_iso_8601_with_offset(self):
        timestamp = self.front_matter["timestamp"]
        self.assertRegex(
            str(timestamp), r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$"
        )

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        heading_text = heading_match.group(1).strip()
        self.assertEqual(heading_text, self.front_matter["title"])


class PerformanceAnalysisContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of docs/performance-analysis.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_ANALYSIS_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn(
            "# AWS Secure App Performance Analysis & Load Testing Report",
            self.content,
        )

    def test_contains_correlation_matrix_section(self):
        self.assertIn("## Performance & Cost Correlation Matrix", self.content)

    def test_contains_technical_breakdown_section(self):
        self.assertIn("## 1. Technical Breakdown by VU Load Level", self.content)

    def test_contains_rca_section(self):
        self.assertIn(
            "## 2. Root Cause Analysis (RCA) - Load Test Bottleneck Summary",
            self.content,
        )

    def test_contains_finops_alignment_section(self):
        self.assertIn(
            "## 3. Financial and Performance Optimization Alignment", self.content
        )

    def test_conversion_rate_is_stated(self):
        self.assertIn("1 USD = 4.50 MYR", self.content)

    def test_cross_reference_link_to_performance_testing_present(self):
        self.assertIn(
            "[System Performance Analysis & Multi-VU Scale-Up Roadmap](performance-testing.html)",
            self.content,
        )

    def test_all_five_vu_tier_headings_present(self):
        for tier in VU_TIERS:
            with self.subTest(tier=tier):
                self.assertIn(f"### 🚀 Ujian Prestasi {tier}", self.content)

    def test_vu_tier_headings_appear_in_ascending_order(self):
        indices = [
            self.content.index(f"### 🚀 Ujian Prestasi {tier}") for tier in VU_TIERS
        ]
        self.assertEqual(indices, sorted(indices))

    def test_each_vu_tier_has_four_subsections(self):
        sections = re.split(r"### 🚀 Ujian Prestasi ", self.content)[1:]
        self.assertEqual(len(sections), len(VU_TIERS))
        for section in sections:
            with self.subTest(section=section.splitlines()[0]):
                self.assertIn("#### A. Test Conditions", section)
                self.assertIn("#### B. Component Performance Results", section)
                self.assertIn(
                    "#### C. Problems Encountered & Root Causes", section
                )
                self.assertIn("#### D. Recommendations & Sizing Mapping", section)

    def test_sections_appear_between_matrix_and_rca_headings(self):
        matrix_idx = self.content.index("## Performance & Cost Correlation Matrix")
        breakdown_idx = self.content.index(
            "## 1. Technical Breakdown by VU Load Level"
        )
        rca_idx = self.content.index(
            "## 2. Root Cause Analysis (RCA) - Load Test Bottleneck Summary"
        )
        self.assertLess(matrix_idx, breakdown_idx)
        self.assertLess(breakdown_idx, rca_idx)
        for tier in VU_TIERS:
            tier_idx = self.content.index(f"### 🚀 Ujian Prestasi {tier}")
            self.assertLess(breakdown_idx, tier_idx)
            self.assertLess(tier_idx, rca_idx)

    def test_sql_code_blocks_are_balanced(self):
        """Boundary check: every ```sql fenced block must be terminated by a
        closing ``` fence, otherwise the rendered Markdown/Jekyll page would
        be broken."""
        fence_count = len(re.findall(r"^\s*```", self.content, re.MULTILINE))
        self.assertGreater(fence_count, 0)
        self.assertEqual(fence_count % 2, 0)


class PerformanceAnalysisCorrelationMatrixTestCase(unittest.TestCase):
    """Tests for the Performance & Cost Correlation Matrix table."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_ANALYSIS_PATH)
        section_match = re.search(
            r"## Performance & Cost Correlation Matrix\n(.*?)\nAll estimates",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None
        cls.section = section_match.group(1)

    def test_matrix_has_header_and_six_data_rows(self):
        # 1 header row + 1 separator row + 6 data rows = 8 pipe-table lines.
        table_rows = [
            line for line in self.section.splitlines() if line.strip().startswith("|")
        ]
        self.assertEqual(len(table_rows), 8)

    def test_matrix_lists_all_vu_tiers_in_order(self):
        matches = re.findall(r"\|\s*\*\*([\d,]+ VU)\*\*\s*\|", self.section)
        self.assertEqual(matches, VU_TIERS)

    def test_matrix_monthly_costs_match_performance_testing_totals(self):
        """Regression: the USD cost quoted for each tier in this report must
        stay consistent with the equivalent total in
        docs/performance-testing.md."""
        matches = re.findall(
            r"\|\s*\*\*([\d,]+ VU)\*\*.*?\*\*\$([\d,]+\.\d{2}) USD\*\*", self.section
        )
        self.assertEqual(len(matches), 6)
        found = dict(matches)
        self.assertEqual(found, EXPECTED_USD_BY_TIER)

    def test_matrix_performance_status_values_are_pass_or_fail(self):
        statuses = re.findall(r"\*\*(PASS|FAIL) \([^)]+\)\*\*", self.section)
        self.assertEqual(len(statuses), 6)
        for status in statuses:
            self.assertIn(status, ("PASS", "FAIL"))

    def test_only_2500_vu_tier_is_marked_as_fail(self):
        """Regression: 2,500 VU is documented elsewhere in this report as
        the critical bottleneck transition point, and should be the only
        row marked FAIL in the correlation matrix."""
        rows = self.section.strip().splitlines()
        data_rows = [
            row
            for row in rows
            if row.strip().startswith("|") and "**" in row and "---" not in row
        ]
        self.assertEqual(len(data_rows), 6)  # 6 data rows (header has no "**")
        fail_rows = [row for row in data_rows if "FAIL" in row]
        self.assertEqual(len(fail_rows), 1)
        self.assertIn("2,500 VU", fail_rows[0])

    def test_matrix_sizing_reference_links_target_performance_testing_and_correct_tier(self):
        rows = re.findall(
            r"\|\s*\*\*([\d,]+ VU)\*\*.*?\[[^\]]+\]\((performance-testing\.html#[^)]+)\)\s*\|",
            self.section,
        )
        self.assertEqual(len(rows), 6)
        for tier, anchor in rows:
            with self.subTest(tier=tier):
                self.assertTrue(anchor.startswith("performance-testing.html#"))
                tier_digits = tier.replace(",", "").split(" ")[0]
                self.assertIn(f"{tier_digits}-vu", anchor.replace(",", ""))

    def test_matrix_sizing_reference_targets_existing_file(self):
        self.assertTrue(os.path.isfile(PERF_TESTING_PATH))


class PerformanceAnalysisRootCauseAnalysisTestCase(unittest.TestCase):
    """Tests for the Section 2 Root Cause Analysis (RCA) summary table."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_ANALYSIS_PATH)
        section_match = re.search(
            r"## 2\. Root Cause Analysis \(RCA\) - Load Test Bottleneck Summary\n"
            r"(.*?)\n---",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None
        cls.section = section_match.group(1)

    def test_rca_table_has_header_and_four_data_rows(self):
        table_rows = [
            line for line in self.section.splitlines() if line.strip().startswith("|")
        ]
        # 1 header row + 1 separator row + 4 data rows = 6 pipe-table lines.
        self.assertEqual(len(table_rows), 6)

    def test_rca_table_contains_expected_impacted_components(self):
        for component in ["RDS MariaDB", "RDS PostgreSQL", "ALB WAFv2", "Nginx & PHP-FPM"]:
            with self.subTest(component=component):
                self.assertIn(f"**{component}**", self.section)

    def test_rca_table_rows_have_five_columns(self):
        data_rows = [
            line
            for line in self.section.splitlines()
            if line.strip().startswith("|") and "---" not in line
        ]
        # Header + 4 data rows.
        self.assertEqual(len(data_rows), 5)
        for row in data_rows:
            # A row with N columns has N+1 pipe characters.
            self.assertEqual(row.count("|"), 6)

    def test_mariadb_root_cause_references_correct_tables(self):
        mariadb_row = next(
            (line for line in self.section.splitlines() if "RDS MariaDB" in line),
            None,
        )
        self.assertIsNotNone(mariadb_row)
        self.assertIn("summary", mariadb_row)
        self.assertIn("recons_2025", mariadb_row)

    def test_postgresql_root_cause_references_wal_sync(self):
        postgres_row = next(
            (line for line in self.section.splitlines() if "RDS PostgreSQL" in line),
            None,
        )
        self.assertIsNotNone(postgres_row)
        self.assertIn("I/O:walSync", postgres_row)


if __name__ == "__main__":
    unittest.main()