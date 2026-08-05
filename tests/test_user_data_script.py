"""
Unit tests for scripts/user_data.sh

This script bootstraps EC2 instances with Nginx + PHP-FPM to serve a
CodeIgniter application. It replaced a previous Apache-based bootstrap
script. These tests validate:
  - Shell syntax correctness (via `bash -n`)
  - Safety flags (set -euo pipefail)
  - Bounded IMDSv2 metadata retrieval (regression: previously unbounded
    curl calls could hang instance boot indefinitely)
  - OS detection branches for Debian/Ubuntu and Amazon Linux
  - Correct package lists, PHP-FPM service/socket naming per OS
  - Nginx configuration generation pointing to the correct FPM socket
  - Fallback behavior (exit 1) for unsupported operating systems
  - Generation of the CodeIgniter mock front controller
"""
import os
import re
import shutil
import subprocess
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT_PATH = os.path.join(REPO_ROOT, "scripts", "user_data.sh")


class UserDataScriptExistsTest(unittest.TestCase):
    def test_script_exists(self):
        self.assertTrue(os.path.isfile(SCRIPT_PATH), "scripts/user_data.sh must exist")

    def setUp(self):
        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            self.content = f.read()


class UserDataScriptSyntaxTest(unittest.TestCase):
    def setUp(self):
        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            self.content = f.read()

    def test_shebang_is_bash(self):
        self.assertTrue(self.content.startswith("#!/bin/bash"))

    def test_bash_syntax_is_valid(self):
        bash_bin = shutil.which("bash")
        if not bash_bin:
            self.skipTest("bash is not available in this environment")
        result = subprocess.run(
            [bash_bin, "-n", SCRIPT_PATH],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            f"bash -n reported a syntax error:\n{result.stderr}"
        )

    def test_safety_flags_enabled(self):
        self.assertIn("set -euo pipefail", self.content)


class UserDataScriptImdsTest(unittest.TestCase):
    """Regression tests ensuring IMDS calls are bounded and won't hang boot."""

    def setUp(self):
        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            self.content = f.read()

    def test_token_request_uses_put_and_ttl_header(self):
        self.assertIn('curl -s -X PUT "http://169.254.169.254/latest/api/token"', self.content)
        self.assertIn("X-aws-ec2-metadata-token-ttl-seconds: 21600", self.content)

    def test_all_curl_calls_are_bounded_with_timeouts(self):
        curl_lines = [line for line in self.content.splitlines() if "curl -s" in line]
        self.assertGreater(len(curl_lines), 0, "expected at least one curl invocation")
        for line in curl_lines:
            self.assertIn("--max-time 2", line, f"curl call missing --max-time bound: {line}")
            self.assertIn("--connect-timeout 2", line, f"curl call missing --connect-timeout bound: {line}")

    def test_curl_failures_fall_back_gracefully(self):
        # Every bounded curl call must have a fallback via `|| echo ...` so that
        # a failed/timed-out IMDS call does not abort the script under `set -e`.
        curl_lines = [line for line in self.content.splitlines() if "curl -s" in line]
        for line in curl_lines:
            self.assertIn("|| echo", line, f"curl call missing failure fallback: {line}")

    def test_instance_id_and_az_have_unknown_fallback_values(self):
        self.assertIn('"unknown-instance-id"', self.content)
        self.assertIn('"unknown-az"', self.content)

    def test_token_conditional_branch_present(self):
        self.assertIn('if [ -n "$TOKEN" ]; then', self.content)
        self.assertIn("else", self.content)


class UserDataScriptOsDetectionTest(unittest.TestCase):
    def setUp(self):
        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            self.content = f.read()

    def test_debian_branch_detects_debian_version_file(self):
        self.assertIn("if [ -f /etc/debian_version ]; then", self.content)

    def test_debian_branch_sets_noninteractive_frontend(self):
        self.assertIn("export DEBIAN_FRONTEND=noninteractive", self.content)

    def test_debian_branch_installs_expected_packages(self):
        debian_section = self._extract_branch("/etc/debian_version", "elif")
        expected_packages = [
            "nginx", "php-fpm", "php-mysql", "php-pgsql",
            "php-mbstring", "php-xml", "php-curl", "php-intl",
            "php-zip", "php-opcache",
        ]
        for pkg in expected_packages:
            self.assertIn(pkg, debian_section, f"Debian branch missing package: {pkg}")

    def test_debian_branch_derives_php_fpm_service_and_socket_dynamically(self):
        self.assertIn(
            'PHP_VER=$(php -r \'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;\')',
            self.content,
        )
        self.assertIn('FPM_SERVICE="php${PHP_VER}-fpm"', self.content)
        self.assertIn('FPM_SOCKET="/run/php/php${PHP_VER}-fpm.sock"', self.content)

    def test_amazon_linux_branch_detects_os_release(self):
        self.assertIn(
            'elif [ -f /etc/os-release ] && grep -q "Amazon Linux" /etc/os-release; then',
            self.content,
        )

    def test_amazon_linux_branch_installs_expected_packages(self):
        al_section = self._extract_branch('grep -q "Amazon Linux"', "else")
        expected_packages = [
            "nginx", "php-fpm", "php-mysqli", "php-pdo",
            "php-mbstring", "php-xml", "php-curl", "php-intl",
            "php-zip", "php-opcache",
        ]
        for pkg in expected_packages:
            self.assertIn(pkg, al_section, f"Amazon Linux branch missing package: {pkg}")

    def test_amazon_linux_branch_uses_fixed_service_and_socket_names(self):
        al_section = self._extract_branch('grep -q "Amazon Linux"', "else")
        self.assertIn('FPM_SERVICE="php-fpm"', al_section)
        self.assertIn('FPM_SOCKET="/run/php-fpm/www.sock"', al_section)

    def test_fallback_branch_exits_nonzero(self):
        start = self.content.find('echo "Fallback OS configuration"')
        self.assertNotEqual(start, -1, "fallback branch message not found")
        end = self.content.find("\nfi", start)
        self.assertNotEqual(end, -1, "closing 'fi' for OS detection block not found")
        fallback_section = self.content[start:end]
        self.assertIn("exit 1", fallback_section)

    def test_fallback_message_present(self):
        self.assertIn('echo "Fallback OS configuration"', self.content)

    def _extract_branch(self, start_marker, end_marker):
        start = self.content.find(start_marker)
        self.assertNotEqual(start, -1, f"start marker not found: {start_marker}")
        end = self.content.find(end_marker, start)
        self.assertNotEqual(end, -1, f"end marker not found after start: {end_marker}")
        return self.content[start:end]


class UserDataScriptNginxConfigTest(unittest.TestCase):
    def setUp(self):
        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            self.content = f.read()

    def test_document_root_created(self):
        self.assertIn("mkdir -p /var/www/html/codeigniter/public", self.content)

    def test_nginx_conf_path_defaults_to_sites_available(self):
        self.assertIn('NGINX_CONF_PATH="/etc/nginx/sites-available/default"', self.content)

    def test_nginx_conf_path_falls_back_for_amazon_linux(self):
        self.assertIn(
            'NGINX_CONF_PATH="/etc/nginx/conf.d/codeigniter.conf"',
            self.content,
        )
        self.assertIn('if [ ! -d "/etc/nginx/sites-available" ]; then', self.content)

    def test_default_server_block_removed_when_no_sites_available(self):
        self.assertIn("sed -i '/default_server/d' /etc/nginx/nginx.conf || true", self.content)

    def test_nginx_server_block_written_via_heredoc(self):
        self.assertIn('cat <<EOF > "$NGINX_CONF_PATH"', self.content)
        self.assertIn("server {", self.content)
        self.assertIn("listen 80 default_server;", self.content)
        self.assertIn("root /var/www/html/codeigniter/public;", self.content)

    def test_php_location_block_uses_fastcgi_and_dynamic_socket(self):
        self.assertIn(r"location ~ \.php\$ {", self.content)
        self.assertIn("fastcgi_pass unix:$FPM_SOCKET;", self.content)
        self.assertIn("include fastcgi_params;", self.content)

    def test_nginx_restarted_after_config_write(self):
        # Nginx should be restarted both before and after writing the custom config
        occurrences = [m.start() for m in re.finditer(r"systemctl restart nginx", self.content)]
        self.assertGreaterEqual(len(occurrences), 2)


class UserDataScriptIndexPhpTest(unittest.TestCase):
    def setUp(self):
        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            self.content = f.read()

    def test_index_php_written_to_public_dir(self):
        self.assertIn(
            "cat <<EOF > /var/www/html/codeigniter/public/index.php",
            self.content,
        )

    def test_index_php_defines_ci_version_and_environment(self):
        self.assertIn("define('CI_VERSION', '4.5.1');", self.content)
        self.assertIn("define('ENVIRONMENT', 'production');", self.content)

    def test_index_php_reports_instance_metadata(self):
        self.assertIn("$INSTANCE_ID", self.content)
        self.assertIn("$AZ", self.content)

    def test_index_php_reports_php_and_framework_version(self):
        self.assertIn("phpversion()", self.content)
        self.assertIn("CI_VERSION", self.content)

    def test_index_php_reports_db_and_valkey_status_placeholders(self):
        self.assertIn("db_status", self.content)
        self.assertIn("valkey_status", self.content)
        self.assertIn("Disconnected (Pending Configuration)", self.content)

    def test_completion_message_present(self):
        self.assertIn('echo "=== Bootstrapping Complete ==="', self.content)

    def test_start_banner_message_present(self):
        self.assertIn(
            'echo "=== Bootstrapping Nginx & PHP-FPM for CodeIgniter Web Application ==="',
            self.content,
        )


class UserDataScriptRegressionTest(unittest.TestCase):
    """Ensures legacy Apache/httpd bootstrap logic was fully removed."""

    def setUp(self):
        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            self.content = f.read()

    def test_no_httpd_or_apache_references(self):
        lowered = self.content.lower()
        self.assertNotIn("httpd", lowered)
        self.assertNotIn("apache", lowered)

    def test_no_unbounded_curl_without_timeout(self):
        for line in self.content.splitlines():
            if "curl -s" in line and "--max-time" not in line:
                self.fail(f"Found a curl invocation without a bounded timeout: {line}")


if __name__ == "__main__":
    unittest.main()