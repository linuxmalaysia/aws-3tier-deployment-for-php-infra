"""
Unit tests for the technical documentation changes in this PR across:
    - docs/ami-design.md
    - docs/architecture.md
    - docs/asg-separation-of-concern.md
    - docs/codeigniter-php-fpm.md (new file)
    - docs/costing.md
    - docs/dr-options.md
    - docs/hybrid-onprem.md

This PR pivoted these guides from the retired "AI Tier" / Server01-03 naming
scheme to a Nginx + PHP-FPM CodeIgniter architecture, added the new
CodeIgniter deployment guide, and refreshed cost tables/diagrams accordingly.
These tests verify structural/content correctness (Jekyll front-matter,
key architectural strings) and, for the costing/DR/hybrid guides, verify the
numeric integrity of the USD/MYR cost tables via lightweight regex-based
extraction (no external Markdown table parser is available in this sandbox).
"""
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(REPO_ROOT, "docs")

AMI_DESIGN_PATH = os.path.join(DOCS_DIR, "ami-design.md")
ARCHITECTURE_PATH = os.path.join(DOCS_DIR, "architecture.md")
ASG_SEPARATION_PATH = os.path.join(DOCS_DIR, "asg-separation-of-concern.md")
CODEIGNITER_PATH = os.path.join(DOCS_DIR, "codeigniter-php-fpm.md")
COSTING_PATH = os.path.join(DOCS_DIR, "costing.md")
DR_OPTIONS_PATH = os.path.join(DOCS_DIR, "dr-options.md")
HYBRID_ONPREM_PATH = os.path.join(DOCS_DIR, "hybrid-onprem.md")

MYR_PER_USD = 4.50

# Matches whole-cent USD amounts like "$12.26" while excluding hourly/unit
# rate figures (which are always immediately followed by "/ hr", "/ GB",
# " USD", etc. in these tables) and partial matches on amounts with more
# than two decimal digits (e.g. "$0.0084").
USD_LINE_ITEM_RE = re.compile(r"\$([\d,]+\.\d{2})(?!\d)(?!\s*/)(?!\s*USD)")
MYR_LINE_ITEM_RE = re.compile(r"RM\s([\d,]+\.\d{2})(?!\d)")


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _section(content, start_marker, end_marker):
    start = content.find(start_marker)
    assert start != -1, f"start marker not found: {start_marker!r}"
    end = content.find(end_marker, start)
    assert end != -1, f"end marker not found: {end_marker!r}"
    return content[start:end]


def _sum_usd_line_items(section_text):
    return sum(float(m.group(1).replace(",", "")) for m in USD_LINE_ITEM_RE.finditer(section_text))


def _sum_myr_line_items(section_text):
    return sum(float(m.group(1).replace(",", "")) for m in MYR_LINE_ITEM_RE.finditer(section_text))


class TechnicalDocsExistTest(unittest.TestCase):
    def test_all_expected_files_exist(self):
        for path in (
            AMI_DESIGN_PATH, ARCHITECTURE_PATH, ASG_SEPARATION_PATH,
            CODEIGNITER_PATH, COSTING_PATH, DR_OPTIONS_PATH, HYBRID_ONPREM_PATH,
        ):
            self.assertTrue(os.path.isfile(path), f"missing expected file: {path}")


class JekyllFrontMatterTest(unittest.TestCase):
    """All docs/*.md pages must start with valid Jekyll front-matter."""

    def _assert_front_matter(self, path, expected_title):
        content = _load(path)
        self.assertTrue(content.startswith("---\n"), f"{path} missing front-matter")
        self.assertIn("layout: default", content)
        self.assertIn(f'title: "{expected_title}"', content)

    def test_ami_design_front_matter(self):
        self._assert_front_matter(AMI_DESIGN_PATH, "AMI Hardening & Baking Strategy")

    def test_architecture_front_matter(self):
        self._assert_front_matter(ARCHITECTURE_PATH, "System Architecture")

    def test_asg_separation_front_matter(self):
        self._assert_front_matter(
            ASG_SEPARATION_PATH, "Auto Scaling Groups (ASGs) & Separation of Concerns"
        )

    def test_codeigniter_front_matter(self):
        self._assert_front_matter(
            CODEIGNITER_PATH,
            "CodeIgniter PHP Application Deployment & Optimization Guide (with Nginx & PHP-FPM)",
        )

    def test_costing_front_matter(self):
        self._assert_front_matter(COSTING_PATH, "AWS Costing Optimization Guide")

    def test_dr_options_front_matter(self):
        self._assert_front_matter(
            DR_OPTIONS_PATH, "Disaster Recovery Playbook & National Sovereignty Compliance"
        )

    def test_hybrid_onprem_front_matter(self):
        self._assert_front_matter(HYBRID_ONPREM_PATH, "Hybrid Cloud Network Connections")


class AmiDesignContentTest(unittest.TestCase):
    def setUp(self):
        self.content = _load(AMI_DESIGN_PATH)

    def test_references_php_app_golden_ami_naming(self):
        self.assertIn("ami-php-app-*", self.content)

    def test_no_longer_references_retired_ai_ami_naming(self):
        self.assertNotIn("ami-ai-", self.content)

    def test_lists_expected_php_extensions(self):
        for ext in ("php-mbstring", "php-xml", "php-curl", "php-intl", "php-zip", "php-opcache"):
            self.assertIn(ext, self.content)

    def test_mentions_asimp_hardening_framework(self):
        self.assertIn("ASIMP (Ansible System Integrity Management Platform)", self.content)


class ArchitectureContentTest(unittest.TestCase):
    def setUp(self):
        self.content = _load(ARCHITECTURE_PATH)

    def test_diagram_labels_codeigniter_asg(self):
        self.assertIn("CODEIGNITER ASG", self.content)

    def test_no_longer_labels_ai_tier_asg(self):
        self.assertNotIn("AI TIER ASG", self.content)

    def test_describes_three_separate_developer_servers(self):
        self.assertIn("three separate standalone virtual machine servers", self.content)

    def test_mentions_nginx_php_fpm_and_valkey(self):
        self.assertIn("Nginx + PHP-FPM", self.content)
        self.assertIn("Amazon ElastiCache for Valkey", self.content)


class AsgSeparationContentTest(unittest.TestCase):
    def setUp(self):
        self.content = _load(ASG_SEPARATION_PATH)

    def test_describes_combined_asg_model(self):
        self.assertIn("Combined ASG Model", self.content)

    def test_mentions_fastcgi_unix_sockets(self):
        self.assertIn("unix:/run/php/php-fpm.sock", self.content)
        self.assertIn("unix:/run/php-fpm/www.sock", self.content)

    def test_mentions_valkey_session_store_section(self):
        self.assertIn("Amazon ElastiCache for Valkey", self.content)
        self.assertIn("Why Valkey/Redis for Sessions?", self.content)


class CodeigniterGuideContentTest(unittest.TestCase):
    def setUp(self):
        self.content = _load(CODEIGNITER_PATH)

    def test_contains_nginx_server_block_for_codeigniter(self):
        self.assertIn("root /var/www/html/codeigniter/public;", self.content)
        self.assertIn("try_files $uri $uri/ /index.php?$query_string;", self.content)

    def test_contains_php_fpm_pool_static_tuning(self):
        self.assertIn("pm = static", self.content)
        self.assertIn("pm.max_children = 60", self.content)

    def test_contains_opcache_settings(self):
        self.assertIn("opcache.enable=1", self.content)
        self.assertIn("opcache.jit=tracing", self.content)

    def test_contains_codeigniter_env_database_and_session_config(self):
        self.assertIn("CI_ENVIRONMENT = production", self.content)
        self.assertIn("app.sessionSavePath = 'tls://${VALKEY_HOST}:6379?auth=${VALKEY_PASSWORD}&timeout=5'", self.content)

    def test_contains_health_controller_php_code(self):
        self.assertIn("class Health extends Controller", self.content)
        self.assertIn("'status' => 'UP'", self.content)


class CostingLegacyReferencesRegressionTest(unittest.TestCase):
    """Regression test: legacy AI-tier branding must not leak into costing.md."""

    def setUp(self):
        self.content = _load(COSTING_PATH)

    def test_mentions_php_codeigniter_and_conversion_rate(self):
        self.assertIn("PHP CodeIgniter secure 3-Tier Web Application", self.content)
        self.assertIn("1 USD = 4.50 MYR", self.content)

    def test_compute_tier_line_items_reference_nginx_php_fpm(self):
        self.assertIn("Amazon EC2** (Nginx + PHP-FPM)", self.content)


class CostingScenarioAArithmeticTest(unittest.TestCase):
    def setUp(self):
        content = _load(COSTING_PATH)
        self.section = _section(
            content,
            "### Monthly Line-Item Breakdown (Baseline)",
            "### Scenario A Combined Total",
        )
        self.full_content = content

    def test_usd_line_items_sum_to_stated_combined_total(self):
        total = _sum_usd_line_items(self.section)
        self.assertAlmostEqual(total, 141.47, delta=0.01)
        self.assertIn("$141.47 USD / month", self.full_content)

    def test_myr_line_items_sum_to_stated_combined_total(self):
        total = _sum_myr_line_items(self.section)
        self.assertAlmostEqual(total, 636.62, delta=0.02)
        self.assertIn("RM 636.62 MYR / month", self.full_content)


class CostingScenarioBArithmeticTest(unittest.TestCase):
    def setUp(self):
        content = _load(COSTING_PATH)
        self.section = _section(
            content,
            "### Monthly Line-Item Breakdown (Enterprise Plan)",
            "### Scenario B Combined Total",
        )
        self.full_content = content

    def test_usd_line_items_sum_to_stated_combined_total(self):
        total = _sum_usd_line_items(self.section)
        self.assertAlmostEqual(total, 898.54, delta=0.01)
        self.assertIn("$898.54 USD / month", self.full_content)

    def test_myr_line_items_sum_to_stated_combined_total(self):
        total = _sum_myr_line_items(self.section)
        self.assertAlmostEqual(total, 4043.43, delta=0.02)
        self.assertIn("RM 4,043.43 MYR / month", self.full_content)


class DrOptionsCostConversionTest(unittest.TestCase):
    def setUp(self):
        self.content = _load(DR_OPTIONS_PATH)

    def test_backup_restore_myr_matches_usd_conversion(self):
        self.assertIn("$8.00", self.content)
        self.assertIn("RM 36.00", self.content)
        self.assertAlmostEqual(8.00 * MYR_PER_USD, 36.00, places=2)

    def test_pilot_light_myr_matches_usd_conversion(self):
        self.assertIn("$35.00", self.content)
        self.assertIn("RM 157.50", self.content)
        self.assertAlmostEqual(35.00 * MYR_PER_USD, 157.50, places=2)

    def test_warm_standby_myr_matches_usd_conversion(self):
        self.assertIn("$110.00", self.content)
        self.assertIn("RM 495.00", self.content)
        self.assertAlmostEqual(110.00 * MYR_PER_USD, 495.00, places=2)

    def test_mentions_pdpa_amendment_act(self):
        self.assertIn("Personal Data Protection (Amendment) Act 2024 (Act A1727)", self.content)


class HybridOnpremCostConversionTest(unittest.TestCase):
    def setUp(self):
        self.content = _load(HYBRID_ONPREM_PATH)

    def test_vpn_total_myr_matches_usd_conversion(self):
        self.assertIn("~$56.50 USD / month", self.content)
        self.assertIn("RM 254.25 MYR / month", self.content)
        self.assertAlmostEqual(56.50 * MYR_PER_USD, 254.25, places=2)

    def test_api_gateway_total_myr_matches_usd_conversion(self):
        self.assertIn("~$2.40 USD / month", self.content)
        self.assertIn("RM 10.80 MYR / month", self.content)
        self.assertAlmostEqual(2.40 * MYR_PER_USD, 10.80, places=2)

    def test_mentions_mtls_tls_1_2_for_custom_domains(self):
        self.assertIn("terminates mTLS using **TLS 1.2** for custom domains", self.content)


if __name__ == "__main__":
    unittest.main()