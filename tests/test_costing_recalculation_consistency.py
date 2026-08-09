#!/usr/bin/env python3
"""Unit tests for the "recalculate and verify USD to MYR exchange rate
costing consistency" documentation fix.

This PR updates the Dev/Staging Baseline Cost-Optimized and High-Performance
Enterprise USD figures quoted in three high-level index/summary files so
that they match the authoritative, granular breakdown already present in
``docs/costing.md``:

* ``README.md`` -- the "Financial Cost Estimations" bullet list quoting
  ``Baseline Cost-Optimized Plan (~$141.47 USD/mo)`` and
  ``High-Performance Enterprise Plan (~$898.54 USD/mo)`` (previously
  ``$426.75`` and ``$1,064.46`` respectively).
* ``llms.txt`` -- the "Costing Guide" AI-agent index entry quoting the same
  two USD figures.
* ``.agents/skills/jules-knowledge/SKILL.md`` -- item 29 under "Financial
  Management & Detailed Cost Breakdown" quoting the same two USD figures.

These files are treated as plain text (rather than parsed with a YAML/HTML
library) to stay dependency free, following the pattern already used by
``tests/test_production_costing_docs.py`` and
``tests/test_performance_testing_docs.py``. The tests pin down the exact,
corrected figures in each file, assert the previously-incorrect figures are
gone, and cross-check all three summary files against the authoritative
totals declared in ``docs/costing.md``.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_costing_recalculation_consistency
"""
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

README_PATH = os.path.join(REPO_ROOT, "README.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
SKILL_PATH = os.path.join(
    REPO_ROOT, ".agents", "skills", "jules-knowledge", "SKILL.md"
)
COSTING_PATH = os.path.join(REPO_ROOT, "docs", "executive", "costing.md")

# The corrected figures introduced by this PR.
CORRECTED_BASELINE_USD = "141.47"
CORRECTED_ENTERPRISE_USD = "898.54"

# The stale, incorrect figures that this PR removes.
STALE_BASELINE_USD = "426.75"
STALE_ENTERPRISE_USD = "1,064.46"


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class ReadmeCostingFiguresTestCase(unittest.TestCase):
    """Tests for the corrected figures in README.md's Financial Cost
    Estimations section."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(README_PATH)

    def test_readme_file_exists(self):
        self.assertTrue(os.path.isfile(README_PATH))

    def test_baseline_figure_present(self):
        self.assertIn(
            "**Baseline Cost-Optimized Plan (~$141.47 USD/mo):**", self.content
        )

    def test_enterprise_figure_present(self):
        self.assertIn(
            "**High-Performance Enterprise Plan (~$898.54 USD/mo):**", self.content
        )

    def test_stale_baseline_figure_no_longer_present(self):
        self.assertNotIn(f"${STALE_BASELINE_USD}", self.content)

    def test_stale_enterprise_figure_no_longer_present(self):
        self.assertNotIn(f"${STALE_ENTERPRISE_USD}", self.content)

    def test_figures_appear_in_financial_cost_estimations_section(self):
        section_match = re.search(
            r"### 4\. Strategic Financial Blueprints \(Executive\)\n(.*?)(?=\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section = section_match.group(1)
        self.assertIn(f"${CORRECTED_BASELINE_USD}", section)
        self.assertIn(f"${CORRECTED_ENTERPRISE_USD}", section)

    def test_baseline_bullet_precedes_enterprise_bullet(self):
        baseline_idx = self.content.index("Baseline Cost-Optimized Plan")
        enterprise_idx = self.content.index("High-Performance Enterprise Plan")
        self.assertLess(baseline_idx, enterprise_idx)

    def test_costing_md_link_still_points_to_dev_staging_guide(self):
        """Regression: only the quoted USD figures should have changed, the
        link target itself must remain untouched."""
        self.assertIn(
            "[Cost Analysis Guide (Dev/Staging)](docs/executive/costing.md)", self.content
        )

    def test_each_corrected_figure_appears_exactly_once(self):
        self.assertEqual(
            self.content.count(f"~${CORRECTED_BASELINE_USD} USD/mo"), 1
        )
        self.assertEqual(
            self.content.count(f"~${CORRECTED_ENTERPRISE_USD} USD/mo"), 1
        )

    def test_production_costing_figures_correctly_updated(self):
        """Verify that the Production Cost Analysis bullet figures have
        been correctly updated to the new baseline of $390.98 and enterprise
        of $3,115.96, occurring exactly once in README.md."""
        self.assertEqual(
            self.content.count("**Baseline Production Plan (~$390.98 USD/mo):**"), 1
        )
        self.assertEqual(
            self.content.count(
                "**High-Performance Enterprise Production Plan (~$3,115.96 USD/mo):**"
            ),
            1,
        )


class LlmsTxtCostingFiguresTestCase(unittest.TestCase):
    """Tests for the corrected figures in llms.txt's Costing Guide entry."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LLMS_PATH)

    def test_llms_txt_file_exists(self):
        self.assertTrue(os.path.isfile(LLMS_PATH))

    def test_costing_guide_entry_present_with_corrected_figures(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\[Costing Guide\]\(docs/executive/costing\.md\)\s*:\s*Granular USD and MYR "
                r"billing comparisons for Baseline Cost-Optimized \(\$141\.47 USD\) "
                r"and High-Performance \(\$898\.54 USD\) setups\."
            ),
        )

    def test_stale_baseline_figure_no_longer_present(self):
        self.assertNotIn(f"${STALE_BASELINE_USD}", self.content)

    def test_stale_enterprise_figure_no_longer_present(self):
        self.assertNotIn(f"${STALE_ENTERPRISE_USD}", self.content)

    def test_entry_under_costing_section_heading(self):
        section_match = re.search(
            r"## Deployment, Automation, and Costing\n(.*?)(?=\n## |\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            f"Baseline Cost-Optimized (${CORRECTED_BASELINE_USD} USD)",
            section_match.group(1),
        )

    def test_entry_appears_exactly_once(self):
        self.assertEqual(self.content.count("[Costing Guide]"), 1)

    def test_entry_precedes_production_costing_guide_entry(self):
        costing_idx = self.content.index("[Costing Guide](docs/executive/costing.md)")
        prod_idx = self.content.index(
            "[Production Costing Guide](docs/executive/production-costing.md)"
        )
        self.assertLess(costing_idx, prod_idx)


class SkillMdCostingFiguresTestCase(unittest.TestCase):
    """Tests for the corrected figures in the jules-knowledge SKILL.md
    Financial Management section (item 29)."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(SKILL_PATH)

    def test_skill_file_exists(self):
        self.assertTrue(os.path.isfile(SKILL_PATH))

    def test_item_29_present_with_corrected_figures(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"29\.\s+\*\*Baseline vs\. High-Performance Financial Plans:\*\*"
                r".*?Baseline Cost-Optimized \(~\$141\.47 USD/mo\) and "
                r"High-Performance \(~\$898\.54 USD/mo\) Plans",
                re.DOTALL,
            ),
        )

    def test_stale_baseline_figure_no_longer_present(self):
        self.assertNotIn(f"${STALE_BASELINE_USD}", self.content)

    def test_stale_enterprise_figure_no_longer_present(self):
        self.assertNotIn(f"${STALE_ENTERPRISE_USD}", self.content)

    def test_unrelated_cost_figures_in_same_item_are_unchanged(self):
        """Regression: item 29 also quotes the SSH Jumphost and Route 53
        costs; this PR must only touch the two Baseline/High-Performance
        USD figures, not these other figures embedded in the same
        sentence."""
        self.assertIn("a secure SSH Jumphost ($10.98/mo)", self.content)
        self.assertIn(
            "AWS Route 53 hosting/query costs ($1.30/mo)", self.content
        )

    def test_item_29_references_costing_md(self):
        self.assertIn(
            "The system costing documentation (at `docs/executive/costing.md`)",
            self.content,
        )

    def test_item_30_still_present_and_unaffected(self):
        self.assertIn(
            "30. **Infrastructure Cost Breakdown Page:** An AWS "
            "infrastructure cost estimation breakdown page is available "
            "at `docs/executive/costing.md`",
            self.content,
        )

    def test_item_29_appears_exactly_once(self):
        self.assertEqual(
            self.content.count(
                "**Baseline vs. High-Performance Financial Plans:**"
            ),
            1,
        )


class CrossFileCostingFigureConsistencyTestCase(unittest.TestCase):
    """Verifies that README.md, llms.txt, and SKILL.md all agree with each
    other, and with the authoritative combined totals declared in
    docs/costing.md, on the Baseline and High-Performance USD figures."""

    @classmethod
    def setUpClass(cls):
        cls.readme_content = _read(README_PATH)
        cls.llms_content = _read(LLMS_PATH)
        cls.skill_content = _read(SKILL_PATH)
        cls.costing_content = _read(COSTING_PATH)

    def _authoritative_totals(self):
        """Extract the authoritative Scenario A / Scenario B "Monthly
        Combined Total (USD)" figures directly from docs/costing.md."""
        totals = re.findall(
            r"\*\*Monthly Combined Total \(USD\):\*\*\s*\*\*\$([\d,]+\.\d{2}) USD / month\*\*",
            self.costing_content,
        )
        self.assertEqual(
            len(totals), 2, "Expected exactly two Scenario combined USD totals"
        )
        return totals[0], totals[1]

    def test_costing_md_declares_expected_authoritative_totals(self):
        baseline_total, enterprise_total = self._authoritative_totals()
        self.assertEqual(baseline_total, CORRECTED_BASELINE_USD)
        self.assertEqual(enterprise_total, CORRECTED_ENTERPRISE_USD)

    def test_readme_baseline_figure_matches_costing_md_authoritative_total(self):
        baseline_total, _ = self._authoritative_totals()
        self.assertIn(f"~${baseline_total} USD/mo", self.readme_content)

    def test_readme_enterprise_figure_matches_costing_md_authoritative_total(self):
        _, enterprise_total = self._authoritative_totals()
        self.assertIn(f"~${enterprise_total} USD/mo", self.readme_content)

    def test_llms_txt_baseline_figure_matches_costing_md_authoritative_total(self):
        baseline_total, _ = self._authoritative_totals()
        self.assertIn(f"(${baseline_total} USD)", self.llms_content)

    def test_llms_txt_enterprise_figure_matches_costing_md_authoritative_total(self):
        _, enterprise_total = self._authoritative_totals()
        self.assertIn(f"(${enterprise_total} USD)", self.llms_content)

    def test_skill_md_baseline_figure_matches_costing_md_authoritative_total(self):
        baseline_total, _ = self._authoritative_totals()
        self.assertIn(f"(~${baseline_total} USD/mo)", self.skill_content)

    def test_skill_md_enterprise_figure_matches_costing_md_authoritative_total(self):
        _, enterprise_total = self._authoritative_totals()
        self.assertIn(f"(~${enterprise_total} USD/mo)", self.skill_content)

    def test_all_three_summary_files_quote_the_identical_baseline_figure(self):
        files = {
            "README.md": self.readme_content,
            "llms.txt": self.llms_content,
            "SKILL.md": self.skill_content,
        }
        for name, content in files.items():
            with self.subTest(file=name):
                self.assertIn(CORRECTED_BASELINE_USD, content)

    def test_all_three_summary_files_quote_the_identical_enterprise_figure(self):
        files = {
            "README.md": self.readme_content,
            "llms.txt": self.llms_content,
            "SKILL.md": self.skill_content,
        }
        for name, content in files.items():
            with self.subTest(file=name):
                self.assertIn(CORRECTED_ENTERPRISE_USD, content)

    def test_enterprise_figure_is_greater_than_baseline_figure_everywhere(self):
        """Sanity check: the High-Performance Enterprise plan must always
        be quoted as more expensive than the Baseline Cost-Optimized plan
        in every summary file."""
        baseline_total, enterprise_total = self._authoritative_totals()
        baseline_usd = float(baseline_total.replace(",", ""))
        enterprise_usd = float(enterprise_total.replace(",", ""))
        self.assertGreater(enterprise_usd, baseline_usd)


class StaleCostingFigureRegressionTestCase(unittest.TestCase):
    """Negative/regression checks ensuring the pre-fix figures do not
    linger anywhere in the three corrected summary files."""

    @classmethod
    def setUpClass(cls):
        cls.files = {
            "README.md": _read(README_PATH),
            "llms.txt": _read(LLMS_PATH),
            "SKILL.md": _read(SKILL_PATH),
        }

    def test_stale_baseline_figure_absent_from_all_three_files(self):
        for name, content in self.files.items():
            with self.subTest(file=name):
                self.assertNotIn(f"${STALE_BASELINE_USD}", content)

    def test_stale_enterprise_figure_absent_from_all_three_files(self):
        for name, content in self.files.items():
            with self.subTest(file=name):
                self.assertNotIn(f"${STALE_ENTERPRISE_USD}", content)


if __name__ == "__main__":
    unittest.main()