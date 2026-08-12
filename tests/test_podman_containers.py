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
    """
    Parse systemd Quadlet text into section-based key-value entries.
    
    Parameters:
        quadlet_text (str): Quadlet configuration text to parse.
    
    Returns:
        dict: A mapping of section names to lists of dictionaries containing
            ``key`` and ``value`` entries.
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
SecurityLabelDisable=true

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


class ParseQuadletFileEdgeCaseTestCase(unittest.TestCase):
    """Edge-case and boundary tests for the dependency-free
    ``parse_quadlet_file`` parser itself, independent of the specific
    secure/insecure fixture Quadlet files used above."""

    def test_empty_text_returns_no_sections(self):
        self.assertEqual(parse_quadlet_file(""), {})

    def test_text_with_only_comments_and_blank_lines_returns_no_sections(self):
        text = """
# top-level comment
; semicolon-style comment

# another comment
"""
        self.assertEqual(parse_quadlet_file(text), {})

    def test_key_value_lines_before_any_section_header_are_ignored(self):
        """Regression: a stray key=value pair appearing before any
        [Section] header must not raise or be silently attributed to a
        None section key."""
        text = """
OrphanKey=OrphanValue

[Unit]
Description=After the orphan line
"""
        sections = parse_quadlet_file(text)
        self.assertEqual(list(sections.keys()), ["Unit"])
        self.assertEqual(
            sections["Unit"], [{"key": "Description", "value": "After the orphan line"}]
        )

    def test_declared_section_with_no_keys_is_present_but_empty(self):
        text = """
[Install]
"""
        sections = parse_quadlet_file(text)
        self.assertIn("Install", sections)
        self.assertEqual(sections["Install"], [])

    def test_section_header_whitespace_is_trimmed(self):
        text = """
[  Container  ]
Image=docker.io/library/alpine:latest
"""
        sections = parse_quadlet_file(text)
        self.assertIn("Container", sections)
        self.assertNotIn("  Container  ", sections)

    def test_malformed_section_header_without_closing_bracket_is_ignored(self):
        """A line that starts with '[' but has no closing ']' should not be
        registered as a new section, and should not crash the parser."""
        text = """
[Unit
Description=Should not be captured anywhere
"""
        sections = parse_quadlet_file(text)
        self.assertEqual(sections, {})

    def test_duplicate_keys_within_a_section_are_all_preserved(self):
        """Quadlet files commonly repeat directives such as 'Volume=' or
        'PublishPort=' multiple times; the parser must keep every
        occurrence rather than overwriting earlier ones."""
        text = """
[Container]
Volume=/data/one:/mnt/one:Z
Volume=/data/two:/mnt/two:Z
PublishPort=8080:80
PublishPort=8443:443
"""
        sections = parse_quadlet_file(text)
        volumes = [item["value"] for item in sections["Container"] if item["key"] == "Volume"]
        ports = [item["value"] for item in sections["Container"] if item["key"] == "PublishPort"]
        self.assertEqual(volumes, ["/data/one:/mnt/one:Z", "/data/two:/mnt/two:Z"])
        self.assertEqual(ports, ["8080:80", "8443:443"])

    def test_value_containing_an_equals_sign_is_preserved_in_full(self):
        """Values such as 'Environment=KEY=VALUE' must only be split on the
        first '=' so the value itself can safely contain '=' characters."""
        text = """
[Container]
Environment=DATABASE_URL=mysql://user:pass@host/db
"""
        sections = parse_quadlet_file(text)
        env_entries = [item for item in sections["Container"] if item["key"] == "Environment"]
        self.assertEqual(len(env_entries), 1)
        self.assertEqual(
            env_entries[0]["value"], "DATABASE_URL=mysql://user:pass@host/db"
        )

    def test_inline_comment_characters_do_not_terminate_a_value(self):
        """The parser has no concept of inline comments -- only whole-line
        comments starting with '#' or ';' are skipped. A value that
        happens to contain a '#' character must be preserved verbatim."""
        text = """
[Unit]
Description=Runs the app # not a comment, part of the value
"""
        sections = parse_quadlet_file(text)
        self.assertEqual(
            sections["Unit"],
            [{"key": "Description", "value": "Runs the app # not a comment, part of the value"}],
        )

    def test_multiple_sections_are_isolated_from_one_another(self):
        text = """
[Unit]
Description=Multi-section test

[Container]
Image=docker.io/library/alpine:latest

[Install]
WantedBy=multi-user.target
"""
        sections = parse_quadlet_file(text)
        self.assertEqual(list(sections.keys()), ["Unit", "Container", "Install"])
        self.assertEqual(len(sections["Unit"]), 1)
        self.assertEqual(len(sections["Container"]), 1)
        self.assertEqual(len(sections["Install"]), 1)

    def test_reopening_a_previously_seen_section_resets_its_entries(self):
        """If the same [Section] header appears twice, the second
        occurrence resets that section's list (last-write-wins), matching
        the parser's straightforward dict-assignment behaviour."""
        text = """
[Container]
Image=first-image:latest

[Container]
Image=second-image:latest
"""
        sections = parse_quadlet_file(text)
        self.assertEqual(sections["Container"], [{"key": "Image", "value": "second-image:latest"}])


if __name__ == "__main__":
    unittest.main()
