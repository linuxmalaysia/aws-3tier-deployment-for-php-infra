#!/usr/bin/env python3
"""Unit tests for .github/workflows/jekyll-gh-pages.yml.

This PR adds a new "Setup Node.js" step (using `actions/setup-node@v4`
pinned to `node-version: "22"`) to the `build` job, inserted between the
"Checkout" and "Setup Python" steps. The workflow file is treated as plain
text (rather than parsed with a YAML library) to stay dependency free,
following the pattern already used by
`tests/test_pdf_generation_workflow.py`.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_jekyll_gh_pages_workflow
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
        "jekyll-gh-pages.yml",
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


class JekyllGhPagesWorkflowTestCase(unittest.TestCase):
    """Tests for the jekyll-gh-pages.yml GitHub Actions workflow."""

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
            re.compile(
                r"^name:\s*Deploy Jekyll with GitHub Pages dependencies "
                r"preinstalled\s*$",
                re.MULTILINE,
            ),
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

    def test_setup_node_step_pins_node_version_22(self):
        block = _get_step_block(self.content, "Setup Node.js")
        self.assertRegex(block, re.compile(r'node-version:\s*"22"'))

    def test_setup_node_step_appears_between_checkout_and_python(self):
        checkout_idx = self.content.index("- name: Checkout")
        node_idx = self.content.index("- name: Setup Node.js")
        python_idx = self.content.index("- name: Setup Python")
        self.assertLess(checkout_idx, node_idx)
        self.assertLess(node_idx, python_idx)

    def test_setup_node_step_appears_exactly_once(self):
        self.assertEqual(self.content.count("- name: Setup Node.js"), 1)

    def test_setup_node_step_only_appears_in_build_job(self):
        """The 'deploy' job only has a 'Deploy to GitHub Pages' step and
        must not have gained a Node.js setup step of its own."""
        deploy_job_match = re.search(
            r"^\s{2}deploy:\n(.*)\Z", self.content, flags=re.MULTILINE | re.DOTALL
        )
        self.assertIsNotNone(deploy_job_match)
        self.assertNotIn("Setup Node.js", deploy_job_match.group(1))

    # ------------------------------------------------------------------
    # Regression checks: pre-existing steps must remain untouched
    # ------------------------------------------------------------------
    def test_checkout_step_unchanged(self):
        block = _get_step_block(self.content, "Checkout")
        self.assertIn("uses: actions/checkout@v4", block)

    def test_setup_python_step_unchanged(self):
        block = _get_step_block(self.content, "Setup Python")
        self.assertIn("uses: actions/setup-python@v5", block)
        self.assertRegex(block, re.compile(r'python-version:\s*"3\.12"'))

    def test_prepare_markdown_front_matter_step_unchanged(self):
        block = _get_step_block(self.content, "Prepare Markdown Front Matter")
        self.assertIn("python scripts/prepare_docs.py", block)

    def test_build_with_jekyll_step_unchanged(self):
        block = _get_step_block(self.content, "Build with Jekyll")
        self.assertIn("uses: actions/jekyll-build-pages@v1", block)
        self.assertIn("source: ./docs", block)
        self.assertIn("destination: ./_site", block)

    def test_deploy_job_unchanged(self):
        self.assertRegex(self.content, re.compile(r"^\s{2}deploy:\s*$", re.MULTILINE))
        deploy_block = _get_step_block(self.content, "Deploy to GitHub Pages")
        self.assertIn("uses: actions/deploy-pages@v5", deploy_block)

    def test_build_job_and_runner_unchanged(self):
        self.assertRegex(self.content, re.compile(r"^\s{2}build:\s*$", re.MULTILINE))
        self.assertIn("runs-on: ubuntu-latest", self.content)

    def test_triggers_unchanged(self):
        self.assertRegex(self.content, re.compile(r'branches:\s*\["main"\]'))
        self.assertRegex(
            self.content, re.compile(r"^\s{2}workflow_dispatch:\s*$", re.MULTILINE)
        )


if __name__ == "__main__":
    unittest.main()