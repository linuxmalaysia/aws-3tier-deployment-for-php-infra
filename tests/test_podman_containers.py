#!/usr/bin/env python3
"""Unit tests for verifying Podman container definitions and systemd Quadlet files.

This test suite validates container execution profiles, unprivileged/rootless configurations,
network options, and systemd Quadlet formatting rules for self-hosted container deployments
(such as Podman 5+ setups referenced in our on-premises comparative reviews).
"""

import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def parse_quadlet_file(quadlet_text):
    """A lightweight, dependency-free parser for systemd Quadlet (.container) files.

    It returns a dictionary mapping section names to list of key-value dictionaries.
    """
    sections = {}
    current_section = None

    for line in quadlet_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(";"):
            continue

        # Detect Section start
        if stripped.startswith("[") and stripped.endswith("]"):
            current_section = stripped[1:-1].strip()
            sections[current_section] = []
            continue

        if current_section is None:
            continue

        # Detect key-value pair
        if "=" in stripped:
            key, val = [part.strip() for part in stripped.split("=", 1)]
            sections[current_section].append({"key": key, "value": val})

    return sections


class PodmanContainerValidationTestCase(unittest.TestCase):
    """Verifies unprivileged, secure container execution parameters and Quadlet compliance."""

    def setUp(self):
        """Set up some standard Quadlet container configs representing secure and insecure

        configurations to test the parser and validation algorithms.
        """
        self.secure_quadlet_ini = """
[Unit]
Description=Secure CodeIgniter Application Container
After=network-online.target

[Container]
Image=docker.io/library/php:8.2-fpm-alpine
ContainerName=secure-app
PublishPort=8080:80
Volume=/home/app/uploads:/var/www/html/uploads:Z
ReadOnly=true
User=1000:1000
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
"""

        self.insecure_quadlet_ini = """
[Unit]
Description=Insecure container running as root
After=network-online.target

[Container]
Image=docker.io/library/php:8.2-fpm-alpine
ContainerName=insecure-app
PublishPort=80:80
Privileged=true
User=root
Volume=/var/run/docker.sock:/var/run/docker.sock
SecurityLabelDisable=true

[Install]
WantedBy=multi-user.target
"""

    def test_secure_quadlet_parses_successfully(self):
        """Ensures that a well-structured secure Quadlet file parses cleanly and has expected sections."""
        sections = parse_quadlet_file(self.secure_quadlet_ini)
        self.assertIn("Unit", sections)
        self.assertIn("Container", sections)
        self.assertIn("Install", sections)

        container_section = sections["Container"]
        self.assertTrue(any(item["key"] == "Image" and "php" in item["value"] for item in container_section))
        self.assertTrue(any(item["key"] == "ContainerName" and item["value"] == "secure-app" for item in container_section))

    def test_insecure_quadlet_detection(self):
        """Enforces secure container best practices (rootless, non-privileged, no docker.sock mount)."""
        sections = parse_quadlet_file(self.insecure_quadlet_ini)
        self.assertIn("Container", sections)
        container_section = sections["Container"]

        # 1. Enforce No Privileged=true
        is_privileged = any(item["key"] == "Privileged" and item["value"].lower() == "true" for item in container_section)
        self.assertTrue(is_privileged, "Should detect privileged=true parameter as insecure")

        # 2. Enforce Non-Root Execution
        is_root_user = any(item["key"] == "User" and item["value"].lower() == "root" for item in container_section)
        self.assertTrue(is_root_user, "Should detect execution as root user as insecure")

        # 3. Detect dangerous socket mount (e.g. docker.sock or podman.sock)
        has_socket_mount = False
        for item in container_section:
            if item["key"] == "Volume":
                val = item["value"]
                if "docker.sock" in val or "podman.sock" in val:
                    has_socket_mount = True
        self.assertTrue(has_socket_mount, "Should detect insecure socket mount")

        # 4. Detect disabled security label separation (SecurityLabelDisable=true)
        has_disabled_label = any(item["key"] == "SecurityLabelDisable" and item["value"].lower() == "true" for item in container_section)
        self.assertTrue(has_disabled_label, "Should detect disabled security label separation as insecure")

    def test_secure_quadlet_adheres_to_rules(self):
        """Verifies that our secure application Quadlet complies fully with security audits."""
        sections = parse_quadlet_file(self.secure_quadlet_ini)
        container_section = sections["Container"]

        # Check: No Privileged key, or set to false
        privileged_val = next((item["value"] for item in container_section if item["key"] == "Privileged"), "false")
        self.assertEqual(privileged_val.lower(), "false")

        # Check: User must not be root
        user_val = next((item["value"] for item in container_section if item["key"] == "User"), None)
        self.assertIsNotNone(user_val)
        self.assertNotEqual(user_val.lower(), "root")

        # Check: ReadOnly or secure volume options
        readonly_val = next((item["value"] for item in container_section if item["key"] == "ReadOnly"), "false")
        self.assertEqual(readonly_val.lower(), "true")

        # Check: NoNewPrivileges must be true
        no_new_privs = next((item["value"] for item in container_section if item["key"] == "NoNewPrivileges"), "false")
        self.assertEqual(no_new_privs.lower(), "true")

        # Check: SecurityLabelDisable must NOT be true in any entry
        has_disabled_label = any(item["key"] == "SecurityLabelDisable" and item["value"].lower() == "true" for item in container_section)
        self.assertFalse(has_disabled_label, "SecurityLabelDisable must not be true for secure profile")

    def test_duplicate_security_label_disable_rejected(self):
        """Regression: ensure a configuration with duplicate SecurityLabelDisable keys where

        a later key is true is rejected.
        """
        duplicate_labels_ini = """
[Container]
Image=docker.io/library/php:8.2-fpm-alpine
ContainerName=secure-app
User=1000:1000
NoNewPrivileges=true
ReadOnly=true
SecurityLabelDisable=false
SecurityLabelDisable=true
"""
        sections = parse_quadlet_file(duplicate_labels_ini)
        container_section = sections["Container"]

        has_disabled_label = any(item["key"] == "SecurityLabelDisable" and item["value"].lower() == "true" for item in container_section)
        self.assertTrue(has_disabled_label, "Should detect duplicate keys where later value is true")


if __name__ == "__main__":
    unittest.main()
