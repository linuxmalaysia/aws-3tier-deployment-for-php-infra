#!/usr/bin/env python3
"""Unit tests for the `render_with_liquid: false` front matter field added
in this PR to three documentation pages:

    * docs/how-to/audit-ansible-and-podman.md
    * docs/reference/static-analysis-rules.md
    * docs/tutorials/setup-development-sandbox.md

`render_with_liquid` is not (yet) processed by `scripts/prepare_docs.py`
or referenced by `docs/_config.yml`; it is a plain "extra" OKF front
matter field. These tests validate that the field is present, has the
expected boolean type/value, sits in the correct position in each file's
front matter block, and that the surrounding required OKF fields were left
intact by the change.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_render_with_liquid_frontmatter
"""
import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import prepare_docs  # noqa: E402  (import after sys.path manipulation)

DOC_PATHS = {
    "audit-ansible-and-podman": os.path.join(
        REPO_ROOT, "docs", "how-to", "audit-ansible-and-podman.md"
    ),
    "static-analysis-rules": os.path.join(
        REPO_ROOT, "docs", "reference", "static-analysis-rules.md"
    ),
    "setup-development-sandbox": os.path.join(
        REPO_ROOT, "docs", "tutorials", "setup-development-sandbox.md"
    ),
}


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _split_front_matter(content):
    """Return (front_matter_text, body_text) for a file that starts with a
    '---' delimited YAML front matter block."""
    stripped = content.lstrip()
    assert stripped.startswith("---"), "Expected file to start with '---' front matter delimiter"
    parts = stripped.split("---", 2)
    return parts[1], parts[2]


class RenderWithLiquidFieldPresenceTestCase(unittest.TestCase):
    """Verify each changed doc declares `render_with_liquid: false` and
    that the surrounding required OKF fields survived the edit."""

    @classmethod
    def setUpClass(cls):
        cls.docs = {}
        for key, path in DOC_PATHS.items():
            content = _read(path)
            fm_text, body_text = _split_front_matter(content)
            cls.docs[key] = {
                "path": path,
                "content": content,
                "front_matter_text": fm_text,
                "body_text": body_text,
                "front_matter": prepare_docs.parse_yaml_front_matter(fm_text),
            }

    def test_all_three_files_exist(self):
        for key, path in DOC_PATHS.items():
            with self.subTest(doc=key):
                self.assertTrue(os.path.isfile(path), f"Missing file: {path}")

    def test_render_with_liquid_key_present(self):
        for key, doc in self.docs.items():
            with self.subTest(doc=key):
                self.assertIn("render_with_liquid", doc["front_matter"])

    def test_render_with_liquid_value_is_boolean_false(self):
        for key, doc in self.docs.items():
            with self.subTest(doc=key):
                value = doc["front_matter"]["render_with_liquid"]
                self.assertIs(value, False)

    def test_render_with_liquid_literal_text_matches_expected_format(self):
        """Regression: the raw text in the file must be the bare YAML
        boolean literal `false` (not quoted, not `False`/`no`/`0`)."""
        for key, doc in self.docs.items():
            with self.subTest(doc=key):
                self.assertIn("render_with_liquid: false", doc["content"])

    def test_required_okf_fields_still_present(self):
        for key, doc in self.docs.items():
            with self.subTest(doc=key):
                for required_key in [
                    "layout",
                    "okf_version",
                    "type",
                    "title",
                    "timestamp",
                    "topics",
                ]:
                    self.assertIn(required_key, doc["front_matter"])

    def test_okf_version_unchanged(self):
        for key, doc in self.docs.items():
            with self.subTest(doc=key):
                self.assertEqual(doc["front_matter"]["okf_version"], "0.1")

    def test_layout_unchanged(self):
        for key, doc in self.docs.items():
            with self.subTest(doc=key):
                self.assertEqual(doc["front_matter"]["layout"], "default")

    def test_topics_remain_lists_of_strings(self):
        for key, doc in self.docs.items():
            with self.subTest(doc=key):
                topics = doc["front_matter"]["topics"]
                self.assertIsInstance(topics, list)
                self.assertTrue(all(isinstance(t, str) for t in topics))

    def test_timestamp_unchanged_value(self):
        for key, doc in self.docs.items():
            with self.subTest(doc=key):
                self.assertEqual(
                    doc["front_matter"]["timestamp"], "2026-08-05T22:30:00+08:00"
                )

    def test_render_with_liquid_is_last_field_before_closing_delimiter(self):
        """render_with_liquid was appended as the final line of the front
        matter block, immediately before the closing '---'."""
        for key, doc in self.docs.items():
            with self.subTest(doc=key):
                lines = [
                    line
                    for line in doc["front_matter_text"].splitlines()
                    if line.strip()
                ]
                self.assertTrue(lines, "Front matter should not be empty")
                self.assertEqual(lines[-1].strip(), "render_with_liquid: false")

    def test_render_with_liquid_appears_exactly_once_per_file(self):
        for key, doc in self.docs.items():
            with self.subTest(doc=key):
                self.assertEqual(doc["content"].count("render_with_liquid"), 1)

    def test_body_heading_still_matches_title(self):
        """Regression: appending the new field must not have disturbed the
        Markdown body -- the first heading should still match the OKF
        `title` field."""
        for key, doc in self.docs.items():
            with self.subTest(doc=key):
                heading_match = prepare_docs.HEADING_PATTERN.search(doc["body_text"])
                self.assertIsNotNone(heading_match)
                heading_text = heading_match.group(1).strip()
                self.assertEqual(heading_text, doc["front_matter"]["title"])


class RenderWithLiquidNotAppliedElsewhereTestCase(unittest.TestCase):
    """Guard against accidental over-application: only the three targeted
    files in this PR should declare `render_with_liquid`."""

    def test_field_is_scoped_to_the_three_expected_files(self):
        matches = []
        for root, dirs, files in os.walk(os.path.join(REPO_ROOT, "docs")):
            for filename in files:
                if not filename.endswith(".md"):
                    continue
                path = os.path.join(root, filename)
                if "render_with_liquid" in _read(path):
                    matches.append(os.path.normpath(path))

        expected = sorted(os.path.normpath(p) for p in DOC_PATHS.values())
        self.assertEqual(sorted(matches), expected)


if __name__ == "__main__":
    unittest.main()