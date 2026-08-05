#!/usr/bin/env python3
"""Unit tests for scripts/prepare_docs.py.

These tests cover the OKF (Open Knowledge Format) front matter helpers that
were added/rewritten in this PR: ``infer_okf_type``, ``infer_okf_topics``,
``get_git_timestamp``, ``parse_yaml_front_matter``, ``format_yaml_front_matter``,
``process_markdown_file`` and ``main``.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_prepare_docs
"""
import datetime
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, call

SCRIPTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "scripts")
)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import prepare_docs  # noqa: E402  (import after sys.path manipulation)


class InferOkfTypeTestCase(unittest.TestCase):
    """Tests for prepare_docs.infer_okf_type."""

    def test_changelog_filename(self):
        self.assertEqual(prepare_docs.infer_okf_type("CHANGELOG.md"), "Changelog")

    def test_history_filename(self):
        self.assertEqual(prepare_docs.infer_okf_type("HISTORY.md"), "History")

    def test_readme_filename(self):
        self.assertEqual(prepare_docs.infer_okf_type("README.md"), "Portal")

    def test_agents_filename(self):
        self.assertEqual(
            prepare_docs.infer_okf_type("AGENTS.md"), "Agent Operating Instructions"
        )

    def test_skill_filename(self):
        self.assertEqual(prepare_docs.infer_okf_type("SKILL.md"), "Agent Skill")

    def test_filename_matching_is_case_insensitive(self):
        # filename.lower() is used for the special-case filenames.
        self.assertEqual(prepare_docs.infer_okf_type("Changelog.MD"), "Changelog")
        self.assertEqual(prepare_docs.infer_okf_type("Readme.Md"), "Portal")

    def test_terraform_modules_non_readme_file(self):
        self.assertEqual(
            prepare_docs.infer_okf_type("terraform/modules/vpc/USAGE.md"),
            "Module README",
        )

    def test_terraform_modules_non_readme_file_with_windows_separators(self):
        self.assertEqual(
            prepare_docs.infer_okf_type("terraform\\modules\\vpc\\USAGE.md"),
            "Module README",
        )

    def test_readme_filename_takes_precedence_over_path_checks(self):
        """Regression: the filename=='readme.md' check runs before the
        'terraform/modules' path substring check, so module README files are
        typed as 'Portal', matching the actual repository convention."""
        self.assertEqual(
            prepare_docs.infer_okf_type("terraform/modules/vpc/README.md"),
            "Portal",
        )

    def test_docs_modules_guide(self):
        self.assertEqual(
            prepare_docs.infer_okf_type("docs/modules/vpc.md"),
            "Module Technical Guide",
        )

    def test_docs_index(self):
        self.assertEqual(
            prepare_docs.infer_okf_type("docs/index.md"), "Documentation Index"
        )

    def test_docs_generic_reference_guide(self):
        self.assertEqual(
            prepare_docs.infer_okf_type("docs/architecture.md"),
            "Technical Reference Guide",
        )

    def test_default_type_for_unrecognized_path(self):
        self.assertEqual(
            prepare_docs.infer_okf_type("misc/notes.md"), "Technical Documentation"
        )

    def test_path_substring_checks_are_case_sensitive(self):
        """Regression: only the filename check is lower-cased; the 'docs/' and
        'terraform/modules' substring checks operate on the raw path, so an
        upper-cased directory does not match."""
        self.assertEqual(
            prepare_docs.infer_okf_type("DOCS/architecture.md"),
            "Technical Documentation",
        )


class InferOkfTopicsTestCase(unittest.TestCase):
    """Tests for prepare_docs.infer_okf_topics."""

    def test_preserves_existing_nonempty_topics(self):
        existing = ["custom", "topic"]
        result = prepare_docs.infer_okf_topics("docs/vpc.md", existing)
        self.assertEqual(result, existing)

    def test_ignores_empty_existing_topics(self):
        result = prepare_docs.infer_okf_topics("docs/vpc.md", [])
        self.assertEqual(result, ["aws", "3-tier", "vpc", "networking"])

    def test_ignores_non_list_existing_topics(self):
        result = prepare_docs.infer_okf_topics("docs/vpc.md", "not-a-list")
        self.assertEqual(result, ["aws", "3-tier", "vpc", "networking"])

    def test_ignores_none_existing_topics(self):
        result = prepare_docs.infer_okf_topics("docs/vpc.md", None)
        self.assertEqual(result, ["aws", "3-tier", "vpc", "networking"])

    def test_default_topics_when_no_keyword_matches(self):
        result = prepare_docs.infer_okf_topics("docs/architecture.md")
        self.assertEqual(result, ["aws", "3-tier"])

    def test_vpc_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/modules/vpc.md"),
            ["aws", "3-tier", "vpc", "networking"],
        )

    def test_security_groups_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/modules/security_groups.md"),
            ["aws", "3-tier", "security", "firewall"],
        )

    def test_waf_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/modules/waf.md"),
            ["aws", "3-tier", "security", "firewall"],
        )

    def test_rds_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/modules/rds.md"),
            ["aws", "3-tier", "database", "rds"],
        )

    def test_postgresql_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/postgresql-comparison.md"),
            ["aws", "3-tier", "database", "rds"],
        )

    def test_elasticache_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/modules/elasticache.md"),
            ["aws", "3-tier", "caching", "valkey"],
        )

    def test_valkey_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("some-valkey-notes.md"),
            ["aws", "3-tier", "caching", "valkey"],
        )

    def test_asg_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/modules/asg.md"),
            ["aws", "3-tier", "compute", "autoscaling"],
        )

    def test_jumphost_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/jumphost.md"),
            ["aws", "3-tier", "security", "bastion"],
        )

    def test_bastion_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("bastion-notes.md"),
            ["aws", "3-tier", "security", "bastion"],
        )

    def test_cost_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/costing.md"),
            ["aws", "3-tier", "finops", "costing"],
        )

    def test_cicd_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/cicd.md"),
            ["aws", "3-tier", "cicd", "automation"],
        )

    def test_gitlab_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/gitlab-efs-cicd.md"),
            ["aws", "3-tier", "cicd", "automation"],
        )

    def test_migration_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/opentofu-migration.md"),
            ["aws", "3-tier", "opentofu", "migration"],
        )

    def test_agent_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("AGENTS.md"),
            ["aws", "3-tier", "ai-agents", "instructions"],
        )

    def test_skill_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("SKILL.md"),
            ["aws", "3-tier", "ai-agents", "instructions"],
        )

    def test_php_keyword(self):
        self.assertEqual(
            prepare_docs.infer_okf_topics("docs/codeigniter-php-fpm.md"),
            ["aws", "3-tier", "php", "codeigniter"],
        )

    def test_first_matching_branch_wins(self):
        """The keyword checks are an if/elif chain, so only the first
        matching keyword's topics are applied even if multiple keywords
        appear in the filename."""
        result = prepare_docs.infer_okf_topics("vpc-security_groups.md")
        self.assertEqual(result, ["aws", "3-tier", "vpc", "networking"])

    def test_no_duplicate_topics_returned(self):
        result = prepare_docs.infer_okf_topics("docs/modules/vpc.md")
        self.assertEqual(len(result), len(set(result)))


class GetGitTimestampTestCase(unittest.TestCase):
    """Tests for prepare_docs.get_git_timestamp."""

    def test_returns_git_commit_timestamp_when_available(self):
        with patch(
            "prepare_docs.subprocess.check_output",
            return_value=b"2026-01-01T00:00:00+08:00\n",
        ) as mock_check_output:
            result = prepare_docs.get_git_timestamp("docs/architecture.md")
        self.assertEqual(result, "2026-01-01T00:00:00+08:00")
        mock_check_output.assert_called_once()

    def test_falls_back_to_mtime_when_git_unavailable(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            expected = datetime.datetime.fromtimestamp(
                os.path.getmtime(tmp_path)
            ).isoformat()
            with patch(
                "prepare_docs.subprocess.check_output",
                side_effect=Exception("git not found"),
            ):
                result = prepare_docs.get_git_timestamp(tmp_path)
            self.assertEqual(result, expected)
        finally:
            os.remove(tmp_path)

    def test_falls_back_to_current_time_when_everything_fails(self):
        with patch(
            "prepare_docs.subprocess.check_output",
            side_effect=Exception("git not found"),
        ):
            with patch("prepare_docs.datetime") as mock_datetime:
                mock_datetime.datetime.now.return_value.isoformat.return_value = (
                    "FAKE_NOW"
                )
                result = prepare_docs.get_git_timestamp(
                    "/this/path/does/not/exist/file.md"
                )
        self.assertEqual(result, "FAKE_NOW")

    def test_empty_git_output_falls_back_to_mtime(self):
        """An empty (falsy) string from git log should not be treated as a
        valid timestamp."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            expected = datetime.datetime.fromtimestamp(
                os.path.getmtime(tmp_path)
            ).isoformat()
            with patch("prepare_docs.subprocess.check_output", return_value=b""):
                result = prepare_docs.get_git_timestamp(tmp_path)
            self.assertEqual(result, expected)
        finally:
            os.remove(tmp_path)


class ParseYamlFrontMatterTestCase(unittest.TestCase):
    """Tests for prepare_docs.parse_yaml_front_matter."""

    def test_parses_scalar_string_values(self):
        fm = "layout: default\ntype: Portal\n"
        result = prepare_docs.parse_yaml_front_matter(fm)
        self.assertEqual(result, {"layout": "default", "type": "Portal"})

    def test_parses_double_and_single_quoted_values(self):
        fm = 'title: "My Title"\nokf_version: \'0.1\'\n'
        result = prepare_docs.parse_yaml_front_matter(fm)
        self.assertEqual(result["title"], "My Title")
        self.assertEqual(result["okf_version"], "0.1")

    def test_parses_boolean_values(self):
        fm = "draft: true\npublished: false\n"
        result = prepare_docs.parse_yaml_front_matter(fm)
        self.assertIs(result["draft"], True)
        self.assertIs(result["published"], False)

    def test_parses_inline_array(self):
        fm = "topics: [aws, 3-tier, vpc]\n"
        result = prepare_docs.parse_yaml_front_matter(fm)
        self.assertEqual(result["topics"], ["aws", "3-tier", "vpc"])

    def test_parses_inline_array_with_quoted_items(self):
        fm = 'topics: ["aws", \'3-tier\']\n'
        result = prepare_docs.parse_yaml_front_matter(fm)
        self.assertEqual(result["topics"], ["aws", "3-tier"])

    def test_parses_multiline_list(self):
        fm = "tags:\n  - alpha\n  - beta\n"
        result = prepare_docs.parse_yaml_front_matter(fm)
        self.assertEqual(result["tags"], ["alpha", "beta"])

    def test_parses_multiline_list_with_quoted_items(self):
        fm = "tags:\n  - 'alpha'\n  - \"beta\"\n"
        result = prepare_docs.parse_yaml_front_matter(fm)
        self.assertEqual(result["tags"], ["alpha", "beta"])

    def test_ignores_blank_lines_and_comments(self):
        fm = "\n# a comment\nlayout: default\n\n"
        result = prepare_docs.parse_yaml_front_matter(fm)
        self.assertEqual(result, {"layout": "default"})

    def test_empty_front_matter_returns_empty_dict(self):
        result = prepare_docs.parse_yaml_front_matter("")
        self.assertEqual(result, {})

    def test_mixed_scalars_and_lists(self):
        fm = (
            "layout: default\n"
            "okf_version: \"0.1\"\n"
            "type: Portal\n"
            "title: \"Mixed Doc\"\n"
            "topics: [aws, 3-tier]\n"
        )
        result = prepare_docs.parse_yaml_front_matter(fm)
        self.assertEqual(
            result,
            {
                "layout": "default",
                "okf_version": "0.1",
                "type": "Portal",
                "title": "Mixed Doc",
                "topics": ["aws", "3-tier"],
            },
        )


class FormatYamlFrontMatterTestCase(unittest.TestCase):
    """Tests for prepare_docs.format_yaml_front_matter."""

    def test_full_field_set_and_order(self):
        data = {
            "layout": "default",
            "okf_version": "0.1",
            "type": "Portal",
            "title": "My Title",
            "timestamp": "2026-08-05T22:20:36+08:00",
            "topics": ["aws", "3-tier"],
        }
        result = prepare_docs.format_yaml_front_matter(data)
        expected = (
            "---\n"
            "layout: default\n"
            'okf_version: "0.1"\n'
            "type: Portal\n"
            'title: "My Title"\n'
            "timestamp: 2026-08-05T22:20:36+08:00\n"
            "topics: [aws, 3-tier]\n"
            "---"
        )
        self.assertEqual(result, expected)

    def test_omits_layout_line_when_not_present(self):
        data = {
            "okf_version": "0.1",
            "type": "Portal",
            "title": "No Layout",
            "timestamp": "2026-08-05T22:20:36+08:00",
            "topics": ["aws"],
        }
        result = prepare_docs.format_yaml_front_matter(data)
        self.assertNotIn("layout:", result)

    def test_title_with_embedded_quotes_is_not_re_quoted(self):
        data = {"title": 'My "Special" Title', "topics": []}
        result = prepare_docs.format_yaml_front_matter(data)
        self.assertIn('title: My "Special" Title\n', result)

    def test_title_without_quotes_gets_wrapped(self):
        data = {"title": "Plain Title", "topics": []}
        result = prepare_docs.format_yaml_front_matter(data)
        self.assertIn('title: "Plain Title"\n', result)

    def test_non_list_topics_written_without_brackets(self):
        data = {"title": "T", "topics": "not-a-list"}
        result = prepare_docs.format_yaml_front_matter(data)
        self.assertIn("topics: not-a-list\n", result)
        self.assertNotIn("topics: [", result)

    def test_extra_boolean_field_lowercased(self):
        data = {"title": "T", "topics": [], "draft": True}
        result = prepare_docs.format_yaml_front_matter(data)
        self.assertIn("draft: true\n", result)

    def test_extra_list_field_wrapped_in_brackets(self):
        data = {"title": "T", "topics": [], "aliases": ["a", "b"]}
        result = prepare_docs.format_yaml_front_matter(data)
        self.assertIn("aliases: [a, b]\n", result)

    def test_extra_plain_string_field_gets_quoted(self):
        data = {"title": "T", "topics": [], "author": "Jane"}
        result = prepare_docs.format_yaml_front_matter(data)
        self.assertIn('author: "Jane"\n', result)

    def test_extra_string_field_with_quote_is_not_re_quoted(self):
        data = {"title": "T", "topics": [], "note": "It's here"}
        result = prepare_docs.format_yaml_front_matter(data)
        self.assertIn("note: It's here\n", result)

    def test_extra_fields_are_sorted_alphabetically(self):
        data = {"title": "T", "topics": [], "zeta": "z", "alpha": "a"}
        result = prepare_docs.format_yaml_front_matter(data)
        alpha_idx = result.index("alpha:")
        zeta_idx = result.index("zeta:")
        self.assertLess(alpha_idx, zeta_idx)

    def test_defaults_used_when_okf_fields_missing(self):
        data = {"title": "T", "topics": []}
        result = prepare_docs.format_yaml_front_matter(data)
        self.assertIn('okf_version: "0.1"\n', result)
        self.assertIn("type: Technical Documentation\n", result)


class ProcessMarkdownFileTestCase(unittest.TestCase):
    """Tests for prepare_docs.process_markdown_file."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.docs_dir = os.path.join(self.tmp_dir.name, "docs")
        os.makedirs(self.docs_dir, exist_ok=True)
        self.get_ts_patcher = patch(
            "prepare_docs.get_git_timestamp",
            return_value="2026-01-01T00:00:00+08:00",
        )
        self.get_ts_patcher.start()

    def tearDown(self):
        self.get_ts_patcher.stop()
        self.tmp_dir.cleanup()

    def _write(self, name, content):
        path = os.path.join(self.docs_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _read(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_adds_front_matter_when_missing(self):
        path = self._write("sample.md", "# Hello World\n\nSome body text.\n")
        prepare_docs.process_markdown_file(path)
        result = self._read(path)
        self.assertTrue(result.startswith("---\n"))
        self.assertIn('okf_version: "0.1"\n', result)
        self.assertIn("type: Technical Reference Guide\n", result)
        self.assertIn('title: "Hello World"\n', result)
        self.assertIn("timestamp: 2026-01-01T00:00:00+08:00\n", result)
        self.assertIn("topics: [aws, 3-tier]\n", result)
        self.assertTrue(result.endswith("# Hello World\n\nSome body text.\n"))

    def test_title_strips_markdown_emphasis_and_code_markers(self):
        path = self._write("sample.md", "## **Bold** `code` Title\nBody\n")
        prepare_docs.process_markdown_file(path)
        result = self._read(path)
        self.assertIn('title: "Bold code Title"\n', result)

    def test_title_falls_back_to_filename_when_no_heading(self):
        path = self._write("my-cool-doc.md", "Just body text, no heading.\n")
        prepare_docs.process_markdown_file(path)
        result = self._read(path)
        self.assertIn('title: "My Cool Doc"\n', result)

    def test_merges_and_preserves_existing_front_matter_values(self):
        content = (
            "---\n"
            "layout: custom\n"
            'okf_version: "0.2"\n'
            "type: Custom Type\n"
            'title: "Existing Title"\n'
            "timestamp: 2020-01-01T00:00:00Z\n"
            "topics: [foo, bar]\n"
            "---\n"
            "\n"
            "Body content here.\n"
        )
        path = self._write("existing.md", content)
        prepare_docs.process_markdown_file(path)
        result = self._read(path)
        self.assertIn("layout: custom\n", result)
        self.assertIn('okf_version: "0.2"\n', result)
        self.assertIn("type: Custom Type\n", result)
        self.assertIn('title: "Existing Title"\n', result)
        self.assertIn("timestamp: 2020-01-01T00:00:00Z\n", result)
        self.assertIn("topics: [foo, bar]\n", result)
        self.assertTrue(result.endswith("Body content here.\n"))

    def test_migrates_legacy_tags_key_to_topics(self):
        content = (
            "---\n"
            "layout: default\n"
            'title: "Some Title"\n'
            "tags:\n"
            "  - alpha\n"
            "  - beta\n"
            "---\n"
            "\n"
            "Body.\n"
        )
        path = self._write("legacy-tags.md", content)
        prepare_docs.process_markdown_file(path)
        result = self._read(path)
        self.assertNotIn("tags:", result)
        self.assertIn("topics: [alpha, beta]\n", result)

    def test_malformed_front_matter_without_closing_delimiter_is_untouched(self):
        content = (
            "---\n"
            "layout: default\n"
            "title: incomplete, no closing delimiter\n"
            "More text without closing markers.\n"
        )
        path = self._write("malformed.md", content)
        prepare_docs.process_markdown_file(path)
        result = self._read(path)
        self.assertEqual(result, content)

    def test_existing_front_matter_missing_optional_fields_gets_defaults(self):
        content = "---\nlayout: default\n---\n\nBody only.\n"
        path = self._write("minimal.md", content)
        prepare_docs.process_markdown_file(path)
        result = self._read(path)
        self.assertIn('okf_version: "0.1"\n', result)
        self.assertIn("type: Technical Reference Guide\n", result)
        self.assertIn("timestamp: 2026-01-01T00:00:00+08:00\n", result)
        self.assertIn("topics: [aws, 3-tier]\n", result)


class MainTestCase(unittest.TestCase):
    """Tests for prepare_docs.main."""

    def test_walks_repo_and_processes_only_markdown_files_skipping_git_dir(self):
        fake_walk_results = [
            ("/repo", ["docs", ".git"], ["AGENTS.md", "notes.txt"]),
            ("/repo/docs", [], ["architecture.md", "image.png"]),
            ("/repo/.git", ["hooks"], ["config"]),
            ("/repo/.git/hooks", [], ["pre-commit.md"]),
        ]
        with patch("prepare_docs.os.walk", return_value=iter(fake_walk_results)):
            with patch("prepare_docs.process_markdown_file") as mock_process:
                prepare_docs.main()

        expected_calls = [
            call(os.path.join("/repo", "AGENTS.md")),
            call(os.path.join("/repo/docs", "architecture.md")),
        ]
        mock_process.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_process.call_count, 2)

    def test_does_not_process_non_markdown_files(self):
        fake_walk_results = [("/repo", [], ["README.rst", "script.py"])]
        with patch("prepare_docs.os.walk", return_value=iter(fake_walk_results)):
            with patch("prepare_docs.process_markdown_file") as mock_process:
                prepare_docs.main()
        mock_process.assert_not_called()


if __name__ == "__main__":
    unittest.main()