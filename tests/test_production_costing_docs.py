#!/usr/bin/env python3
"""Unit tests for the "Production Costing" documentation added in this PR.

This PR introduces a new documentation page (``docs/production-costing.md``)
and wires it up from three other files:

* ``docs/_config.yml``  -- adds a navbar entry pointing at
  ``/production-costing.html``.
* ``docs/index.md``     -- adds a bullet link pointing at
  ``production-costing.html``.
* ``llms.txt``           -- adds an AI-agent index entry pointing at
  ``docs/production-costing.md``.

These files are treated as plain text (rather than parsed with a YAML/HTML
library) to stay dependency free, following the pattern already used by
``tests/test_pdf_generation_workflow.py``. The tests pin down the exact
cross-references between the four changed files and validate the internal
numeric consistency of the new cost tables.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_production_costing_docs
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

CONFIG_PATH = os.path.join(REPO_ROOT, "docs", "_config.yml")
INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
PROD_COSTING_PATH = os.path.join(REPO_ROOT, "docs", "production-costing.md")


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

    def test_production_costing_navbar_entry_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r'-\s*title:\s*"Production Costing"\s*\n\s*url:\s*"/production-costing\.html"'
            ),
        )

    def test_navbar_entry_placed_directly_after_costing_entry(self):
        """Regression: the new entry should be inserted right after the
        existing 'Costing' entry, not appended somewhere unrelated."""
        match = re.search(
            r'-\s*title:\s*"Costing"\s*\n\s*url:\s*"/costing\.html"\s*\n'
            r'\s*-\s*title:\s*"Production Costing"\s*\n\s*url:\s*"/production-costing\.html"',
            self.content,
        )
        self.assertIsNotNone(
            match, "Expected 'Production Costing' entry directly after 'Costing'"
        )

    def test_navbar_entry_placed_before_route53_entry(self):
        prod_idx = self.content.index('title: "Production Costing"')
        route53_idx = self.content.index('title: "Route 53"')
        self.assertLess(prod_idx, route53_idx)

    def test_navbar_title_appears_exactly_once(self):
        self.assertEqual(self.content.count('"Production Costing"'), 1)

    def test_navbar_url_appears_exactly_once(self):
        self.assertEqual(self.content.count('/production-costing.html'), 1)

    def test_navbar_url_points_to_existing_doc_file(self):
        """The navbar entry URL should resolve to an actual markdown source
        file that Jekyll can build into production-costing.html."""
        self.assertTrue(os.path.isfile(PROD_COSTING_PATH))


class IndexMdProductionCostingLinkTestCase(unittest.TestCase):
    """Tests for the new link added to docs/index.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)

    def test_index_file_exists(self):
        self.assertTrue(os.path.isfile(INDEX_PATH))

    def test_production_costing_link_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\*\*\[Production Costing Estimate\]\(production-costing\.html\):\*\*"
                r"\s*Comprehensive monthly and annual production-scale cost breakdown"
            ),
        )

    def test_link_appears_after_costing_estimate_link(self):
        costing_idx = self.content.index("[Costing Estimate](costing.html)")
        prod_idx = self.content.index(
            "[Production Costing Estimate](production-costing.html)"
        )
        self.assertLess(costing_idx, prod_idx)

    def test_link_appears_in_deployment_cicd_section(self):
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n---|\Z)", self.content, re.DOTALL
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[Production Costing Estimate](production-costing.html)",
            section_match.group(1),
        )

    def test_link_uses_relative_html_url_not_markdown_extension(self):
        self.assertIn("(production-costing.html)", self.content)
        self.assertNotIn("(production-costing.md)", self.content)

    def test_link_target_file_exists(self):
        self.assertTrue(os.path.isfile(PROD_COSTING_PATH))

    def test_link_appears_exactly_once(self):
        self.assertEqual(
            self.content.count("[Production Costing Estimate]"), 1
        )


class LlmsTxtProductionCostingEntryTestCase(unittest.TestCase):
    """Tests for the new entry added to llms.txt."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LLMS_PATH)

    def test_llms_txt_file_exists(self):
        self.assertTrue(os.path.isfile(LLMS_PATH))

    def test_production_costing_entry_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\[Production Costing Guide\]\(docs/production-costing\.md\)\s*:"
                r"\s*Comprehensive monthly and annual production-scale cost breakdown"
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
            "[Production Costing Guide](docs/production-costing.md)",
            section_match.group(1),
        )

    def test_entry_appears_directly_after_costing_guide_entry(self):
        costing_idx = self.content.index("[Costing Guide](docs/costing.md)")
        prod_idx = self.content.index(
            "[Production Costing Guide](docs/production-costing.md)"
        )
        self.assertLess(costing_idx, prod_idx)
        # The end of the "Costing Guide" line should flow directly (across
        # a single newline) into the start of the "Production Costing
        # Guide" bullet, with no other entry sandwiched between them.
        between = self.content[costing_idx:prod_idx]
        self.assertEqual(between.count("\n"), 1)
        self.assertNotIn("\n- [", between.strip("\n"))

    def test_entry_target_file_exists(self):
        self.assertTrue(os.path.isfile(PROD_COSTING_PATH))

    def test_entry_follows_bullet_link_colon_description_format(self):
        match = re.search(
            r"^- \[Production Costing Guide\]\(docs/production-costing\.md\) : .+$",
            self.content,
            re.MULTILINE,
        )
        self.assertIsNotNone(
            match, "Entry does not follow the '- [Title](path) : description' format"
        )

    def test_entry_appears_exactly_once(self):
        self.assertEqual(self.content.count("[Production Costing Guide]"), 1)


class CrossFileReferenceConsistencyTestCase(unittest.TestCase):
    """Verifies the slug used for production-costing is consistent across
    docs/_config.yml, docs/index.md, and llms.txt."""

    @classmethod
    def setUpClass(cls):
        cls.config_content = _read(CONFIG_PATH)
        cls.index_content = _read(INDEX_PATH)
        cls.llms_content = _read(LLMS_PATH)

    def test_html_slug_consistent_between_navbar_and_index(self):
        self.assertIn("/production-costing.html", self.config_content)
        self.assertIn("(production-costing.html)", self.index_content)

    def test_markdown_path_consistent_between_llms_txt_and_filesystem(self):
        match = re.search(
            r"\[Production Costing Guide\]\((docs/production-costing\.md)\)",
            self.llms_content,
        )
        self.assertIsNotNone(match)
        referenced_path = os.path.join(REPO_ROOT, match.group(1))
        self.assertTrue(os.path.isfile(referenced_path))
        self.assertEqual(os.path.normpath(referenced_path), PROD_COSTING_PATH)


class ProductionCostingMarkdownFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of docs/production-costing.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PROD_COSTING_PATH)
        stripped = cls.content.lstrip()
        parts = stripped.split("---", 2)
        # parts[0] is empty (before first ---), parts[1] is the front matter body.
        cls.front_matter_text = parts[1]
        cls.body_text = parts[2]
        cls.front_matter = prepare_docs.parse_yaml_front_matter(cls.front_matter_text)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(PROD_COSTING_PATH))

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
            self.front_matter["title"], "Production Infrastructure Costing Analysis"
        )

    def test_type_matches_prepare_docs_inference(self):
        """docs/*.md files that aren't index.md or under docs/modules are
        inferred as 'Technical Reference Guide' by prepare_docs.py; the
        front matter of the new doc should match that convention."""
        inferred_type = prepare_docs.infer_okf_type("docs/production-costing.md")
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_is_a_list_of_strings(self):
        topics = self.front_matter["topics"]
        self.assertIsInstance(topics, list)
        self.assertTrue(all(isinstance(t, str) for t in topics))

    def test_topics_include_keyword_inferred_baseline(self):
        """The 'cost' keyword in the filename should map to finops/costing
        topics per prepare_docs.infer_okf_topics; the manually-authored
        front matter should be a superset of that inference."""
        inferred = prepare_docs.infer_okf_topics("docs/production-costing.md")
        self.assertEqual(inferred, ["aws", "3-tier", "finops", "costing"])
        for topic in inferred:
            self.assertIn(topic, self.front_matter["topics"])

    def test_topics_include_production_tag(self):
        self.assertIn("production", self.front_matter["topics"])

    def test_topics_have_no_duplicates(self):
        topics = self.front_matter["topics"]
        self.assertEqual(len(topics), len(set(topics)))

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        heading_text = heading_match.group(1).strip()
        # The body heading includes a parenthetical suffix not present in
        # the front matter title; the front matter title should be a prefix.
        self.assertTrue(heading_text.startswith(self.front_matter["title"]))


class ProductionCostingContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of docs/production-costing.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PROD_COSTING_PATH)

    def test_contains_baseline_scenario_heading(self):
        self.assertIn("### Scenario A: Baseline Cost-Optimized Plan", self.content)

    def test_contains_enterprise_scenario_heading(self):
        self.assertIn(
            "### Scenario B: High-Performance Enterprise Plan", self.content
        )

    def test_baseline_scenario_precedes_enterprise_scenario(self):
        baseline_idx = self.content.index("Scenario A")
        enterprise_idx = self.content.index("Scenario B")
        self.assertLess(baseline_idx, enterprise_idx)

    def test_asg_inventory_lists_nine_groups(self):
        asg_items = re.findall(r"^\d+\.\s+\*\*`secure-app-[\w-]+-asg`\*\*", self.content, re.MULTILINE)
        self.assertEqual(len(asg_items), 9)

    def test_alb_inventory_lists_three_load_balancers(self):
        section_match = re.search(
            r"3x Application Load Balancers \(ALBs\):\*{0,2}\n(.*?)\n\*",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        alb_items = re.findall(r"^\s*\d+\.\s+`secure-app-[\w-]+-alb`", section_match.group(1), re.MULTILINE)
        self.assertEqual(len(alb_items), 3)

    def test_conversion_rate_is_stated(self):
        self.assertIn("1 USD = 4.50 MYR", self.content)

    def test_anonymization_mapping_documented(self):
        self.assertIn("`pbtpay`", self.content)
        self.assertIn("`secure-app`", self.content)
        self.assertIn("`kpkt.gov.my`", self.content)
        self.assertIn("`enterprise.gov.my`", self.content)
        self.assertIn("`Radmikv2`", self.content)
        self.assertIn("`EnterpriseRepo`", self.content)

    def test_cost_optimization_section_present(self):
        self.assertIn("## 3. Cost-Optimization Pathways (Day-2 Operations)", self.content)


class ProductionCostingNumericConsistencyTestCase(unittest.TestCase):
    """Regression tests validating the internal arithmetic of the cost
    tables: component rows must sum to the stated TOTAL, and MYR figures
    must be consistent with the stated 1 USD = 4.50 MYR conversion rate."""

    USD_TO_MYR_RATE = 4.50

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PROD_COSTING_PATH)

    @staticmethod
    def _extract_section(content, start_marker, end_marker):
        match = re.search(
            re.escape(start_marker) + r"(.*?)" + re.escape(end_marker),
            content,
            re.DOTALL,
        )
        assert match is not None, f"Could not find section between {start_marker!r} and {end_marker!r}"
        return match.group(1)

    @staticmethod
    def _extract_rows(section_text):
        """Extract (usd, myr) float tuples from every table row (component
        rows and the final TOTAL row) in a cost-table section."""
        pattern = re.compile(
            r"\$([\d,]+\.\d{2})\*{0,2}\s*\|\s*\*{0,2}RM\s*([\d,]+\.\d{2})"
        )
        rows = []
        for usd_str, myr_str in pattern.findall(section_text):
            usd = float(usd_str.replace(",", ""))
            myr = float(myr_str.replace(",", ""))
            rows.append((usd, myr))
        return rows

    def _baseline_section(self):
        return self._extract_section(
            self.content,
            "### Scenario A: Baseline Cost-Optimized Plan",
            "### Scenario B: High-Performance Enterprise Plan",
        )

    def _enterprise_section(self):
        return self._extract_section(
            self.content,
            "### Scenario B: High-Performance Enterprise Plan",
            "## 3. Cost-Optimization Pathways",
        )

    def test_baseline_table_has_expected_row_count(self):
        rows = self._extract_rows(self._baseline_section())
        # 11 component rows + 1 TOTAL row.
        self.assertEqual(len(rows), 12)

    def test_enterprise_table_has_expected_row_count(self):
        rows = self._extract_rows(self._enterprise_section())
        self.assertEqual(len(rows), 12)

    def test_baseline_component_costs_sum_to_stated_total(self):
        rows = self._extract_rows(self._baseline_section())
        *components, total = rows
        component_sum = round(sum(usd for usd, _ in components), 2)
        self.assertAlmostEqual(component_sum, total[0], places=2)

    def test_enterprise_component_costs_sum_to_stated_total(self):
        rows = self._extract_rows(self._enterprise_section())
        *components, total = rows
        component_sum = round(sum(usd for usd, _ in components), 2)
        self.assertAlmostEqual(component_sum, total[0], places=2)

    def test_baseline_myr_values_match_conversion_rate(self):
        rows = self._extract_rows(self._baseline_section())
        for usd, myr in rows:
            expected_myr = round(usd * self.USD_TO_MYR_RATE, 2)
            self.assertAlmostEqual(
                myr, expected_myr, delta=0.01,
                msg=f"${usd} -> RM{myr} does not match rate of 4.50 (expected RM{expected_myr})",
            )

    def test_enterprise_myr_values_match_conversion_rate(self):
        rows = self._extract_rows(self._enterprise_section())
        for usd, myr in rows:
            expected_myr = round(usd * self.USD_TO_MYR_RATE, 2)
            self.assertAlmostEqual(
                myr, expected_myr, delta=0.01,
                msg=f"${usd} -> RM{myr} does not match rate of 4.50 (expected RM{expected_myr})",
            )

    def test_baseline_annual_total_matches_monthly_times_twelve(self):
        match = re.search(
            r"Annual Baseline Operational Spend:\*\*\s*\*\*\$([\d,]+\.\d{2}) USD",
            self.content,
        )
        self.assertIsNotNone(match)
        annual_usd = float(match.group(1).replace(",", ""))

        rows = self._extract_rows(self._baseline_section())
        monthly_total_usd = rows[-1][0]
        self.assertAlmostEqual(annual_usd, round(monthly_total_usd * 12, 2), places=2)

    def test_enterprise_annual_total_matches_monthly_times_twelve(self):
        match = re.search(
            r"Annual Enterprise Operational Spend:\*\*\s*\*\*\$([\d,]+\.\d{2}) USD",
            self.content,
        )
        self.assertIsNotNone(match)
        annual_usd = float(match.group(1).replace(",", ""))

        rows = self._extract_rows(self._enterprise_section())
        monthly_total_usd = rows[-1][0]
        self.assertAlmostEqual(annual_usd, round(monthly_total_usd * 12, 2), places=2)

    def test_enterprise_total_is_higher_than_baseline_total(self):
        """Sanity/regression check: the enterprise plan must always cost
        more than the baseline plan given it uses larger instance sizes."""
        baseline_total = self._extract_rows(self._baseline_section())[-1][0]
        enterprise_total = self._extract_rows(self._enterprise_section())[-1][0]
        self.assertGreater(enterprise_total, baseline_total)


if __name__ == "__main__":
    unittest.main()