#!/usr/bin/env python3
"""Unit tests for .github/workflows/opentofu.yml.

This PR adds a new "Setup Node.js" step (using `actions/setup-node@v4`
pinned to `node-version: "22"`) to the `opentofu-lint-and-validate` job,
inserted between the "Checkout Code" and "Setup OpenTofu" steps. The
workflow file is treated as plain text (rather than parsed with a YAML
library) to stay dependency free, following the pattern already used by
`tests/test_pdf_generation_workflow.py`.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_opentofu_workflow
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
        "opentofu.yml",
    )
)


def _get_job_block(content, job_name):
    """Extract the raw text of a top-level job block (2-space indented key)
    up to (but not including) the next 2-space indented top-level key."""
    pattern = (
        r"^\s{2}"
        + re.escape(job_name)
        + r":\n((?:(?!^\s{2}\S).*\n?)*)"
    )
    match = re.search(pattern, content, flags=re.MULTILINE)
    return match.group(1) if match else None


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


class OpentofuWorkflowTestCase(unittest.TestCase):
    """Tests for the opentofu.yml GitHub Actions workflow."""

    @classmethod
    def setUpClass(cls):
        with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()
        cls.lint_job = _get_job_block(cls.content, "opentofu-lint-and-validate")

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
            re.compile(r'^name:\s*"OpenTofu CI/CD"\s*$', re.MULTILINE),
        )

    def test_lint_job_block_extracted(self):
        self.assertIsNotNone(
            self.lint_job, "Could not locate the opentofu-lint-and-validate job"
        )

    # ------------------------------------------------------------------
    # New step: Setup Node.js
    # ------------------------------------------------------------------
    def test_setup_node_step_exists_in_lint_job(self):
        block = _get_step_block(self.lint_job, "Setup Node.js")
        self.assertIsNotNone(block, "Expected a 'Setup Node.js' step in the lint job")

    def test_setup_node_step_uses_expected_action(self):
        block = _get_step_block(self.lint_job, "Setup Node.js")
        self.assertTrue(
            "uses: actions/setup-node@v4" in block
            or "uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020" in block
        )

    def test_setup_node_step_pins_node_version_22(self):
        block = _get_step_block(self.lint_job, "Setup Node.js")
        self.assertRegex(block, re.compile(r'node-version:\s*"22"'))

    def test_setup_node_step_appears_between_checkout_and_opentofu_setup(self):
        checkout_idx = self.lint_job.index("- name: Checkout Code")
        node_idx = self.lint_job.index("- name: Setup Node.js")
        tofu_idx = self.lint_job.index("- name: Setup OpenTofu")
        self.assertLess(checkout_idx, node_idx)
        self.assertLess(node_idx, tofu_idx)

    def test_setup_node_step_appears_exactly_once_in_whole_workflow(self):
        """Regression: only the lint-and-validate job should have gained a
        Node.js setup step; the plan/apply jobs must not."""
        self.assertEqual(self.content.count("- name: Setup Node.js"), 1)

    def test_plan_and_apply_jobs_have_no_node_setup(self):
        plan_job = _get_job_block(self.content, "opentofu-plan")
        apply_job = _get_job_block(self.content, "opentofu-apply")
        self.assertIsNotNone(plan_job)
        self.assertIsNotNone(apply_job)
        self.assertNotIn("Setup Node.js", plan_job)
        self.assertNotIn("Setup Node.js", apply_job)

    # ------------------------------------------------------------------
    # Regression checks: pre-existing steps/jobs must remain untouched
    # ------------------------------------------------------------------
    def test_checkout_step_unchanged(self):
        block = _get_step_block(self.lint_job, "Checkout Code")
        self.assertIn("uses: actions/checkout@v4", block)

    def test_setup_opentofu_step_unchanged(self):
        block = _get_step_block(self.lint_job, "Setup OpenTofu")
        self.assertIn("uses: opentofu/setup-opentofu@v1", block)
        self.assertRegex(block, re.compile(r'tofu_version:\s*"1\.8\.2"'))

    def test_format_check_init_validate_steps_unchanged(self):
        self.assertIn("run: tofu fmt -check -recursive", self.lint_job)
        self.assertIn("tofu init -backend=false", self.lint_job)
        self.assertIn("tofu validate", self.lint_job)

    def test_lint_job_name_and_runner_unchanged(self):
        self.assertIn('name: "OpenTofu Lint & Validate"', self.lint_job)
        self.assertIn("runs-on: ubuntu-latest", self.lint_job)

    def test_plan_job_dependency_unchanged(self):
        plan_job = _get_job_block(self.content, "opentofu-plan")
        self.assertIn("needs: opentofu-lint-and-validate", plan_job)
        self.assertIn("if: github.event_name == 'pull_request'", plan_job)

    def test_apply_job_dependency_unchanged(self):
        apply_job = _get_job_block(self.content, "opentofu-apply")
        self.assertIn("needs: opentofu-lint-and-validate", apply_job)
        self.assertIn(
            "if: github.ref == 'refs/heads/main' && github.event_name == 'push'",
            apply_job,
        )

    def test_triggers_and_permissions_unchanged(self):
        self.assertIn("id-token: write", self.content)
        self.assertIn("contents: read", self.content)
        self.assertRegex(self.content, re.compile(r"^\s{6}- main\s*$", re.MULTILINE))


if __name__ == "__main__":
    unittest.main()