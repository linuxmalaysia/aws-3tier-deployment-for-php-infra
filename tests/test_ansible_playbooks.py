#!/usr/bin/env python3
"""Unit tests for verifying Ansible playbook structure, syntax, and security hardening patterns.

This test suite acts as an automated static analyzer and linter for Ansible configuration
files and playbooks within the context of our ASIMP (Ansible System Integrity Management Platform)
standards. It validates structure, best practices, and checks for potential security
vulnerabilities (such as hardcoded secrets or insecure file permissions) in playbooks using a
dependency-free parser.
"""

import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def parse_playbook_lines(playbook_text):
    """A lightweight, dependency-free YAML-like parser that extracts keys and tasks

    from simple playbooks for testing purposes.
    """
    plays = []
    current_play = None
    current_tasks = []
    current_task = None
    in_tasks = False
    in_vars = False
    vars_dict = {}

    for line in playbook_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Detect play start
        if line.startswith("- ") or line.startswith("-name:") or line.startswith("- name:"):
            if current_play is not None:
                if current_task is not None:
                    current_tasks.append(current_task)
                    current_task = None
                current_play['tasks'] = current_tasks
                current_play['vars'] = vars_dict
                plays.append(current_play)
            current_play = {}
            current_tasks = []
            vars_dict = {}
            in_tasks = False
            in_vars = False

            # Extract name if present
            if "name:" in stripped:
                current_play['name'] = stripped.split("name:", 1)[1].strip().strip("'\"")
            continue

        if current_play is None:
            continue

        # Detect list item within tasks
        if in_tasks and (line.startswith("    - ") or line.startswith("  - ")):
            if current_task is not None:
                current_tasks.append(current_task)
            current_task = {}
            if "name:" in stripped:
                current_task["name"] = stripped.split("name:", 1)[1].strip().strip("'\"")
            continue

        # Detect key-value pair
        if ":" in stripped:
            parts = stripped.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip().strip("'\"")

            if key == "hosts":
                current_play["hosts"] = val
                continue
            elif key == "become":
                current_play["become"] = val.lower() in ["true", "yes"]
                continue
            elif key == "tasks":
                in_tasks = True
                in_vars = False
                continue
            elif key == "vars":
                in_vars = True
                in_tasks = False
                continue

            # If inside vars, store them
            if in_vars and not line.startswith("    -"):
                vars_dict[key] = val
                continue

            # If inside a task, store properties
            if in_tasks and current_task is not None:
                current_task[key] = val

    if current_play is not None:
        if current_task is not None:
            current_tasks.append(current_task)
        current_play['tasks'] = current_tasks
        current_play['vars'] = vars_dict
        plays.append(current_play)

    return plays


def check_is_group_or_other_writable(mode_str):
    """Parses a file mode representation (e.g. '0666', '777', or symbolic 'o+w')

    and returns True if the group or other write permissions are enabled.
    """
    mode_str = mode_str.strip("'\"")
    if 'o+w' in mode_str or 'g+w' in mode_str:
        return True

    # Try to parse as octal
    try:
        val = int(mode_str, 8)
        group_write = 0o020
        other_write = 0o002
        if (val & group_write) != 0 or (val & other_write) != 0:
            return True
    except ValueError:
        pass

    return False


class AnsiblePlaybookValidationTestCase(unittest.TestCase):
    """Verifies playbook syntax, best practices, and security configurations

    for Ansible playbooks.
    """

    def setUp(self):
        """Set up some standard playbooks representing secure and insecure

        configurations to test the audit algorithms.
        """
        self.valid_playbook_yaml = """
- name: Harden system via ASIMP
  hosts: app_servers
  become: true
  vars:
    ssh_port: 22
    permit_root_login: "no"
  tasks:
    - name: Ensure SSH server is configured securely
      ansible.builtin.template: ""
      dest: /etc/ssh/sshd_config
      owner: root
      group: root
      mode: '0600'

    - name: Disable legacy/unused system services
      ansible.builtin.service: ""
      state: stopped
      enabled: false
"""

        self.insecure_playbook_yaml = """
- name: Insecure playbook example
  hosts: all
  become: true
  vars:
    db_password: "super_secret_password_123"
  tasks:
    - name: Set insecure file permissions
      ansible.builtin.file: ""
      path: /etc/app_config.ini
      mode: '0666'
"""

    def test_valid_playbook_parses_successfully(self):
        """Ensures that a well-structured and secure playbook parses cleanly."""
        plays = parse_playbook_lines(self.valid_playbook_yaml)
        self.assertEqual(len(plays), 1)
        play = plays[0]
        self.assertEqual(play['hosts'], 'app_servers')
        self.assertTrue(play['become'])
        self.assertEqual(len(play['tasks']), 2)

    def test_ansible_security_rules_enforcement(self):
        """Enforces ASIMP security rules: checks for unencrypted secrets and

        insecure file permissions (e.g., world-writable files '0666' or '0766' or 'o+w').
        """
        plays = parse_playbook_lines(self.insecure_playbook_yaml)
        self.assertEqual(len(plays), 1)
        play = plays[0]

        # Rule 1: No hardcoded variable names with 'password' matching plaintext-like patterns
        vars_dict = play.get('vars', {})
        has_hardcoded_pwd = False
        for var_name, var_val in vars_dict.items():
            if 'password' in var_name.lower():
                if isinstance(var_val, str) and "{{" not in var_val:
                    # Plaintext hardcoded password detected!
                    has_hardcoded_pwd = True

        self.assertTrue(has_hardcoded_pwd, "Insecure hardcoded password should have been detected")

        # Rule 2: Insecure file permission detection ('0666', '777', or 'o+w')
        has_insecure_perms = False
        for task in play.get('tasks', []):
            mode = task.get('mode')
            if mode is not None and check_is_group_or_other_writable(mode):
                has_insecure_perms = True

        self.assertTrue(has_insecure_perms, "Insecure file permissions should have been detected")

    def test_various_octal_modes(self):
        """Test the octal file permission write-bit detection for various modes."""
        self.assertTrue(check_is_group_or_other_writable('0666'))
        self.assertTrue(check_is_group_or_other_writable('0766'))
        self.assertTrue(check_is_group_or_other_writable('777'))
        self.assertTrue(check_is_group_or_other_writable('o+w'))
        self.assertFalse(check_is_group_or_other_writable('0600'))
        self.assertFalse(check_is_group_or_other_writable('0640'))
        self.assertFalse(check_is_group_or_other_writable('0755'))

    def test_secure_playbook_passes_all_security_audits(self):
        """Verifies that our valid secure playbook adheres fully to security

        rules (no plaintext passwords, secure file permission settings of '0600' or similar).
        """
        plays = parse_playbook_lines(self.valid_playbook_yaml)
        self.assertEqual(len(plays), 1)
        play = plays[0]

        # No hardcoded password variables
        vars_dict = play.get('vars', {})
        for var_name in vars_dict:
            self.assertNotIn("password", var_name.lower())

        # Check file task for secure mode
        for task in play.get('tasks', []):
            mode = task.get('mode')
            if mode is not None:
                self.assertFalse(check_is_group_or_other_writable(mode))
                self.assertIn(mode, ["'0600'", "0600", "'0640'", "0640", "'0750'", "0750"])


if __name__ == "__main__":
    unittest.main()
