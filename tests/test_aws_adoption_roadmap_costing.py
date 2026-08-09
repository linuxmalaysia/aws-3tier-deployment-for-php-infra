#!/usr/bin/env python3
"""Unit tests for the recalculated Phase 2 and Phase 4 financial run-rate
figures in ``docs/executive/aws-adoption-roadmap.md``.

This PR updates the Phase 2 (Omnichannel/CRM Staging) and Phase 4
(High-Performance Enterprise Sovereignty Scaling) monthly cost figures to
match the rewritten Production Costing model in
``docs/executive/production-costing.md``:

* Phase 2 run-rate: ``$418.60`` -> ``$462.09`` USD/mo (RM 1,883.70 -> RM
  2,079.41 MYR/mo), in both the ASCII timeline diagram and the narrative
  "Financial Model Run-Rate" bullet.
* Phase 4 run-rate: ``$1,037.73+`` -> ``$3,115.96+`` USD/mo (up to
  ``$3,808.88`` at the highest concurrency tier), in both the ASCII timeline
  diagram and the narrative bullet.

Phase 1 (~$141.47 USD/mo) and Phase 3 (~$898.54 USD/mo) are distinct,
unrelated cost models that must remain untouched by this PR.

These files are treated as plain text (rather than parsed with a YAML/HTML
library) to stay dependency free, following the pattern already used by
other doc-consistency test modules in this repository.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_aws_adoption_roadmap_costing
"""
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROADMAP_PATH = os.path.join(REPO_ROOT, "docs", "executive", "aws-adoption-roadmap.md")
PROD_COSTING_PATH = os.path.join(REPO_ROOT, "docs", "executive", "production-costing.md")

# Figures introduced/confirmed by this PR.
PHASE2_USD = "462.09"
PHASE2_MYR = "2,079.41"
PHASE4_USD = "3,115.96"
PHASE4_MYR = "14,021.82"
PHASE4_MAX_USD = "3,808.88"
PHASE4_MAX_MYR = "17,139.96"

# Unrelated, pre-existing figures that must remain unchanged by this PR.
PHASE1_USD = "141.47"
PHASE3_USD = "898.54"

# Stale figures that this PR removes.
STALE_PHASE2_USD = "418.60"
STALE_PHASE4_USD = "1,037.73"


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class RoadmapFileFrontMatterUnaffectedTestCase(unittest.TestCase):
    """Regression: only body figures changed; front matter is untouched."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ROADMAP_PATH)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(ROADMAP_PATH))

    def test_front_matter_timestamp_unchanged(self):
        self.assertIn("timestamp: 2026-08-05T22:20:36+08:00", self.content)

    def test_title_unchanged(self):
        self.assertIn(
            'title: "AWS Sovereign Infrastructure Adoption Roadmap"', self.content
        )

    def test_top_level_heading_unchanged(self):
        self.assertIn(
            "# AWS Sovereign Infrastructure Adoption Roadmap & DR Maturation Timeline",
            self.content,
        )


class TimelineDiagramCostFiguresTestCase(unittest.TestCase):
    """Tests for the ASCII timeline diagram's per-phase cost annotations."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ROADMAP_PATH)
        diagram_match = re.search(
            r"```text\n(.*?)\n```", cls.content, re.DOTALL
        )
        assert diagram_match is not None
        cls.diagram = diagram_match.group(1)

    def test_diagram_present(self):
        self.assertIn("AWS ADOPTION & DR MATURATION CURVE", self.diagram)

    def test_phase1_cost_unchanged(self):
        self.assertIn(f"~${PHASE1_USD} USD/mo", self.diagram)

    def test_phase2_cost_updated(self):
        self.assertIn(f"~${PHASE2_USD} USD/mo", self.diagram)

    def test_phase3_cost_unchanged(self):
        self.assertIn(f"~${PHASE3_USD} USD/mo", self.diagram)

    def test_phase4_cost_updated(self):
        self.assertIn(f"~${PHASE4_USD}+ USD/mo", self.diagram)

    def test_stale_phase2_cost_absent(self):
        self.assertNotIn(STALE_PHASE2_USD, self.diagram)

    def test_stale_phase4_cost_absent(self):
        self.assertNotIn(STALE_PHASE4_USD, self.diagram)

    def test_phase_costs_appear_in_ascending_order_left_to_right(self):
        """Regression: the 4 phase cost annotations must appear on a single
        line, in phase order, since the diagram is a left-to-right timeline."""
        cost_line = next(
            line for line in self.diagram.splitlines() if "- Cost:" in line
        )
        p1_idx = cost_line.index(f"${PHASE1_USD}")
        p2_idx = cost_line.index(f"${PHASE2_USD}")
        p3_idx = cost_line.index(f"${PHASE3_USD}")
        p4_idx = cost_line.index(f"${PHASE4_USD}")
        self.assertLess(p1_idx, p2_idx)
        self.assertLess(p2_idx, p3_idx)
        self.assertLess(p3_idx, p4_idx)


class PhaseNarrativeFinancialRunRateTestCase(unittest.TestCase):
    """Tests for the narrative 'Financial Model Run-Rate' bullets under each
    phase's detailed subsection."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ROADMAP_PATH)

    def test_phase1_run_rate_unchanged(self):
        self.assertIn(
            f"**Financial Model Run-Rate:** **~${PHASE1_USD} USD/mo** (RM 636.62 MYR/mo).",
            self.content,
        )

    def test_phase2_run_rate_updated(self):
        self.assertIn(
            f"**Financial Model Run-Rate:** **~${PHASE2_USD} USD/mo** (RM {PHASE2_MYR} MYR/mo).",
            self.content,
        )

    def test_phase3_run_rate_unchanged(self):
        """Regression: Phase 3's run-rate is a distinct cost model
        (non-DRS baseline subtotal) and must not be touched by this PR."""
        self.assertIn(f"**~${PHASE3_USD} USD/mo** (RM 4,043.43 MYR/mo)", self.content)

    def test_phase4_run_rate_updated(self):
        self.assertIn(
            f"**Financial Model Run-Rate:** **~${PHASE4_USD} USD/mo** (RM {PHASE4_MYR} MYR/mo) "
            f"to **~${PHASE4_MAX_USD} USD/mo** (RM {PHASE4_MAX_MYR} MYR/mo) based on concurrency tiers.",
            self.content,
        )

    def test_phase_headings_appear_in_expected_order(self):
        idx1 = self.content.index("### Phase 1: Foundation")
        idx2 = self.content.index("### Phase 2: Omnichannel Integration")
        idx3 = self.content.index("### Phase 3: Omnichannel & CRM Go-Live")
        idx4 = self.content.index("### Phase 4: High-Performance Enterprise")
        self.assertLess(idx1, idx2)
        self.assertLess(idx2, idx3)
        self.assertLess(idx3, idx4)

    def test_each_phase_has_exactly_one_run_rate_bullet(self):
        for heading, next_heading in [
            ("### Phase 1: Foundation", "### Phase 2: Omnichannel Integration"),
            ("### Phase 2: Omnichannel Integration", "### Phase 3: Omnichannel & CRM Go-Live"),
            ("### Phase 3: Omnichannel & CRM Go-Live", "### Phase 4: High-Performance Enterprise"),
        ]:
            with self.subTest(heading=heading):
                start = self.content.index(heading)
                end = self.content.index(next_heading)
                section = self.content[start:end]
                self.assertEqual(
                    section.count("**Financial Model Run-Rate:**"), 1
                )

    def test_stale_phase2_figure_absent(self):
        self.assertNotIn(f"${STALE_PHASE2_USD}", self.content)

    def test_stale_phase4_figure_absent(self):
        self.assertNotIn(f"${STALE_PHASE4_USD}", self.content)


class RoadmapCrossFileConsistencyWithProductionCostingTestCase(unittest.TestCase):
    """Verifies the Phase 2 and Phase 4 figures match the authoritative
    totals declared in docs/executive/production-costing.md."""

    @classmethod
    def setUpClass(cls):
        cls.roadmap_content = _read(ROADMAP_PATH)
        cls.costing_content = _read(PROD_COSTING_PATH)

    def _authoritative_totals(self):
        baseline_match = re.search(
            r"\*\*TOTAL \(Baseline\)\*\*.*?\*\*\$([\d,]+\.\d{2})\*\*.*?\*\*RM ([\d,]+\.\d{2})\*\*",
            self.costing_content,
        )
        enterprise_match = re.search(
            r"\*\*TOTAL \(Enterprise\)\*\*.*?\*\*\$([\d,]+\.\d{2})\*\*.*?\*\*RM ([\d,]+\.\d{2})\*\*",
            self.costing_content,
        )
        self.assertIsNotNone(baseline_match, "Expected a Baseline TOTAL row")
        self.assertIsNotNone(enterprise_match, "Expected an Enterprise TOTAL row")
        return baseline_match.groups(), enterprise_match.groups()

    def test_production_costing_declares_expected_totals(self):
        (baseline_usd, baseline_myr), (enterprise_usd, enterprise_myr) = (
            self._authoritative_totals()
        )
        self.assertEqual(baseline_usd, PHASE2_USD)
        self.assertEqual(baseline_myr, PHASE2_MYR)
        self.assertEqual(enterprise_usd, PHASE4_USD)
        self.assertEqual(enterprise_myr, PHASE4_MYR)

    def test_roadmap_phase2_matches_production_costing_baseline_total(self):
        (baseline_usd, baseline_myr), _ = self._authoritative_totals()
        self.assertIn(f"~${baseline_usd} USD/mo", self.roadmap_content)
        self.assertIn(f"RM {baseline_myr} MYR/mo", self.roadmap_content)

    def test_roadmap_phase4_matches_production_costing_enterprise_total(self):
        _, (enterprise_usd, enterprise_myr) = self._authoritative_totals()
        self.assertIn(f"~${enterprise_usd} USD/mo", self.roadmap_content)
        self.assertIn(f"RM {enterprise_myr} MYR/mo", self.roadmap_content)

    def test_phase4_figure_is_greater_than_phase2_figure(self):
        phase2_usd = float(PHASE2_USD.replace(",", ""))
        phase4_usd = float(PHASE4_USD.replace(",", ""))
        self.assertGreater(phase4_usd, phase2_usd)


if __name__ == "__main__":
    unittest.main()