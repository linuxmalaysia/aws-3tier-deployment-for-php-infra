"""
Unit tests for terraform/modules/standalone_ec2/main.tf

This module provisions standalone EC2 instances used for AMI staging/baking.
This PR updated its `user_data` bootstrap script from a bare Nginx install to
a full Nginx + PHP-FPM CodeIgniter stack (mirroring the ASG module), added
safety flags, dynamic PHP-FPM service/socket discovery, and bounded IMDS
metadata retrieval.
"""
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODULE_PATH = os.path.join(REPO_ROOT, "terraform", "modules", "standalone_ec2", "main.tf")


def _load():
    with open(MODULE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _extract_user_data_heredoc(content):
    match = re.search(
        r"user_data = <<-EOF\n(.*?)\n\s*EOF\n",
        content,
        re.DOTALL,
    )
    assert match, "Could not locate user_data heredoc block in standalone_ec2/main.tf"
    return match.group(1)


class StandaloneEc2ModuleExistsTest(unittest.TestCase):
    def test_module_exists(self):
        self.assertTrue(os.path.isfile(MODULE_PATH))


class StandaloneEc2AmiSelectionTest(unittest.TestCase):
    def setUp(self):
        self.content = _load()

    def test_is_arm64_regex_matches_graviton_family(self):
        pattern = r"^[a-z]+[0-9]g\."
        self.assertTrue(re.match(pattern, "t4g.micro"))
        self.assertFalse(re.match(pattern, "t3.micro"))

    def test_ami_data_source_filters_canonical_owner(self):
        self.assertIn('owners      = ["099720109477"] # Canonical', self.content)

    def test_ami_architecture_filter_uses_is_arm64_local(self):
        self.assertIn('values = [local.is_arm64 ? "arm64" : "x86_64"]', self.content)

    def test_selected_ami_falls_back_to_dynamic_lookup(self):
        self.assertIn(
            'selected_ami_id = var.ami_id != "" ? var.ami_id : one(data.aws_ami.ubuntu_canonical[*].id)',
            self.content,
        )

    def test_lifecycle_ignores_ami_changes(self):
        self.assertIn("ignore_changes = [ami]", self.content)


class StandaloneEc2SecurityGroupTest(unittest.TestCase):
    def setUp(self):
        self.content = _load()

    def test_ingress_allows_http_and_https_from_alb_only(self):
        # Ensure both port 80 and 443 ingress rules restrict source to the ALB SG
        ingress_blocks = re.findall(r"ingress\s*\{(.*?)\}", self.content, re.DOTALL)
        self.assertEqual(len(ingress_blocks), 2, "expected exactly two ingress rules (80 and 443)")
        ports = set()
        for block in ingress_blocks:
            self.assertIn("security_groups = [var.alb_sg_id]", block)
            port_match = re.search(r"from_port\s*=\s*(\d+)", block)
            self.assertIsNotNone(port_match)
            ports.add(int(port_match.group(1)))
        self.assertEqual(ports, {80, 443})

    def test_egress_allows_all_outbound(self):
        egress_match = re.search(r"egress\s*\{(.*?)\}", self.content, re.DOTALL)
        self.assertIsNotNone(egress_match)
        egress_block = egress_match.group(1)
        self.assertIn('protocol    = "-1"', egress_block)
        self.assertIn('cidr_blocks = ["0.0.0.0/0"]', egress_block)


class StandaloneEc2IamTest(unittest.TestCase):
    def setUp(self):
        self.content = _load()

    def test_attaches_ssm_managed_policy(self):
        self.assertIn(
            'policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"',
            self.content,
        )

    def test_instance_count_uses_var(self):
        self.assertIn("count         = var.instance_count", self.content)

    def test_instance_tags_indicate_hardening_compliance(self):
        self.assertIn('OS          = "Ubuntu-26.04-LTS"', self.content)
        self.assertIn('Hardened    = "ASIMP-Compliant"', self.content)


class StandaloneEc2UserDataBootstrapTest(unittest.TestCase):
    def setUp(self):
        self.content = _load()
        self.user_data = _extract_user_data_heredoc(self.content)

    def test_safety_flags_and_noninteractive_frontend(self):
        self.assertIn("set -euo pipefail", self.user_data)
        self.assertIn("export DEBIAN_FRONTEND=noninteractive", self.user_data)

    def test_uses_apt_get_package_manager(self):
        self.assertIn("apt-get update -y", self.user_data)
        self.assertIn("apt-get upgrade -y", self.user_data)
        self.assertIn("apt-get install -y", self.user_data)

    def test_installs_expected_nginx_php_packages(self):
        expected_packages = [
            "nginx", "php-fpm", "php-mysql", "php-pgsql",
            "php-mbstring", "php-xml", "php-curl", "php-intl",
            "php-zip", "php-opcache",
        ]
        for pkg in expected_packages:
            self.assertIn(pkg, self.user_data, f"user_data missing package: {pkg}")

    def test_derives_php_version_dynamically(self):
        self.assertIn(
            'PHP_VER=$(php -r \'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;\')',
            self.user_data,
        )

    def test_fpm_service_and_socket_use_escaped_terraform_interpolation(self):
        # Because this heredoc is NOT quoted (<<-EOF), Terraform will try to
        # interpolate ${...}; the raw bash ${PHP_VER} must be escaped as $${PHP_VER}
        # to survive Terraform's templating and reach the shell unescaped.
        self.assertIn('FPM_SERVICE="php$${PHP_VER}-fpm"', self.user_data)
        self.assertIn('FPM_SOCKET="/run/php/php$${PHP_VER}-fpm.sock"', self.user_data)

    def test_restarts_and_enables_fpm_and_nginx(self):
        self.assertIn('systemctl restart "$FPM_SERVICE"', self.user_data)
        self.assertIn('systemctl enable "$FPM_SERVICE"', self.user_data)
        self.assertIn("systemctl restart nginx", self.user_data)
        self.assertIn("systemctl enable nginx", self.user_data)

    def test_creates_codeigniter_document_root(self):
        self.assertIn("mkdir -p /var/www/html/codeigniter/public", self.user_data)

    def test_writes_nginx_config_to_sites_available(self):
        self.assertIn("/etc/nginx/sites-available/default", self.user_data)
        self.assertIn("fastcgi_pass unix:$FPM_SOCKET;", self.user_data)

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

    def test_writes_mock_codeigniter_front_controller_with_index_label(self):
        self.assertIn("define('CI_VERSION', '4.5.1');", self.user_data)
        self.assertIn("Standalone Developer Server", self.user_data)
        self.assertIn("${count.index + 1}", self.user_data)

    def test_no_legacy_bare_nginx_only_bootstrap(self):
        self.assertNotIn("var/www/html/index.html", self.content)
        self.assertNotIn("systemctl enable --now nginx", self.content)


if __name__ == "__main__":
    unittest.main()