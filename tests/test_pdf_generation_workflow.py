#!/usr/bin/env python3
"""Unit tests for .github/workflows/pdf-generation.yml.

These tests validate the GitHub Actions workflow that generates a PDF
snapshot of the project's GitHub Pages site. The workflow file is treated
as plain text (rather than parsed with a YAML library) because PyYAML is
not guaranteed to be available in every environment that runs this
repository's test suite. Regex-based assertions keep the tests dependency
free while still pinning down the exact structure of the workflow.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_pdf_generation_workflow
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
        "pdf-generation.yml",
    )
)


class PdfGenerationWorkflowTestCase(unittest.TestCase):
    """Tests for the pdf-generation.yml GitHub Actions workflow."""

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
            re.compile(r"^name:\s*Generate Page PDF\s*$", re.MULTILINE),
        )

    def _get_on_block(self):
        """Extract the raw text of the `on:` trigger block."""
        match = re.search(
            r"^on:\n((?:[ \t]+.*\n|\n)+)",
            self.content,
            flags=re.MULTILINE,
        )
        self.assertIsNotNone(match, "Could not locate top-level 'on:' block")
        return match.group(1)

    # ------------------------------------------------------------------
    # New trigger: workflow_dispatch
    # ------------------------------------------------------------------
    def test_workflow_dispatch_trigger_added(self):
        on_block = self._get_on_block()
        self.assertRegex(
            on_block,
            re.compile(r"^\s{2}workflow_dispatch:\s*$", re.MULTILINE),
            msg="Expected 'workflow_dispatch:' trigger to be present under 'on:'",
        )

    def test_workflow_dispatch_has_no_extra_config(self):
        """workflow_dispatch should be a bare trigger (no inputs) on this PR."""
        on_block = self._get_on_block()
        line = next(
            (l for l in on_block.splitlines() if "workflow_dispatch" in l), None
        )
        self.assertIsNotNone(line)
        self.assertEqual(line.strip(), "workflow_dispatch:")

    def test_push_trigger_still_present(self):
        """Regression: adding workflow_dispatch must not remove the push trigger."""
        on_block = self._get_on_block()
        self.assertRegex(on_block, re.compile(r"^\s{2}push:\s*$", re.MULTILINE))
        self.assertRegex(on_block, r'branches:\s*\["main"\]')

    def test_on_block_only_declares_expected_triggers(self):
        on_block = self._get_on_block()
        top_level_keys = re.findall(r"^\s{2}(\w+):", on_block, flags=re.MULTILINE)
        self.assertEqual(sorted(top_level_keys), sorted(["push", "workflow_dispatch"]))

    # ------------------------------------------------------------------
    # Target URL change
    # ------------------------------------------------------------------
    def _get_step_block(self, step_name):
        pattern = (
            r"- name:\s*"
            + re.escape(step_name)
            + r"\n((?:(?!- name:).*\n)*)"
        )
        match = re.search(pattern, self.content)
        self.assertIsNotNone(match, f"Could not locate step '{step_name}'")
        return match.group(1)

    def test_webpage_to_pdf_step_uses_updated_url(self):
        step_block = self._get_step_block("Webpage to PDF")
        self.assertIn(
            "webPageURL: 'https://linuxmalaysia.github.io/"
            "aws-3tier-deployment-for-php-infra/'",
            step_block,
        )

    def test_old_url_no_longer_present(self):
        """Regression: the previous target URL must not linger anywhere in the file."""
        self.assertNotIn("songketmail", self.content)
        self.assertNotIn("aws-3tier-deployment-for-ai-infra", self.content)

    def test_webpage_url_is_well_formed_https_url(self):
        step_block = self._get_step_block("Webpage to PDF")
        match = re.search(r"webPageURL:\s*'([^']+)'", step_block)
        self.assertIsNotNone(match)
        url = match.group(1)
        self.assertRegex(
            url,
            r"^https://[a-zA-Z0-9.-]+\.github\.io/[a-zA-Z0-9._-]+/$",
            msg=f"webPageURL '{url}' does not look like a valid GitHub Pages URL",
        )

    def test_url_uses_https_scheme(self):
        step_block = self._get_step_block("Webpage to PDF")
        match = re.search(r"webPageURL:\s*'([^']+)'", step_block)
        self.assertIsNotNone(match)
        self.assertTrue(match.group(1).startswith("https://"))

    # ------------------------------------------------------------------
    # Regression checks: unrelated fields/steps must remain untouched
    # ------------------------------------------------------------------
    def test_pdf_action_version_unchanged(self):
        step_block = self._get_step_block("Webpage to PDF")
        self.assertIn("uses: misaelnieto/web_to_pdf_action@v0.3.1", step_block)

    def test_output_file_path_unchanged(self):
        step_block = self._get_step_block("Webpage to PDF")
        self.assertIn("outputFile: './docs/assets/output.pdf'", step_block)

    def test_use_puppeteer_flag_unchanged(self):
        step_block = self._get_step_block("Webpage to PDF")
        self.assertIn("usePuppeteer: true", step_block)

    def test_pdf_options_unchanged(self):
        step_block = self._get_step_block("Webpage to PDF")
        self.assertIn(
            'pdfOptions: \'{"format": "A4", "printBackground": true}\'',
            step_block,
        )

    def test_checkout_step_unchanged(self):
        step_block = self._get_step_block("Checkout Repository")
        self.assertIn("uses: actions/checkout@v4", step_block)

    def test_upload_artifact_step_unchanged(self):
        step_block = self._get_step_block("Upload PDF Artifact")
        self.assertIn("uses: actions/upload-artifact@v4", step_block)
        self.assertIn("name: page-pdf", step_block)
        self.assertIn("path: ./docs/assets/output.pdf", step_block)

    def test_job_and_runner_unchanged(self):
        self.assertRegex(
            self.content, re.compile(r"^\s{2}build-pdf:\s*$", re.MULTILINE)
        )
        self.assertIn("runs-on: ubuntu-latest", self.content)

    # ------------------------------------------------------------------
    # New step: Setup Node.js
    # ------------------------------------------------------------------
    def test_setup_node_step_exists(self):
        step_block = self._get_step_block("Setup Node.js")
        self.assertIsNotNone(step_block)

    def test_setup_node_step_uses_expected_action(self):
        step_block = self._get_step_block("Setup Node.js")
        self.assertIn("uses: actions/setup-node@v4", step_block)

    def test_setup_node_step_pins_node_version_22(self):
        step_block = self._get_step_block("Setup Node.js")
        self.assertRegex(step_block, re.compile(r'node-version:\s*"22"'))

    def test_setup_node_step_appears_between_checkout_and_pdf_step(self):
        checkout_idx = self.content.index("- name: Checkout Repository")
        node_idx = self.content.index("- name: Setup Node.js")
        pdf_idx = self.content.index("- name: Webpage to PDF")
        self.assertLess(checkout_idx, node_idx)
        self.assertLess(node_idx, pdf_idx)

    def test_setup_node_step_appears_exactly_once(self):
        self.assertEqual(self.content.count("- name: Setup Node.js"), 1)


if __name__ == "__main__":
    unittest.main()