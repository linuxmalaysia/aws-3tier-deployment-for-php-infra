#!/usr/bin/env python3
"""Unit tests for the "Performance Testing & Scaling Roadmap" documentation
added in this PR.

This PR introduces a new documentation page
(``docs/performance-testing.md``) and wires it up from two other files:

* ``docs/index.md`` -- adds a bullet link pointing at
  ``performance-testing.html``.
* ``llms.txt``       -- adds an AI-agent index entry pointing at
  ``docs/performance-testing.md``.

These files are treated as plain text (rather than parsed with a YAML/HTML
library) to stay dependency free, following the pattern already used by
``tests/test_production_costing_docs.py``. The tests pin down the exact
cross-references between the changed files and validate the internal
numeric consistency of the new multi-VU cost tables.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_performance_testing_docs
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
PERF_TESTING_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "performance-testing.md")

# The six Virtual User (VU) tiers documented in the new page, in the order
# they are expected to appear.
VU_TIER_HEADINGS = [
    "100 VU",
    "500 VU",
    "1,000 VU",
    "2,500 VU",
    "5,000 VU",
    "10,000 VU",
]

USD_TO_MYR_RATE = 4.50


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class IndexMdPerformanceTestingLinkTestCase(unittest.TestCase):
    """Tests for the new link added to docs/index.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)

    def test_index_file_exists(self):
        self.assertTrue(os.path.isfile(INDEX_PATH))

    def test_performance_testing_link_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\*\*\[Performance Testing & Scaling Roadmap\]\(engineering/performance-testing\.html\):\*\*"
                r"\s*Comprehensive analysis of 100 VU, 500 VU, 1,000 VU, 2,500 VU, 5,000 VU, and 10,000 VU loads"
            ),
        )

    def test_link_appears_after_production_costing_link(self):
        prod_idx = self.content.index(
            "[Production Costing Estimate](executive/production-costing.html)"
        )
        perf_idx = self.content.index(
            "[Performance Testing & Scaling Roadmap](engineering/performance-testing.html)"
        )
        self.assertLess(prod_idx, perf_idx)

    def test_link_appears_in_deployment_cicd_section(self):
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n---|\Z)", self.content, re.DOTALL
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[Performance Testing & Scaling Roadmap](engineering/performance-testing.html)",
            section_match.group(1),
        )

    def test_link_uses_relative_html_url_not_markdown_extension(self):
        self.assertIn("(engineering/performance-testing.html)", self.content)
        self.assertNotIn("(engineering/performance-testing.md)", self.content)

    def test_link_target_file_exists(self):
        self.assertTrue(os.path.isfile(PERF_TESTING_PATH))

    def test_link_appears_exactly_once(self):
        self.assertEqual(
            self.content.count("[Performance Testing & Scaling Roadmap]"), 1
        )


class LlmsTxtPerformanceTestingEntryTestCase(unittest.TestCase):
    """Tests for the new entry added to llms.txt."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LLMS_PATH)

    def test_llms_txt_file_exists(self):
        self.assertTrue(os.path.isfile(LLMS_PATH))

    def test_performance_testing_entry_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\[Performance Testing and Scaling Roadmap\]\(docs/engineering/performance-testing\.md\)\s*:"
                r"\s*Comprehensive analysis of 100 VU, 500 VU, 1,000 VU, 2,500 VU, 5,000 VU, and 10,000 VU loads"
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
            "[Performance Testing and Scaling Roadmap](docs/engineering/performance-testing.md)",
            section_match.group(1),
        )

    def test_entry_appears_directly_after_production_costing_guide_entry(self):
        prod_idx = self.content.index(
            "[Production Costing Guide](docs/executive/production-costing.md)"
        )
        perf_idx = self.content.index(
            "[Performance Testing and Scaling Roadmap](docs/engineering/performance-testing.md)"
        )
        self.assertLess(prod_idx, perf_idx)
        # The end of the "Production Costing Guide" line should flow
        # directly (across a single newline) into the start of the
        # "Performance Testing and Scaling Roadmap" bullet, with no other
        # entry sandwiched between them.
        between = self.content[prod_idx:perf_idx]
        self.assertEqual(between.count("\n"), 1)
        self.assertNotIn("\n- [", between.strip("\n"))

    def test_entry_target_file_exists(self):
        self.assertTrue(os.path.isfile(PERF_TESTING_PATH))

    def test_entry_follows_bullet_link_colon_description_format(self):
        match = re.search(
            r"^- \[Performance Testing and Scaling Roadmap\]\(docs/engineering/performance-testing\.md\) : .+$",
            self.content,
            re.MULTILINE,
        )
        self.assertIsNotNone(
            match, "Entry does not follow the '- [Title](path) : description' format"
        )

    def test_entry_appears_exactly_once(self):
        self.assertEqual(
            self.content.count("[Performance Testing and Scaling Roadmap]"), 1
        )


class CrossFileReferenceConsistencyTestCase(unittest.TestCase):
    """Verifies the slug used for performance-testing is consistent across
    docs/index.md and llms.txt."""

    @classmethod
    def setUpClass(cls):
        cls.index_content = _read(INDEX_PATH)
        cls.llms_content = _read(LLMS_PATH)

    def test_html_slug_used_in_index(self):
        self.assertIn("(engineering/performance-testing.html)", self.index_content)

    def test_markdown_path_consistent_between_llms_txt_and_filesystem(self):
        match = re.search(
            r"\[Performance Testing and Scaling Roadmap\]\((docs/engineering/performance-testing\.md)\)",
            self.llms_content,
        )
        self.assertIsNotNone(match)
        referenced_path = os.path.join(REPO_ROOT, match.group(1))
        self.assertTrue(os.path.isfile(referenced_path))
        self.assertEqual(os.path.normpath(referenced_path), PERF_TESTING_PATH)


class PerformanceTestingMarkdownFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of docs/performance-testing.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_TESTING_PATH)
        stripped = cls.content.lstrip()
        parts = stripped.split("---", 2)
        # parts[0] is empty (before first ---), parts[1] is the front matter body.
        cls.front_matter_text = parts[1]
        cls.body_text = parts[2]
        cls.front_matter = prepare_docs.parse_yaml_front_matter(cls.front_matter_text)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(PERF_TESTING_PATH))

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
            "System Performance Analysis & Multi-VU Scale-Up Roadmap",
        )

    def test_type_matches_prepare_docs_inference(self):
        """docs/*.md files that aren't index.md or under docs/modules are
        inferred as 'Technical Reference Guide' by prepare_docs.py; the
        front matter of the new doc should match that convention."""
        inferred_type = prepare_docs.infer_okf_type("docs/engineering/performance-testing.md")
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

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        heading_text = heading_match.group(1).strip()
        self.assertEqual(heading_text, self.front_matter["title"])


class PerformanceTestingContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of docs/performance-testing.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_TESTING_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn(
            "# System Performance Analysis & Multi-VU Scale-Up Roadmap", self.content
        )

    def test_contains_methodology_section(self):
        self.assertIn("## Performance Testing Methodology & Core Metrics", self.content)

    def test_contains_sizing_matrix_section(self):
        self.assertIn("## 1. Multi-VU Performance Sizing and Cost Matrix", self.content)

    def test_contains_technical_breakdown_section(self):
        self.assertIn("## 2. In-Depth Technical Breakdown by VU Level", self.content)

    def test_contains_finops_section(self):
        self.assertIn(
            "## 3. Financial Optimization Recommendations (Day-2 FinOps)", self.content
        )

    def test_conversion_rate_is_stated(self):
        self.assertIn("1 USD = 4.50 MYR", self.content)

    def test_all_five_vu_tier_headings_present(self):
        for tier in VU_TIER_HEADINGS:
            with self.subTest(tier=tier):
                self.assertIn(f"### 🚀 {tier} —", self.content)

    def test_vu_tier_headings_appear_in_ascending_order(self):
        indices = [self.content.index(f"### 🚀 {tier} —") for tier in VU_TIER_HEADINGS]
        self.assertEqual(indices, sorted(indices))

    def test_each_vu_tier_has_three_subsections(self):
        sections = re.split(r"### 🚀 ", self.content)[1:]
        self.assertEqual(len(sections), len(VU_TIER_HEADINGS))
        for section in sections:
            with self.subTest(section=section.splitlines()[0]):
                self.assertIn(
                    "#### A. AWS Services & Sizing Specifications", section
                )
                self.assertIn(
                    "#### B. Sizing & Line-Item Costing (Monthly)", section
                )
                self.assertIn("#### C. Performance Insights & Bottlenecks", section)

    def test_sections_appear_between_matrix_and_finops_headings(self):
        matrix_idx = self.content.index(
            "## 1. Multi-VU Performance Sizing and Cost Matrix"
        )
        breakdown_idx = self.content.index(
            "## 2. In-Depth Technical Breakdown by VU Level"
        )
        finops_idx = self.content.index(
            "## 3. Financial Optimization Recommendations (Day-2 FinOps)"
        )
        self.assertLess(matrix_idx, breakdown_idx)
        self.assertLess(breakdown_idx, finops_idx)
        for tier in VU_TIER_HEADINGS:
            tier_idx = self.content.index(f"### 🚀 {tier} —")
            self.assertLess(breakdown_idx, tier_idx)
            self.assertLess(tier_idx, finops_idx)


class PerformanceTestingSizingMatrixTestCase(unittest.TestCase):
    """Tests for the Section 1 Multi-VU sizing/cost matrix table."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_TESTING_PATH)
        section_match = re.search(
            r"## 1\. Multi-VU Performance Sizing and Cost Matrix\n(.*?)\n---",
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
        self.assertEqual(matches, ["100 VU", "500 VU", "1,000 VU", "2,500 VU", "5,000 VU", "10,000 VU"])

    def test_matrix_monthly_costs_are_positive_and_increasing(self):
        matches = re.findall(
            r"\*\*\$([\d,]+\.\d{2}) USD\*\*", self.section
        )
        self.assertEqual(len(matches), 6)
        usd_values = [float(v.replace(",", "")) for v in matches]
        for v in usd_values:
            self.assertGreater(v, 0)
        # Regression: cost must strictly increase as VU load scales up.
        self.assertEqual(usd_values, sorted(usd_values))

    def test_matrix_myr_values_match_conversion_rate(self):
        pairs = re.findall(
            r"\*\*\$([\d,]+\.\d{2}) USD\*\*\s*\|\s*\*\*RM ([\d,]+\.\d{2}) MYR\*\*",
            self.section,
        )
        self.assertEqual(len(pairs), 6)
        for usd_str, myr_str in pairs:
            usd = float(usd_str.replace(",", ""))
            myr = float(myr_str.replace(",", ""))
            expected_myr = round(usd * USD_TO_MYR_RATE, 2)
            self.assertAlmostEqual(
                myr, expected_myr, delta=0.01,
                msg=f"${usd} -> RM{myr} does not match rate of 4.50 (expected RM{expected_myr})",
            )


class PerformanceTestingLineItemCostingTestCase(unittest.TestCase):
    """Regression tests validating the internal arithmetic of each VU
    tier's "B. Sizing & Line-Item Costing" bullet list: MYR figures must
    match the stated 1 USD = 4.50 MYR conversion rate, and the totals
    quoted in each tier's detail section must match the totals quoted in
    the Section 1 summary matrix."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_TESTING_PATH)
        cls.sections = re.split(r"### 🚀 ", cls.content)[1:]

    @staticmethod
    def _extract_costing_block(section_text):
        match = re.search(
            r"#### B\. Sizing & Line-Item Costing \(Monthly\)\n(.*?)\n\n",
            section_text,
            re.DOTALL,
        )
        assert match is not None, "Could not locate the line-item costing block"
        return match.group(1)

    @staticmethod
    def _extract_component_rows(block_text):
        """Extract (usd, myr) tuples for every non-Total bullet line."""
        pattern = re.compile(r"^\* \*\*(?!Total Monthly Cost)(?!.*Alternative).+?:\*\*\s*\$([\d,]+\.\d{2}) USD \(RM ([\d,]+\.\d{2}) MYR\)(?:[^\n]*)$", re.MULTILINE)
        rows = []
        for usd_str, myr_str in pattern.findall(block_text):
            rows.append((float(usd_str.replace(",", "")), float(myr_str.replace(",", ""))))
        return rows

    @staticmethod
    def _extract_total_row(block_text):
        match = re.search(
            r"\*\*Total Monthly Cost:\*\*\s*\*\*\$([\d,]+\.\d{2}) USD\*\*\s*/\s*\*\*RM ([\d,]+\.\d{2}) MYR\*\*",
            block_text,
        )
        assert match is not None, "Could not locate the Total Monthly Cost line"
        return float(match.group(1).replace(",", "")), float(match.group(2).replace(",", ""))

    def test_every_tier_has_a_total_monthly_cost_line(self):
        for section in self.sections:
            tier_name = section.splitlines()[0]
            with self.subTest(tier=tier_name):
                block = self._extract_costing_block(section)
                total_usd, total_myr = self._extract_total_row(block)
                self.assertGreater(total_usd, 0)
                self.assertGreater(total_myr, 0)

    def test_every_tier_component_and_total_myr_values_match_conversion_rate(self):
        for section in self.sections:
            tier_name = section.splitlines()[0]
            with self.subTest(tier=tier_name):
                block = self._extract_costing_block(section)
                rows = self._extract_component_rows(block) + [self._extract_total_row(block)]
                self.assertTrue(rows, "Expected at least one cost row")
                for usd, myr in rows:
                    expected_myr = round(usd * USD_TO_MYR_RATE, 2)
                    self.assertAlmostEqual(
                        myr, expected_myr, delta=0.01,
                        msg=f"${usd} -> RM{myr} does not match rate of 4.50 "
                        f"(expected RM{expected_myr}) in section {tier_name!r}",
                    )

    def test_every_tier_detail_total_matches_summary_matrix_total(self):
        """Regression: the Total Monthly Cost quoted inside each VU tier's
        detailed breakdown must equal the figure quoted for that same tier
        in the Section 1 summary matrix table."""
        matrix_section_match = re.search(
            r"## 1\. Multi-VU Performance Sizing and Cost Matrix\n(.*?)\n---",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(matrix_section_match)
        matrix_rows = re.findall(
            r"\|\s*\*\*([\d,]+ VU)\*\*.*?\*\*\$([\d,]+\.\d{2}) USD\*\*\s*\|\s*\*\*RM ([\d,]+\.\d{2}) MYR\*\*",
            matrix_section_match.group(1),
        )
        self.assertEqual(len(matrix_rows), 6)
        matrix_totals = {
            tier: (float(usd.replace(",", "")), float(myr.replace(",", "")))
            for tier, usd, myr in matrix_rows
        }

        for section, tier in zip(self.sections, VU_TIER_HEADINGS):
            with self.subTest(tier=tier):
                block = self._extract_costing_block(section)
                detail_total = self._extract_total_row(block)
                component_rows = self._extract_component_rows(block)
                sum_usd = sum(r[0] for r in component_rows)
                sum_myr = sum(r[1] for r in component_rows)

                # Verify that sums of component line-items match detail_total exactly (or within a tiny float precision)
                self.assertAlmostEqual(sum_usd, detail_total[0], delta=0.01)
                self.assertAlmostEqual(sum_myr, detail_total[1], delta=0.01)

                # Check match with matrix_totals
                self.assertEqual(detail_total, matrix_totals[tier])

    def test_all_extracted_cost_figures_are_positive(self):
        """Boundary check: no line item or total in any VU tier should be
        zero or negative -- a negative/zero cost would indicate a typo or a
        broken table row."""
        found_any = False
        for section in self.sections:
            block = self._extract_costing_block(section)
            rows = self._extract_component_rows(block) + [self._extract_total_row(block)]
            for usd, myr in rows:
                found_any = True
                self.assertGreater(usd, 0)
                self.assertGreater(myr, 0)
        self.assertTrue(found_any, "Expected to extract at least one cost row")

    def test_compute_tier_cost_strictly_increases_with_vu_load(self):
        """Regression/sanity check: as the target VU load scales up, the
        Compute Tier (ASG) line item cost must never decrease."""
        compute_costs = []
        for section in self.sections:
            block = self._extract_costing_block(section)
            match = re.search(
                r"\*\*Compute Tier \(ASG\):\*\*\s*\$([\d,]+\.\d{2}) USD", block
            )
            self.assertIsNotNone(match)
            compute_costs.append(float(match.group(1).replace(",", "")))
        self.assertEqual(compute_costs, sorted(compute_costs))


class PerformanceTesting2500VuMyrRoundingRegressionTestCase(unittest.TestCase):
    """Regression tests for a rounding fix applied to the 2,500 VU tier's
    MYR figure: RM 5,562.14 (the value that
    actually results from $1,236.03 * 4.50, rounded to 2 decimal places) in
    both the Section 1 summary matrix and the 2,500 VU tier's own "Total
    Monthly Cost" line."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_TESTING_PATH)

    def test_incorrect_myr_value_no_longer_present(self):
        self.assertNotIn("4,807.49", self.content)

    def test_corrected_myr_value_present(self):
        self.assertIn("RM 5,562.14 MYR", self.content)

    def test_corrected_value_appears_in_summary_matrix_and_detail_section(self):
        # The corrected figure must appear exactly twice: once in the
        # Section 1 summary matrix row for 2,500 VU, and once in the
        # 2,500 VU tier's own "Total Monthly Cost" line.
        self.assertEqual(self.content.count("RM 5,562.14 MYR"), 2)

    def test_corrected_value_matches_conversion_rate(self):
        usd = 1236.03
        expected_myr = round(usd * USD_TO_MYR_RATE, 2)
        self.assertAlmostEqual(expected_myr, 5562.14, delta=0.01)
        self.assertIn(f"RM {expected_myr:,.2f} MYR", self.content)


class PerformanceTestingComputeTierLabelFormatTestCase(unittest.TestCase):
    """Regression tests for the reformatted "Compute Tier (ASG)" line items:
    the instance-count/type detail (e.g. "2x t4g.micro nodes") was moved out
    of the bold label and into a trailing parenthetical after the cost
    figures, e.g.:

        Before: * **Compute Tier (ASG - 2x t4g.micro nodes):** $12.26 USD (RM 55.17 MYR)
        After:  * **Compute Tier (ASG):** $12.26 USD (RM 55.17 MYR) (2x t4g.micro nodes)
    """

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_TESTING_PATH)
        cls.sections = re.split(r"### 🚀 ", cls.content)[1:]

    def test_old_label_format_no_longer_present(self):
        self.assertNotIn("**Compute Tier (ASG -", self.content)

    def test_new_label_format_present_for_every_tier(self):
        matches = re.findall(
            r"^\* \*\*Compute Tier \(ASG\):\*\*\s*\$[\d,]+\.\d{2} USD "
            r"\(RM [\d,]+\.\d{2} MYR\)\s*\(.+?\)$",
            self.content,
            re.MULTILINE,
        )
        self.assertEqual(len(matches), len(VU_TIER_HEADINGS))

    def test_every_tier_has_exactly_one_compute_tier_line(self):
        for section in self.sections:
            tier_name = section.splitlines()[0]
            with self.subTest(tier=tier_name):
                self.assertEqual(
                    len(re.findall(r"\*\*Compute Tier \(ASG\):\*\*", section)), 1
                )

    def test_compute_tier_node_detail_matches_expected_text(self):
        expected_details = [
            "2x t4g.micro nodes",
            "2x t4g.medium nodes",
            "Average 4x t4g.xlarge nodes",
            "Minimum 4x t4g.xlarge nodes",
            "Minimum 8x t4g.xlarge nodes",
        ]
        for detail in expected_details:
            with self.subTest(detail=detail):
                self.assertIn(
                    f"**Compute Tier (ASG):** ", self.content
                )
                self.assertRegex(
                    self.content,
                    re.compile(
                        r"\*\*Compute Tier \(ASG\):\*\*\s*\$[\d,]+\.\d{2} USD "
                        r"\(RM [\d,]+\.\d{2} MYR\)\s*\("
                        + re.escape(detail)
                        + r"\)"
                    ),
                )


class PerformanceTestingTotalMonthlyCostLabelConsistencyTestCase(unittest.TestCase):
    """Regression tests for the renamed "Total Monthly Cost" line item: the
    10,000 VU tier previously used the inconsistent label
    "Total Monthly Cost (Base Specs):" while every other tier used
    "Total Monthly Cost:". This PR normalizes the label so that all five
    tiers use the same wording."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_TESTING_PATH)

    def test_old_base_specs_label_no_longer_present(self):
        self.assertNotIn("Total Monthly Cost (Base Specs):", self.content)

    def test_total_monthly_cost_label_appears_once_per_tier(self):
        matches = re.findall(r"\*\*Total Monthly Cost:\*\*", self.content)
        self.assertEqual(len(matches), len(VU_TIER_HEADINGS))

    def test_all_tiers_use_identical_total_monthly_cost_label(self):
        # Every "Total Monthly Cost" bullet must use exactly the same
        # wording, with no tier-specific suffix such as "(Base Specs)".
        labels = re.findall(r"\*\*(Total Monthly Cost[^*]*):\*\*", self.content)
        self.assertEqual(len(labels), len(VU_TIER_HEADINGS))
        self.assertEqual(set(labels), {"Total Monthly Cost"})


class PerformanceTesting2500VuBastionMyrRoundingRegressionTestCase(unittest.TestCase):
    """Regression tests for the 2,500 VU tier's
    "Bastion / Standalone (2x t4g.xlarge)" line item: the MYR figure should
    match $201.02 * 4.50 rounded to 2 decimal places (which is 904.59)."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_TESTING_PATH)

    def test_incorrect_myr_value_no_longer_present(self):
        self.assertNotIn("RM 1,032.98 MYR", self.content)

    def test_corrected_myr_value_present(self):
        self.assertIn("RM 904.59 MYR", self.content)

    def test_corrected_value_appears_exactly_once(self):
        # The Bastion / Standalone line item for the 2,500 VU tier is expected to appear.
        self.assertEqual(self.content.count("RM 904.59 MYR"), 1)

    def test_corrected_value_matches_conversion_rate(self):
        usd = 201.02
        expected_myr = round(usd * USD_TO_MYR_RATE, 2)
        self.assertAlmostEqual(expected_myr, 904.59, delta=0.001)
        self.assertIn(f"RM {expected_myr:,.2f} MYR", self.content)

    def test_corrected_value_appears_on_bastion_standalone_line(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\*\*Bastion / Standalone \(2x t4g\.xlarge\):\*\*\s*\$201\.02 USD "
                r"\(RM 904\.59 MYR\)"
            ),
        )

    def test_corrected_value_belongs_to_2500_vu_tier_section(self):
        sections = re.split(r"### 🚀 ", self.content)[1:]
        matching_sections = [
            s for s in sections if "RM 904.59 MYR" in s
        ]
        self.assertEqual(len(matching_sections), 1)
        self.assertTrue(matching_sections[0].startswith("2,500 VU"))


if __name__ == "__main__":
    unittest.main()