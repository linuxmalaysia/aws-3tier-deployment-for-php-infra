"""
Unit tests for terraform/modules/asg/main.tf

This PR migrated the ASG launch template's bootstrap logic from a bare
Nginx installation to a full Nginx + PHP-FPM CodeIgniter stack, and added
bounded IMDS metadata retrieval. These tests validate the structural and
content correctness of the embedded `user_data` heredoc and surrounding
resources using lightweight text/regex based assertions (no external HCL
parser dependency is available in this environment).
"""
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODULE_PATH = os.path.join(REPO_ROOT, "terraform", "modules", "asg", "main.tf")


def _load():
    with open(MODULE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _extract_user_data_heredoc(content):
    match = re.search(
        r"user_data = base64encode\(<<-EOF\n(.*?)\n\s*EOF\n\s*\)",
        content,
        re.DOTALL,
    )
    assert match, "Could not locate user_data heredoc block in asg/main.tf"
    return match.group(1)


class AsgModuleExistsTest(unittest.TestCase):
    def test_module_exists(self):
        self.assertTrue(os.path.isfile(MODULE_PATH))


class AsgAmiSelectionTest(unittest.TestCase):
    def setUp(self):
        self.content = _load()

    def test_fetches_al2023_x86_64_and_arm64_ssm_parameters(self):
        self.assertIn('data "aws_ssm_parameter" "al2023_x86_64"', self.content)
        self.assertIn('data "aws_ssm_parameter" "al2023_arm64"', self.content)
        self.assertIn(
            "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64",
            self.content,
        )
        self.assertIn(
            "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64",
            self.content,
        )

    def test_is_arm64_regex_matches_graviton_family_instance_types(self):
        pattern = r"^[a-z]+[0-9]g\."
        graviton_types = ["t4g.micro", "m6g.xlarge", "c6g.large", "r6g.medium"]
        non_graviton_types = ["t3.micro", "m5.large", "c5.xlarge"]
        for t in graviton_types:
            self.assertTrue(re.match(pattern, t), f"{t} should be classified as Graviton/arm64")
        for t in non_graviton_types:
            self.assertFalse(re.match(pattern, t), f"{t} should NOT be classified as Graviton/arm64")

    def test_selected_ami_falls_back_to_var_ami_id_override(self):
        self.assertIn(
            'selected_ami_id = var.ami_id != "" ? var.ami_id : local.default_ami_id',
            self.content,
        )


class AsgIamAndLaunchTemplateTest(unittest.TestCase):
    def setUp(self):
        self.content = _load()

    def test_instance_profile_attaches_ssm_managed_policy(self):
        self.assertIn(
            'policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"',
            self.content,
        )

    def test_launch_template_disables_public_ip(self):
        self.assertIn("associate_public_ip_address = false", self.content)

    def test_launch_template_uses_selected_ami_and_var_instance_type(self):
        self.assertIn("image_id      = local.selected_ami_id", self.content)
        self.assertIn("instance_type = var.instance_type", self.content)

    def test_launch_template_create_before_destroy(self):
        # There should be at least one lifecycle block enforcing create_before_destroy
        self.assertIn("create_before_destroy = true", self.content)


class AsgUserDataBootstrapTest(unittest.TestCase):
    def setUp(self):
        self.content = _load()
        self.user_data = _extract_user_data_heredoc(self.content)

    def test_safety_flags_enabled(self):
        self.assertIn("set -euo pipefail", self.user_data)

    def test_installs_nginx_and_php_fpm_stack(self):
        expected_packages = [
            "nginx", "php-fpm", "php-mysqli", "php-pdo",
            "php-mbstring", "php-xml", "php-curl", "php-intl",
            "php-zip", "php-opcache",
        ]
        for pkg in expected_packages:
            self.assertIn(pkg, self.user_data, f"user_data missing package: {pkg}")

    def test_uses_dnf_package_manager(self):
        self.assertIn("dnf update -y", self.user_data)
        self.assertIn("dnf install -y", self.user_data)

    def test_enables_and_restarts_php_fpm_and_nginx(self):
        self.assertIn("systemctl restart php-fpm", self.user_data)
        self.assertIn("systemctl enable php-fpm", self.user_data)
        self.assertIn("systemctl restart nginx", self.user_data)
        self.assertIn("systemctl enable nginx", self.user_data)

    def test_creates_codeigniter_document_root(self):
        self.assertIn("mkdir -p /var/www/html/codeigniter/public", self.user_data)

    def test_writes_nginx_config_pointing_to_php_fpm_socket(self):
        self.assertIn("/etc/nginx/conf.d/codeigniter.conf", self.user_data)
        self.assertIn("fastcgi_pass unix:/run/php-fpm/www.sock;", self.user_data)

    def test_removes_default_nginx_server_block(self):
        self.assertIn("sed -i '/default_server/d' /etc/nginx/nginx.conf || true", self.user_data)

    def test_imds_calls_are_bounded_with_timeouts(self):
        curl_lines = [line for line in self.user_data.splitlines() if "curl -s" in line]
        self.assertGreater(len(curl_lines), 0)
        for line in curl_lines:
            self.assertIn("--max-time 2", line)
            self.assertIn("--connect-timeout 2", line)
            self.assertIn("|| echo", line)

    def test_instance_metadata_has_fallback_defaults(self):
        self.assertIn('INSTANCE_ID="unknown-instance-id"', self.user_data)
        self.assertIn('AZ="unknown-az"', self.user_data)

    def test_writes_mock_codeigniter_front_controller(self):
        self.assertIn("define('CI_VERSION', '4.5.1');", self.user_data)
        self.assertIn("/var/www/html/codeigniter/public/index.php", self.user_data)

    def test_no_legacy_bare_nginx_only_bootstrap(self):
        # Regression: previously this only installed nginx and echoed a static
        # index.html; ensure that legacy one-liner is gone.
        self.assertNotIn("usr/share/nginx/html/index.html", self.content)


class AsgAutoScalingResourcesTest(unittest.TestCase):
    def setUp(self):
        self.content = _load()

    def test_autoscaling_group_uses_elb_health_checks(self):
        self.assertIn('health_check_type         = "ELB"', self.content)
        self.assertIn("health_check_grace_period = 300", self.content)

    def test_autoscaling_group_sizing_variables(self):
        self.assertIn("min_size         = var.min_size", self.content)
        self.assertIn("max_size         = var.max_size", self.content)
        self.assertIn("desired_capacity = var.desired_capacity", self.content)

    def test_instance_refresh_uses_rolling_strategy(self):
        self.assertIn('strategy = "Rolling"', self.content)
        self.assertIn("min_healthy_percentage = 50", self.content)

    def test_lifecycle_ignores_desired_capacity_changes(self):
        self.assertIn("ignore_changes        = [desired_capacity]", self.content)

    def test_scale_out_and_scale_in_policies_defined(self):
        self.assertIn('resource "aws_autoscaling_policy" "scale_out"', self.content)
        self.assertIn('resource "aws_autoscaling_policy" "scale_in"', self.content)
        self.assertIn("scaling_adjustment     = 1", self.content)
        self.assertIn("scaling_adjustment     = -1", self.content)

    def test_cpu_alarms_use_expected_thresholds(self):
        high_cpu_match = re.search(
            r'resource "aws_cloudwatch_metric_alarm" "cpu_high" \{.*?threshold\s*=\s*(\d+)',
            self.content,
            re.DOTALL,
        )
        low_cpu_match = re.search(
            r'resource "aws_cloudwatch_metric_alarm" "cpu_low" \{.*?threshold\s*=\s*(\d+)',
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(high_cpu_match)
        self.assertIsNotNone(low_cpu_match)
        self.assertEqual(int(high_cpu_match.group(1)), 70)
        self.assertEqual(int(low_cpu_match.group(1)), 30)


if __name__ == "__main__":
    unittest.main()