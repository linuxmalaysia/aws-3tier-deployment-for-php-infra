#!/usr/bin/env python3
"""Unit tests for the Python ignore rules added to .gitignore in this PR.

This PR appends three new patterns to the repository's `.gitignore`:

    # Python files to ignore
    __pycache__/
    *.py[cod]
    *$py.class

These tests use ``git check-ignore`` (rather than re-implementing gitignore
pattern matching) so the assertions exercise the exact same matching engine
Git itself uses, which is the most reliable way to validate the behavior of
these rules.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_gitignore
"""
import os
import subprocess
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GITIGNORE_PATH = os.path.join(REPO_ROOT, ".gitignore")


def _is_ignored(relative_path):
    """Return True if `git check-ignore` reports the given path (relative
    to the repo root) as ignored by the current .gitignore rules."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--", relative_path],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


class GitignorePythonRulesTestCase(unittest.TestCase):
    """Tests for the new '# Python files to ignore' block in .gitignore."""

    @classmethod
    def setUpClass(cls):
        with open(GITIGNORE_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_gitignore_file_exists(self):
        self.assertTrue(os.path.isfile(GITIGNORE_PATH))

    def test_python_section_comment_present(self):
        self.assertIn("# Python files to ignore", self.content)

    def test_pycache_directory_pattern_present(self):
        self.assertIn("__pycache__/", self.content)

    def test_compiled_python_pattern_present(self):
        self.assertIn("*.py[cod]", self.content)

    def test_jython_class_pattern_present(self):
        self.assertIn("*$py.class", self.content)

    def test_python_section_appears_after_shell_scripts_section(self):
        shell_idx = self.content.index("# Shell scripts and logs")
        python_idx = self.content.index("# Python files to ignore")
        self.assertLess(shell_idx, python_idx)

    def test_each_new_pattern_appears_exactly_once(self):
        for pattern in ["__pycache__/", "*.py[cod]", "*$py.class"]:
            with self.subTest(pattern=pattern):
                self.assertEqual(self.content.count(pattern), 1)

    def test_preexisting_terraform_rules_are_untouched(self):
        """Regression: appending the new Python section should not have
        disturbed the pre-existing Terraform ignore rules."""
        for pattern in [
            "*.tfstate",
            ".terraform/",
            ".terraform.lock.hcl",
            "terraform.rc",
        ]:
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, self.content)


class GitignoreJekyllRulesTestCase(unittest.TestCase):
    """Tests for the new '# Jekyll build artifacts' block in .gitignore,
    which adds an ignore rule for the '_site/' directory produced by the
    `actions/jekyll-build-pages@v1` step in
    .github/workflows/jekyll-gh-pages.yml (destination: ./_site)."""

    @classmethod
    def setUpClass(cls):
        with open(GITIGNORE_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_jekyll_section_comment_present(self):
        self.assertIn("# Jekyll build artifacts", self.content)

    def test_site_directory_pattern_present(self):
        self.assertIn("_site/", self.content)

    def test_pattern_appears_exactly_once(self):
        self.assertEqual(self.content.count("_site/"), 1)

    def test_jekyll_section_appears_after_shell_scripts_section(self):
        shell_idx = self.content.index("# Shell scripts and logs")
        jekyll_idx = self.content.index("# Jekyll build artifacts")
        self.assertLess(shell_idx, jekyll_idx)

    def test_jekyll_section_appears_before_python_section(self):
        jekyll_idx = self.content.index("# Jekyll build artifacts")
        python_idx = self.content.index("# Python files to ignore")
        self.assertLess(jekyll_idx, python_idx)


class GitignoreJekyllRulesMatchingTestCase(unittest.TestCase):
    """Functional tests verifying the new '_site/' pattern actually
    matches/excludes the intended paths when evaluated by Git's own ignore
    engine."""

    def test_top_level_site_directory_is_ignored(self):
        for relpath in ["_site/index.html", "_site/assets/style.css"]:
            with self.subTest(relpath=relpath):
                self.assertTrue(_is_ignored(relpath), f"{relpath} should be ignored")

    def test_nested_site_directory_is_ignored(self):
        """The pattern has no leading slash, so it must match '_site'
        directories at any depth, not just at the repository root."""
        for relpath in ["docs/_site/index.html", "nested/deep/_site/page.html"]:
            with self.subTest(relpath=relpath):
                self.assertTrue(_is_ignored(relpath), f"{relpath} should be ignored")

    def test_unrelated_paths_with_similar_names_are_not_ignored(self):
        """Boundary check: the pattern only matches a directory literally
        named '_site', not files/directories that merely contain that
        substring."""
        for relpath in ["site/index.html", "docs/_site_data.txt", "_sites/index.html"]:
            with self.subTest(relpath=relpath):
                self.assertFalse(
                    _is_ignored(relpath), f"{relpath} should NOT be ignored"
                )

    def test_docs_source_markdown_is_not_ignored(self):
        self.assertFalse(_is_ignored("docs/index.md"))


class GitignorePythonRulesMatchingTestCase(unittest.TestCase):
    """Functional tests verifying the new patterns actually match/exclude
    the intended files when evaluated by Git's own ignore engine."""

    def test_pycache_directory_anywhere_is_ignored(self):
        for relpath in [
            "scripts/__pycache__/prepare_docs.cpython-312.pyc",
            "tests/__pycache__/test_prepare_docs.cpython-312.pyc",
            "nested/deep/__pycache__/module.cpython-39.pyc",
        ]:
            with self.subTest(relpath=relpath):
                self.assertTrue(_is_ignored(relpath), f"{relpath} should be ignored")

    def test_compiled_python_extensions_are_ignored(self):
        for relpath in ["scripts/module.pyc", "scripts/module.pyo", "scripts/module.pyd"]:
            with self.subTest(relpath=relpath):
                self.assertTrue(_is_ignored(relpath), f"{relpath} should be ignored")

    def test_jython_class_files_are_ignored(self):
        self.assertTrue(_is_ignored("scripts/SomeModule$py.class"))

    def test_python_source_files_are_not_ignored(self):
        for relpath in ["scripts/prepare_docs.py", "tests/test_prepare_docs.py"]:
            with self.subTest(relpath=relpath):
                self.assertFalse(
                    _is_ignored(relpath), f"{relpath} should NOT be ignored"
                )

    def test_unrelated_extension_pyx_is_not_ignored(self):
        """Negative/boundary check: the `*.py[cod]` character class only
        covers 'c', 'o', and 'd' -- an unrelated extension like `.pyx`
        (Cython source) must not be swept up by the new rule."""
        self.assertFalse(_is_ignored("scripts/module.pyx"))

    def test_markdown_docs_are_not_ignored(self):
        for relpath in ["docs/performance-testing.md", "docs/production-costing.md"]:
            with self.subTest(relpath=relpath):
                self.assertFalse(_is_ignored(relpath))

    def test_previously_committed_pycache_artifacts_are_now_ignored(self):
        """Regression: the exact .pyc paths that this PR removed from
        version control (because they are build artifacts) must now be
        covered by the updated .gitignore."""
        for relpath in [
            "scripts/__pycache__/prepare_docs.cpython-312.pyc",
            "tests/__pycache__/test_pdf_generation_workflow.cpython-312.pyc",
            "tests/__pycache__/test_pdf_generation_workflow.cpython-39.pyc",
            "tests/__pycache__/test_prepare_docs.cpython-312.pyc",
            "tests/__pycache__/test_production_costing_docs.cpython-312.pyc",
        ]:
            with self.subTest(relpath=relpath):
                self.assertTrue(_is_ignored(relpath))


if __name__ == "__main__":
    unittest.main()