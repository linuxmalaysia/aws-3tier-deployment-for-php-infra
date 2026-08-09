#!/usr/bin/env python3
"""Unit tests for the recalculated 500 VU tier costing figures in
``docs/engineering/performance-testing.md``.

This PR updates the 500 VU ("Cost-Optimized Staged Model") tier's monthly
total from ``$418.60 USD`` (RM 1,883.70 MYR) to ``$462.09 USD`` (RM 2,079.41
MYR), driven entirely by a change to the "Operational Services (CloudWatch,
Secrets Manager, Backup)" line item, which increases from ``$15.04 USD``
(RM 67.68 MYR) to ``$58.53 USD`` (RM 263.39 MYR). The change is reflected in
both the tier's entry in the "Multi-VU Performance Sizing and Cost Matrix"
table and its detailed "Sizing & Line-Item Costing" breakdown. All other 500
VU line items, and all other VU tiers, are unaffected.

These files are treated as plain text (rather than parsed with a YAML/HTML
library) to stay dependency free, following the pattern already used by
``tests/test_performance_testing_docs.py``.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_performance_testing_500vu_costing
"""
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PERF_TESTING_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "performance-testing.md")

NEW_TOTAL_USD = "462.09"
NEW_TOTAL_MYR = "2,079.41"
NEW_OPS_USD = "58.53"
NEW_OPS_MYR = "263.39"

STALE_TOTAL_USD = "418.60"
STALE_TOTAL_MYR = "1,883.70"
STALE_OPS_USD = "15.04"
STALE_OPS_MYR = "67.68"

# Other VU tiers' totals, which must be unaffected by this PR.
OTHER_TIER_TOTALS_USD = ["141.47", "1,236.03", "1,948.12", "3,808.88"]

USD_TO_MYR_RATE = 4.50


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class FiveHundredVuMatrixRowTestCase(unittest.TestCase):
    """Tests for the 500 VU row in the Multi-VU Performance Sizing and Cost
    Matrix table."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_TESTING_PATH)
        row_match = re.search(r"^\|\s*\*\*500 VU\*\*.*$", cls.content, re.MULTILINE)
        assert row_match is not None
        cls.row = row_match.group(0)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(PERF_TESTING_PATH))

    def test_matrix_row_present_exactly_once(self):
        self.assertEqual(
            len(re.findall(r"^\|\s*\*\*500 VU\*\*.*$", self.content, re.MULTILINE)),
            1,
        )

    def test_matrix_row_shows_updated_usd_total(self):
        self.assertIn(f"**${NEW_TOTAL_USD} USD**", self.row)

    def test_matrix_row_shows_updated_myr_total(self):
        self.assertIn(f"**RM {NEW_TOTAL_MYR} MYR**", self.row)

    def test_matrix_row_does_not_show_stale_total(self):
        self.assertNotIn(STALE_TOTAL_USD, self.row)
        self.assertNotIn(STALE_TOTAL_MYR, self.row)

    def test_matrix_row_sizing_specs_unchanged(self):
        """Regression: only the cost columns changed; compute/DB/cache
        sizing specs for the 500 VU tier are untouched by this PR."""
        self.assertIn("2x `t4g.medium` (ASG)", self.row)
        self.assertIn("`db.m6g.large`", self.row)
        self.assertIn("`cache.t4g.micro`", self.row)
        self.assertIn("Cost-Optimized Staged Model", self.row)

    def test_other_tier_rows_unaffected(self):
        for total in OTHER_TIER_TOTALS_USD:
            with self.subTest(total=total):
                self.assertIn(f"**${total} USD**", self.content)


class FiveHundredVuDetailSectionTestCase(unittest.TestCase):
    """Tests for the 500 VU tier's detailed line-item costing section."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PERF_TESTING_PATH)
        section_match = re.search(
            r"### 🚀 500 VU — Cost-Optimized Staged Model\n(.*?)\n---",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None
        cls.section = section_match.group(1)

    def test_section_present(self):
        self.assertIn("#### B. Sizing & Line-Item Costing (Monthly)", self.section)

    def test_operational_services_line_updated(self):
        self.assertIn(
            f"**Operational Services (CloudWatch, Secrets Manager, Backup):** "
            f"${NEW_OPS_USD} USD (RM {NEW_OPS_MYR} MYR)",
            self.section,
        )

    def test_operational_services_stale_value_absent(self):
        self.assertNotIn(f"${STALE_OPS_USD} USD (RM {STALE_OPS_MYR} MYR)", self.section)

    def test_total_monthly_cost_line_updated(self):
        self.assertIn(
            f"**Total Monthly Cost:** **${NEW_TOTAL_USD} USD** / **RM {NEW_TOTAL_MYR} MYR**",
            self.section,
        )

    def test_total_monthly_cost_stale_value_absent(self):
        self.assertNotIn(STALE_TOTAL_USD, self.section)
        self.assertNotIn(STALE_TOTAL_MYR, self.section)

    def test_other_line_items_unchanged(self):
        """Regression: only the Operational Services and Total lines should
        have changed; all other 500 VU line items remain as-is."""
        unchanged_lines = [
            "**Compute Tier (ASG):** $49.06 USD (RM 220.77 MYR) (2x t4g.medium nodes)",
            "**Compute SSD Storage (ASG EBS):** $4.80 USD (RM 21.60 MYR)",
            "**Database Tier (RDS Multi-AZ - db.m6g.large):** $221.92 USD (RM 998.64 MYR)",
            "**Database Storage (RDS GP3 Multi-AZ):** $11.50 USD (RM 51.75 MYR)",
            "**Cache Store Tier (Valkey - 1x cache.t4g.micro):** $9.34 USD (RM 42.03 MYR)",
            "**Load Balancing (ALB):** $28.11 USD (RM 126.50 MYR)",
            "**WAFv2 regional ACL:** $8.60 USD (RM 38.70 MYR)",
            "**NAT Gateway (Secure Egress):** $35.10 USD (RM 157.95 MYR)",
            "**Shared Storage (EFS & S3):** $5.80 USD (RM 26.10 MYR)",
            "**Bastion / Standalone (2x t4g.medium):** $29.33 USD (RM 131.98 MYR)",
        ]
        for line in unchanged_lines:
            with self.subTest(line=line):
                self.assertIn(line, self.section)

    def test_performance_insights_subsection_unchanged(self):
        self.assertIn("#### C. Performance Insights & Bottlenecks", self.section)
        self.assertIn(
            "Standalone Valkey and single NAT Gateway remain non-HA failover "
            "single points of failure (SPOFs).",
            self.section,
        )

    def test_line_items_sum_to_new_total(self):
        """Numeric consistency: all USD line items in the 500 VU costing
        section must sum to the new total of $462.09."""
        usd_values = [
            float(v.replace(",", ""))
            for v in re.findall(r"\$([\d,]+\.\d{2}) USD", self.section)
        ]
        # Exclude the total itself from the summed line items.
        total = float(NEW_TOTAL_USD)
        line_items = [v for v in usd_values if v != total]
        self.assertAlmostEqual(sum(line_items), total, places=2)

    def test_myr_values_match_conversion_rate(self):
        pairs = re.findall(
            r"\$([\d,]+\.\d{2}) USD \(RM ([\d,]+\.\d{2}) MYR\)", self.section
        )
        self.assertGreater(len(pairs), 0)
        for usd_str, myr_str in pairs:
            with self.subTest(usd=usd_str, myr=myr_str):
                usd = float(usd_str.replace(",", ""))
                myr = float(myr_str.replace(",", ""))
                self.assertAlmostEqual(myr, usd * USD_TO_MYR_RATE, delta=0.02)


if __name__ == "__main__":
    unittest.main()