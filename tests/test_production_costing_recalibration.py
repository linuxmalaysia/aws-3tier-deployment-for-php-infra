#!/usr/bin/env python3
"""Unit tests for the "Sovereign Enterprise Production Costing Recalibration"
documentation update.

This PR performs a wholesale rewrite of
``docs/executive/production-costing.md``, replacing the previous 9-ASG/3-ALB
narrative (single unified compute sizing, `db.m6g.large`/`db.m6g.xlarge`
PostgreSQL-only database tier, single-node Valkey cache) with a granular,
line-item cost model built around:

* Nine explicitly-named functional Auto Scaling Groups running a combined
  20 active EC2 instances (`t4g.micro` Baseline / `t4g.medium` Enterprise).
* Dual managed relational database engines (MariaDB Multi-AZ + Single-AZ
  Read Replica, and a separate Multi-AZ PostgreSQL instance).
* A two-tier ElastiCache for Valkey topology (a single-node API cache plus
  a Multi-AZ session replication group, 3-node `cache.r6g.2xlarge` under the
  Enterprise plan).
* Three explicitly-named Application Load Balancers.
* Recalculated Scenario A / Scenario B totals of **$462.09 USD** and
  **$3,115.96 USD** respectively (up from the previous $418.60 / $1,037.73
  and $1,009.20 figures).

This PR also propagates the two new headline totals into README.md,
docs/engineering/performance-analysis.md, docs/engineering/performance-testing.md,
and docs/executive/aws-adoption-roadmap.md.

These files are treated as plain text (rather than parsed with a YAML/HTML
library) to stay dependency free, following the pattern already used by
``tests/test_production_costing_docs.py``.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_production_costing_recalibration
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

README_PATH = os.path.join(REPO_ROOT, "README.md")
PROD_COSTING_PATH = os.path.join(REPO_ROOT, "docs", "executive", "production-costing.md")
PERF_ANALYSIS_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "performance-analysis.md")
PERF_TESTING_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "performance-testing.md")
ROADMAP_PATH = os.path.join(REPO_ROOT, "docs", "executive", "aws-adoption-roadmap.md")

NEW_BASELINE_TOTAL_USD = "462.09"
NEW_ENTERPRISE_TOTAL_USD = "3,115.96"
NEW_BASELINE_TOTAL_MYR = "2,079.41"
NEW_ENTERPRISE_TOTAL_MYR = "14,021.82"

# Stale figures that must no longer appear anywhere in the recalibrated doc.
STALE_FIGURES = ["418.60", "1,037.73", "1,009.20", "5,023.20", "12,110.40"]

USD_TO_MYR_RATE = 4.50


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class ProductionCostingFrontMatterTestCase(unittest.TestCase):
    """Tests for the updated OKF front matter timestamp."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PROD_COSTING_PATH)
        stripped = cls.content.lstrip()
        parts = stripped.split("---", 2)
        cls.front_matter_text = parts[1]
        cls.body_text = parts[2]
        cls.front_matter = prepare_docs.parse_yaml_front_matter(cls.front_matter_text)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(PROD_COSTING_PATH))

    def test_timestamp_updated_to_expected_value(self):
        self.assertEqual(self.front_matter["timestamp"], "2026-08-07T15:00:00+08:00")

    def test_stale_timestamp_no_longer_present(self):
        self.assertNotIn("2026-08-05T22:20:36+08:00", self.content)

    def test_okf_version_unchanged(self):
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_title_unchanged(self):
        self.assertEqual(
            self.front_matter["title"], "Production Infrastructure Costing Analysis"
        )

    def test_type_matches_prepare_docs_inference(self):
        inferred_type = prepare_docs.infer_okf_type(
            "docs/executive/production-costing.md"
        )
        self.assertEqual(self.front_matter["type"], inferred_type)


class ProductionCostingIntroTestCase(unittest.TestCase):
    """Tests for the rewritten introductory paragraphs."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PROD_COSTING_PATH)

    def test_stale_dev_staging_cross_reference_note_removed(self):
        """Regression: the old note pointing at the separate 'developer-focused,
        staging and SaaS-alternative' costing.html guide has been replaced."""
        self.assertNotIn(
            "For our developer-focused, staging and SaaS-alternative environment costs",
            self.content,
        )
        self.assertNotIn("Sovereign Enterprise Production Cost Model**", self.content)

    def test_new_intro_paragraph_present(self):
        self.assertIn(
            "This document provides a highly granular, transparent, and comprehensive "
            "breakdown of the monthly operating costs associated with deploying our "
            "**Enterprise Multi-AZ PHP Secure 3-Tier Web Application** on AWS in the "
            "**Asia Pacific (Malaysia) Region (`ap-southeast-5`)**.",
            self.content,
        )

    def test_new_second_paragraph_describes_target_architecture(self):
        self.assertIn(
            "The target architecture represents an enterprise-scale system mapped "
            "directly from production parameters", self.content
        )
        self.assertIn("nine (9) Auto Scaling Groups (ASGs)", self.content)
        self.assertIn("three (3) Application Load Balancers (ALBs)", self.content)
        self.assertIn("hybrid/DR components", self.content)

    def test_conversion_rate_statement_unchanged(self):
        self.assertIn("1 USD = 4.50 MYR", self.content)

    def test_intro_precedes_anonymization_section(self):
        intro_idx = self.content.index("This document provides a highly granular")
        anon_idx = self.content.index("## Anonymization and Corporate Mapping")
        self.assertLess(intro_idx, anon_idx)


class ProductionCostingSystemInventorySectionTestCase(unittest.TestCase):
    """Tests for the new '## 1. System Inventory & Specifications' section
    and its five lettered subsections (A-E)."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PROD_COSTING_PATH)
        section_match = re.search(
            r"## 1\. System Inventory & Specifications\n(.*?)\n---\n\n## 2\. Infrastructure Cost Models",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None
        cls.section = section_match.group(1)

    def test_section_heading_present(self):
        self.assertIn("## 1. System Inventory & Specifications", self.content)

    def test_all_five_subsections_present_in_order(self):
        subsections = [
            "### A. Compute & Auto Scaling (ASGs)",
            "### B. Relational Databases (Amazon RDS)",
            "### C. Performance & Caching (ElastiCache for Valkey)",
            "### D. Storage Tier",
            "### E. Load Balancing & Security Gateways",
        ]
        indices = [self.content.index(s) for s in subsections]
        self.assertEqual(indices, sorted(indices))

    def test_asg_inventory_lists_nine_named_groups(self):
        expected_asgs = [
            "secure-app-core-api-asg",
            "secure-app-billing-api-asg",
            "secure-app-checkout-processing-asg",
            "secure-app-portal-frontend-asg",
            "secure-app-analytics-dashboard-asg",
            "secure-app-parking-api-asg",
            "secure-app-gis-mapping-asg",
            "secure-app-integration-gateway-asg",
            "secure-app-staging-checkout-asg",
        ]
        for asg in expected_asgs:
            with self.subTest(asg=asg):
                self.assertIn(f"`{asg}`", self.section)

    def test_asg_list_has_exactly_nine_numbered_entries(self):
        asg_items = re.findall(
            r"^\d+\.\s+\*\*`secure-app-[\w-]+-asg`\*\*", self.section, re.MULTILINE
        )
        self.assertEqual(len(asg_items), 9)

    def test_states_twenty_active_ec2_instances(self):
        self.assertIn(
            "the system runs exactly **20 active EC2 compute instances**",
            self.section,
        )

    def test_compute_sizing_specs_for_both_plans(self):
        self.assertIn("`t4g.medium`", self.section)
        self.assertIn("30GB gp3 SSD", self.section)
        self.assertIn("`t4g.micro`", self.section)
        self.assertIn("15GB gp3 SSD", self.section)

    def test_rds_section_describes_dual_engines(self):
        self.assertIn("**MariaDB Engine:**", self.section)
        self.assertIn("**PostgreSQL Engine:**", self.section)
        self.assertIn("Single-AZ Read Replica", self.section)
        self.assertIn("Multi-AZ configuration", self.section)

    def test_caching_section_describes_two_valkey_services(self):
        self.assertIn("**Valkey API Caching Service:**", self.section)
        self.assertIn("**Valkey Core Session Service:**", self.section)
        self.assertIn("**3-node**", self.section)
        self.assertIn("`cache.r6g.2xlarge`", self.section)

    def test_storage_tier_describes_efs_and_s3(self):
        self.assertIn("1.29 TiB total capacity", self.section)
        self.assertIn("44.70 GiB Standard", self.section)
        self.assertIn("410.26 GiB Infrequent Access", self.section)
        self.assertIn("869.38 GiB Archive Storage", self.section)
        self.assertIn("10 buckets", self.section)
        self.assertIn("14.7 GB", self.section)
        self.assertIn("2.7 Million objects", self.section)

    def test_efs_component_gib_breakdown_sums_correctly(self):
        """Numeric consistency: Standard + Infrequent Access GiB should equal
        the '454.96 GiB' figure quoted later in the Cost-Optimization
        Pathways section as eligible for lifecycle transition."""
        standard = 44.70
        infrequent_access = 410.26
        self.assertAlmostEqual(standard + infrequent_access, 454.96, places=2)

    def test_load_balancing_section_lists_three_named_albs(self):
        expected_albs = [
            "secure-app-public-alb",
            "secure-app-checkout-alb",
            "secure-app-internal-alb",
        ]
        for alb in expected_albs:
            with self.subTest(alb=alb):
                self.assertIn(f"`{alb}`", self.section)
        alb_items = re.findall(
            r"^\d+\.\s+`secure-app-[\w-]+-alb`", self.section, re.MULTILINE
        )
        self.assertEqual(len(alb_items), 3)

    def test_load_balancing_section_mentions_wafv2(self):
        self.assertIn("AWS WAFv2 Web ACL", self.section)
        self.assertIn("Cyberjaya dev office", self.section)


class ProductionCostingInfrastructureCostModelsSectionTestCase(unittest.TestCase):
    """Tests for the new '## 2. Infrastructure Cost Models' assumptions
    block that replaced the old 'Cost Breakdown Assumptions and Pricing
    Citations' section."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PROD_COSTING_PATH)

    def test_section_heading_present(self):
        self.assertIn("## 2. Infrastructure Cost Models", self.content)

    def test_old_pricing_citations_heading_removed(self):
        self.assertNotIn(
            "## Cost Breakdown Assumptions and Pricing Citations", self.content
        )
        self.assertNotIn("## Infrastructure Assets Inventory", self.content)
        self.assertNotIn("## Architectural Cost Scenarios", self.content)

    def test_price_snapshot_and_fx_dates_stated(self):
        self.assertIn("**AWS Price Snapshot Date:** April 25, 2026", self.content)
        self.assertIn("**FX Effective Date:** April 25, 2026", self.content)

    def test_tax_treatment_stated(self):
        self.assertIn("8.00% SST", self.content)

    def test_pricing_basis_stated(self):
        self.assertIn("730 operating hours per month", self.content)

    def test_dr_hybrid_charges_exclusion_stated(self):
        self.assertIn(
            "**DR & Hybrid Connect Charges:** Excluded from the baseline and "
            "enterprise annual totals below",
            self.content,
        )

    def test_section_precedes_scenario_a(self):
        section_idx = self.content.index("## 2. Infrastructure Cost Models")
        scenario_a_idx = self.content.index("### Scenario A: Baseline Cost-Optimized Plan")
        self.assertLess(section_idx, scenario_a_idx)


class ProductionCostingTableColumnHeaderTestCase(unittest.TestCase):
    """Regression tests for the renamed cost-table column header: the old
    'Hourly / Unit Rate' column was replaced with 'Driver Qty / Rate' to
    accommodate multi-instance / combined-rate driver descriptions."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PROD_COSTING_PATH)

    def test_old_column_header_removed(self):
        self.assertNotIn("Hourly / Unit Rate", self.content)

    def test_new_column_header_present(self):
        self.assertEqual(self.content.count("Driver Qty / Rate"), 2)

    def test_new_header_appears_in_both_scenario_tables(self):
        matches = re.findall(
            r"\| Component / Layer \| AWS Service Details \| Sizing Spec \| "
            r"Driver Qty / Rate \| Monthly Cost \(USD\) \| Monthly Cost \(MYR\) \|",
            self.content,
        )
        self.assertEqual(len(matches), 2)


class ProductionCostingNewHeadlineFiguresTestCase(unittest.TestCase):
    """Pinned regression tests for the recalculated headline totals
    introduced by this PR."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PROD_COSTING_PATH)

    def test_baseline_total_present(self):
        self.assertIn(
            f"**TOTAL (Baseline)** | **Combined monthly operational spend** | | "
            f"**Sum of all items above** | **${NEW_BASELINE_TOTAL_USD}** | "
            f"**RM {NEW_BASELINE_TOTAL_MYR}** |",
            self.content,
        )

    def test_enterprise_total_present(self):
        self.assertIn(
            f"**TOTAL (Enterprise)** | **Combined monthly operational spend** | | "
            f"**Sum of all items above** | **${NEW_ENTERPRISE_TOTAL_USD}** | "
            f"**RM {NEW_ENTERPRISE_TOTAL_MYR}** |",
            self.content,
        )

    def test_annual_baseline_spend_present(self):
        self.assertIn(
            "**Annual Baseline Operational Spend:** **$5,545.08 USD / year** "
            "(RM 24,952.86 MYR / year)",
            self.content,
        )

    def test_annual_enterprise_spend_present(self):
        self.assertIn(
            "**Annual Enterprise Operational Spend:** **$37,391.52 USD / year** "
            "(RM 168,261.84 MYR / year)",
            self.content,
        )

    def test_annual_baseline_equals_monthly_times_twelve(self):
        monthly = float(NEW_BASELINE_TOTAL_USD.replace(",", ""))
        self.assertAlmostEqual(round(monthly * 12, 2), 5545.08, places=2)

    def test_annual_enterprise_equals_monthly_times_twelve(self):
        monthly = float(NEW_ENTERPRISE_TOTAL_USD.replace(",", ""))
        self.assertAlmostEqual(round(monthly * 12, 2), 37391.52, places=2)

    def test_stale_figures_are_absent(self):
        for stale in STALE_FIGURES:
            with self.subTest(stale=stale):
                self.assertNotIn(stale, self.content)

    def test_enterprise_total_exceeds_baseline_total(self):
        baseline = float(NEW_BASELINE_TOTAL_USD.replace(",", ""))
        enterprise = float(NEW_ENTERPRISE_TOTAL_USD.replace(",", ""))
        self.assertGreater(enterprise, baseline)


class ProductionCostingScenarioLineItemDriverColumnTestCase(unittest.TestCase):
    """Tests validating the new 'Driver Qty / Rate' cell content describes
    the arithmetic actually used to compute each line item's USD figure."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PROD_COSTING_PATH)

    def _extract_scenario(self, start, end):
        match = re.search(re.escape(start) + r"(.*?)" + re.escape(end), self.content, re.DOTALL)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_baseline_compute_row_driver_matches_stated_cost(self):
        section = self._extract_scenario(
            "### Scenario A: Baseline Cost-Optimized Plan",
            "### Scenario B: High-Performance Enterprise Plan",
        )
        self.assertIn(
            "20 * $0.0084/hr * 730 hrs", section
        )
        computed = round(20 * 0.0084 * 730, 2)
        self.assertAlmostEqual(computed, 122.64, places=2)
        self.assertIn("$122.64", section)

    def test_enterprise_compute_row_driver_matches_stated_cost(self):
        section = self._extract_scenario(
            "### Scenario B: High-Performance Enterprise Plan",
            "## 3. Cost-Optimization Pathways",
        )
        self.assertIn("20 * $0.0336/hr * 730 hrs", section)
        computed = round(20 * 0.0336 * 730, 2)
        self.assertAlmostEqual(computed, 490.56, places=2)
        self.assertIn("$490.56", section)

    def test_enterprise_database_row_driver_matches_stated_cost(self):
        section = self._extract_scenario(
            "### Scenario B: High-Performance Enterprise Plan",
            "## 3. Cost-Optimization Pathways",
        )
        # 2x Multi-AZ instances at $0.608/hr plus 1x Single-AZ at $0.304/hr.
        computed = round((2 * 0.608 + 1 * 0.304) * 730, 2)
        self.assertAlmostEqual(computed, 1109.60, places=2)
        self.assertIn("$1,109.60", section)


class ProductionCostingCostOptimizationPathwaysRewriteTestCase(unittest.TestCase):
    """Tests for the rewritten '## 3. Cost-Optimization Pathways (Day-2
    Operations)' section, which now targets the high-performance/enterprise
    setup with RI, Savings Plan, and EFS lifecycle recommendations."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(PROD_COSTING_PATH)
        section_match = re.search(
            r"## 3\. Cost-Optimization Pathways \(Day-2 Operations\)\n(.*)\Z",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None
        cls.section = section_match.group(1)

    def test_section_heading_present(self):
        self.assertIn(
            "## 3. Cost-Optimization Pathways (Day-2 Operations)", self.content
        )

    def test_intro_targets_high_performance_setup(self):
        self.assertIn(
            "To achieve maximum efficiency on the high-performance setup",
            self.section,
        )

    def test_rds_reserved_instance_recommendation(self):
        self.assertIn("**RDS Reserved Instances (RI):**", self.section)
        self.assertIn("`db.m6g.xlarge`", self.section)
        self.assertIn("33% savings", self.section)
        self.assertIn("~$366.17/month", self.section)

    def test_compute_savings_plan_recommendation(self):
        self.assertIn("**Compute Savings Plans:**", self.section)
        self.assertIn("active 20 ASG instances", self.section)
        self.assertIn("25%", self.section)
        self.assertIn("~$136.10/month", self.section)

    def test_efs_lifecycle_management_recommendation(self):
        self.assertIn("**EFS Lifecycle Management:**", self.section)
        self.assertIn("1.29 TiB", self.section)
        self.assertIn("869.38 GiB", self.section)
        self.assertIn("**454.96 GiB**", self.section)
        self.assertIn("`AFTER_90_DAYS`", self.section)
        self.assertIn("$0.30/GB to $0.01/GB-month", self.section)
        self.assertIn("**$82.50 USD / month**", self.section)
        self.assertIn("(RM 371.25 MYR / month)", self.section)

    def test_efs_saving_myr_conversion_is_correct(self):
        usd_saving = 82.50
        expected_myr = round(usd_saving * USD_TO_MYR_RATE, 2)
        self.assertAlmostEqual(expected_myr, 371.25, places=2)

    def test_recommendations_are_numbered_one_through_three(self):
        items = re.findall(r"^\d+\.\s+\*\*", self.section, re.MULTILINE)
        self.assertEqual(len(items), 3)

    def test_stale_day2_operations_bullets_removed(self):
        """Regression: the previous version's AWS Savings Plans & Reserved
        Instances combined bullet, along with the standalone Private VPC
        Gateway S3 Endpoints recommendation, must no longer be present in
        their old wording."""
        self.assertNotIn(
            "AWS Savings Plans & Reserved Instances (RIs):", self.section
        )
        self.assertNotIn("Private VPC Gateway S3 Endpoints:", self.section)


class CrossFileProductionCostingFigureConsistencyTestCase(unittest.TestCase):
    """Verifies that the two new headline production-costing totals are
    propagated consistently across every summary/roadmap document that
    references them."""

    @classmethod
    def setUpClass(cls):
        cls.readme_content = _read(README_PATH)
        cls.perf_analysis_content = _read(PERF_ANALYSIS_PATH)
        cls.perf_testing_content = _read(PERF_TESTING_PATH)
        cls.roadmap_content = _read(ROADMAP_PATH)
        cls.prod_costing_content = _read(PROD_COSTING_PATH)

    def test_readme_baseline_production_figure(self):
        self.assertIn(
            f"**Baseline Production Plan (~${NEW_BASELINE_TOTAL_USD} USD/mo):**",
            self.readme_content,
        )

    def test_readme_enterprise_production_figure(self):
        self.assertIn(
            f"**High-Performance Enterprise Production Plan "
            f"(~${NEW_ENTERPRISE_TOTAL_USD} USD/mo):**",
            self.readme_content,
        )

    def test_readme_baseline_production_description_updated(self):
        self.assertIn(
            "Cost-optimized, secure production network utilizing 20 active "
            "t4g.micro instances, Multi-AZ/Single-AZ MariaDB/PostgreSQL, "
            "EFS storage, and 3 ALBs.",
            self.readme_content,
        )

    def test_readme_enterprise_production_description_updated(self):
        self.assertIn(
            "High-performance production network utilizing 20 active "
            "t4g.medium instances, Multi-AZ/Single-AZ MariaDB/PostgreSQL, "
            "high-capacity clustered Valkey session store, and 3 ALBs.",
            self.readme_content,
        )

    def test_performance_analysis_matrix_uses_new_baseline_figure(self):
        self.assertIn(f"**${NEW_BASELINE_TOTAL_USD} USD**", self.perf_analysis_content)

    def test_performance_testing_matrix_uses_new_baseline_figure(self):
        self.assertIn(
            f"**${NEW_BASELINE_TOTAL_USD} USD** | **RM {NEW_BASELINE_TOTAL_MYR} MYR**",
            self.perf_testing_content,
        )

    def test_performance_testing_500vu_detail_total_matches_matrix(self):
        self.assertIn(
            f"**Total Monthly Cost:** **${NEW_BASELINE_TOTAL_USD} USD** / "
            f"**RM {NEW_BASELINE_TOTAL_MYR} MYR**",
            self.perf_testing_content,
        )

    def test_roadmap_phase2_run_rate_matches_new_baseline_figure(self):
        self.assertIn(
            f"**Financial Model Run-Rate:** **~${NEW_BASELINE_TOTAL_USD} USD/mo** "
            f"(RM {NEW_BASELINE_TOTAL_MYR} MYR/mo).",
            self.roadmap_content,
        )

    def test_roadmap_phase4_run_rate_matches_new_enterprise_figure(self):
        self.assertIn(
            f"~${NEW_ENTERPRISE_TOTAL_USD} USD/mo** (RM {NEW_ENTERPRISE_TOTAL_MYR} MYR/mo)",
            self.roadmap_content,
        )

    def test_roadmap_timeline_diagram_matches_new_figures(self):
        self.assertIn(f"~${NEW_BASELINE_TOTAL_USD} USD/mo", self.roadmap_content)
        self.assertIn(f"~${NEW_ENTERPRISE_TOTAL_USD}+ USD/mo", self.roadmap_content)

    def test_all_referencing_files_agree_with_production_costing_authoritative_total(self):
        baseline_match = re.search(
            r"\*\*TOTAL \(Baseline\)\*\*.*?\*\*\$([\d,]+\.\d{2})\*\*",
            self.prod_costing_content,
        )
        enterprise_match = re.search(
            r"\*\*TOTAL \(Enterprise\)\*\*.*?\*\*\$([\d,]+\.\d{2})\*\*",
            self.prod_costing_content,
        )
        self.assertIsNotNone(baseline_match)
        self.assertIsNotNone(enterprise_match)
        self.assertEqual(baseline_match.group(1), NEW_BASELINE_TOTAL_USD)
        self.assertEqual(enterprise_match.group(1), NEW_ENTERPRISE_TOTAL_USD)

    def test_stale_figures_absent_from_all_referencing_files(self):
        files = {
            "README.md": self.readme_content,
            "performance-analysis.md": self.perf_analysis_content,
            "performance-testing.md": self.perf_testing_content,
            "aws-adoption-roadmap.md": self.roadmap_content,
            "production-costing.md": self.prod_costing_content,
        }
        for name, content in files.items():
            for stale in ["1,037.73", "1,009.20"]:
                with self.subTest(file=name, stale=stale):
                    self.assertNotIn(stale, content)


if __name__ == "__main__":
    unittest.main()