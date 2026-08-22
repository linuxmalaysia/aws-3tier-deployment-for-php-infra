#!/usr/bin/env python3
"""Unit tests for .github/workflows/docs-ci.yml.

This PR adds a new "Setup Node.js" step (using `actions/setup-node@v4`
pinned to `node-version: "22"`) to the `validate-docs` job, inserted
between the "Checkout Code" and "Setup Python" steps. The workflow file is
treated as plain text (rather than parsed with a YAML library) to stay
dependency free, following the pattern already used by
`tests/test_pdf_generation_workflow.py`.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_docs_ci_workflow
"""
import os
import re
import unittest

WORKFLOW_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".github",
        "workflows",
        "docs-ci.yml",
    )
)


def _get_step_block(content, step_name):
    """Extract the raw text of a step (everything after its `- name:` line
    up to, but not including, the next `- name:` line), regardless of
    indentation."""
    pattern = re.compile(
        r"^[ \t]*- name:\s*"
        + re.escape(step_name)
        + r"\s*\n((?:(?!^[ \t]*- name:).*\n?)*)",
        re.MULTILINE,
    )
    match = pattern.search(content)
    return match.group(1) if match else None


class DocsCiWorkflowTestCase(unittest.TestCase):
    """Tests for the docs-ci.yml GitHub Actions workflow."""

    @classmethod
    def setUpClass(cls):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()

    # ------------------------------------------------------------------
    # Sanity / structural checks
    # ------------------------------------------------------------------
    def test_workflow_file_exists(self):
        self.assertTrue(
            os.path.isfile(WORKFLOW_PATH),
            f"Expected workflow file at {WORKFLOW_PATH}",
        )

    def test_workflow_name_unchanged(self):
        self.assertRegex(
            self.content,
            re.compile(r"^name:\s*Documentation CI\s*$", re.MULTILINE),
        )

    # ------------------------------------------------------------------
    # New step: Setup Node.js
    # ------------------------------------------------------------------
    def test_setup_node_step_exists(self):
        block = _get_step_block(self.content, "Setup Node.js")
        self.assertIsNotNone(block, "Expected a 'Setup Node.js' step to be present")

    def test_setup_node_step_uses_expected_action(self):
        block = _get_step_block(self.content, "Setup Node.js")
        self.assertTrue(
            "uses: actions/setup-node@v4" in block or "uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020" in block
        )
            "uses: actions/setup-node@v4" in block
            or "uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020" in block
        )
        self.assertIn("uses: actions/setup-node@v4", block)

    def test_setup_node_step_pins_node_version_22(self):
        block = _get_step_block(self.content, "Setup Node.js")
        self.assertRegex(block, re.compile(r'node-version:\s*"22"'))

    def test_setup_node_step_has_no_extra_configuration(self):
        """The 'with:' block for Setup Node.js should only declare
        node-version, and nothing else."""
        block = _get_step_block(self.content, "Setup Node.js")
        with_match = re.search(r"^([ \t]*)with:\s*\n", block, flags=re.MULTILINE)
        self.assertIsNotNone(with_match, "Expected a 'with:' block")
        indent = len(with_match.group(1))
        child_keys = re.findall(
            r"^[ \t]{" + str(indent + 1) + r",}(\w[\w-]*):", block, flags=re.MULTILINE
        )
        self.assertEqual(child_keys, ["node-version"])

    def test_setup_node_step_appears_between_checkout_and_python(self):
        checkout_idx = self.content.index("- name: Checkout Code")
        node_idx = self.content.index("- name: Setup Node.js")
        python_idx = self.content.index("- name: Setup Python")
        self.assertLess(checkout_idx, node_idx)
        self.assertLess(node_idx, python_idx)

    def test_setup_node_step_appears_exactly_once(self):
        self.assertEqual(self.content.count("- name: Setup Node.js"), 1)

    # ------------------------------------------------------------------
    # Regression checks: pre-existing steps must remain untouched
    # ------------------------------------------------------------------
    def test_checkout_step_unchanged(self):
        block = _get_step_block(self.content, "Checkout Code")
        self.assertIn(
            "uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4",
            block,
        )
        self.assertIn("persist-credentials: false", block)
        self.assertIn("fetch-depth: 0", block)

    def test_setup_python_step_unchanged(self):
        block = _get_step_block(self.content, "Setup Python")
        self.assertIn(
            "uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5",
            block,
        )
        self.assertRegex(block, re.compile(r'python-version:\s*"3\.12"'))

    def test_install_dependencies_step_unchanged(self):
        block = _get_step_block(self.content, "Install Dependencies")
        self.assertIn("pip install PyYAML", block)

    def test_verify_frontmatter_step_unchanged(self):
        block = _get_step_block(
            self.content, "Verify Frontmatter Preparation & Formatting"
        )
        self.assertIn("python scripts/prepare_docs.py", block)

    def test_test_suite_step_unchanged(self):
        block = _get_step_block(self.content, "Execute Comprehensive Test Suite")
        self.assertIn("python3 -m unittest discover -s tests", block)

    def test_job_and_runner_unchanged(self):
        self.assertRegex(
            self.content, re.compile(r"^\s{2}validate-docs:\s*$", re.MULTILINE)
        )
        self.assertIn("runs-on: ubuntu-latest", self.content)

    def test_triggers_unchanged(self):
        self.assertRegex(self.content, re.compile(r'branches:\s*\["main"\]'))
        self.assertRegex(self.content, re.compile(r"^\s{2}pull_request:\s*$", re.MULTILINE))

    def test_permissions_unchanged(self):
        self.assertIn("contents: read", self.content)


if __name__ == "__main__":
    unittest.main()