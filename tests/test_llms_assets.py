#!/usr/bin/env python3
"""
Unit tests for GitBook configuration, Table of Contents, and generated LLM assets.
"""

import os
import sys
import tempfile
import unittest
import subprocess
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import generate_llms_assets

class TestLlmsAssetsAndGitBook(unittest.TestCase):
    def test_gitbook_yaml_syntax_and_values(self):
        gb_yaml_path = os.path.join(REPO_ROOT, ".gitbook.yaml")
        self.assertTrue(os.path.exists(gb_yaml_path))
        with open(gb_yaml_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('version: "1.0.0"', content)
        self.assertIn('root: ./', content)
        self.assertIn('readme: README.md', content)
        self.assertIn('summary: SUMMARY.md', content)

    def test_summary_md_structure(self):
        summary_path = os.path.join(REPO_ROOT, "SUMMARY.md")
        self.assertTrue(os.path.exists(summary_path))
        with open(summary_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("# Table of Contents", content)
        self.assertIn("* [Introduction](README.md)", content)
        self.assertIn("docs/engineering/", content)
        self.assertIn("docs/executive/", content)

    def test_python_api_parsing(self):
        sample_txt = """# Project Name
> This is a project summary blockquote.

Intro info text.

## Section A
- [Document 1](README.md) : First description.
- [Document 2](docs/legal-notice.md)

## Optional
- [Doc 3](AGENTS.md) : Optional desc.
"""
        parsed = generate_llms_assets.parse_llms_file(sample_txt)
        self.assertEqual(parsed.title, "Project Name")
        self.assertEqual(parsed.summary, "This is a project summary blockquote.")
        self.assertEqual(parsed.info, "Intro info text.")
        self.assertIn("Section A", parsed.sections)
        self.assertIn("Optional", parsed.sections)
        self.assertEqual(len(parsed.sections["Section A"]), 2)
        self.assertEqual(parsed.sections["Section A"][0]["title"], "Document 1")
        self.assertEqual(parsed.sections["Section A"][0]["url"], "README.md")
        self.assertEqual(parsed.sections["Section A"][0]["desc"], "First description.")

    def test_python_api_xml_generation(self):
        sample_txt = """# Project Title
> Project summary.

## Section 1
- [Doc 1](README.md) : Description.
"""
        xml_ctx = generate_llms_assets.create_ctx(sample_txt, optional=False)
        self.assertIn('<project title="Project Title" summary="Project summary.">', xml_ctx)
        self.assertIn('<section title="Section 1">', xml_ctx)
        self.assertIn('<document title="Doc 1" url="README.md" desc="Description.">', xml_ctx)

    def test_file_existence_and_matching(self):
        root_full = os.path.join(REPO_ROOT, "llms-full.txt")
        docs_full = os.path.join(REPO_ROOT, "docs", "llms-full.txt")
        root_xml = os.path.join(REPO_ROOT, "llms-context.xml")
        docs_xml = os.path.join(REPO_ROOT, "docs", "llms-context.xml")

        self.assertTrue(os.path.exists(root_full))
        self.assertTrue(os.path.exists(docs_full))
        self.assertTrue(os.path.exists(root_xml))
        self.assertTrue(os.path.exists(docs_xml))

        with open(root_full, "r", encoding="utf-8") as f1, open(docs_full, "r", encoding="utf-8") as f2:
            self.assertEqual(f1.read(), f2.read())

        with open(root_xml, "r", encoding="utf-8") as f1, open(docs_xml, "r", encoding="utf-8") as f2:
            self.assertEqual(f1.read(), f2.read())

    def test_xml_is_well_formed(self):
        root_xml_path = os.path.join(REPO_ROOT, "llms-context.xml")
        try:
            ET.parse(root_xml_path)
        except ET.ParseError as e:
            self.fail(f"llms-context.xml is not valid XML: {e}")

    def test_cli_execution(self):
        script_path = os.path.join(SCRIPTS_DIR, "generate_llms_assets.py")
        llms_txt_path = os.path.join(REPO_ROOT, "llms.txt")

        result = subprocess.run(
            [sys.executable, script_path, llms_txt_path, "--optional", "True"],
            capture_output=True,
            text=True,
            check=True
        )

        self.assertIn("<project ", result.stdout)
        self.assertIn("</project>", result.stdout)


class TestAttrDict(unittest.TestCase):
    """Unit tests for the generate_llms_assets.AttrDict helper class."""

    def test_attribute_read_returns_item_value(self):
        d = generate_llms_assets.AttrDict({"foo": "bar"})
        self.assertEqual(d.foo, "bar")
        self.assertEqual(d["foo"], "bar")

    def test_attribute_write_sets_item_value(self):
        d = generate_llms_assets.AttrDict()
        d.title = "My Title"
        self.assertEqual(d["title"], "My Title")
        self.assertEqual(d.title, "My Title")

    def test_missing_attribute_raises_attribute_error(self):
        d = generate_llms_assets.AttrDict()
        with self.assertRaises(AttributeError):
            _ = d.does_not_exist

    def test_is_still_a_regular_dict(self):
        d = generate_llms_assets.AttrDict({"a": 1, "b": 2})
        self.assertIsInstance(d, dict)
        self.assertEqual(sorted(d.keys()), ["a", "b"])


class TestStripFrontMatter(unittest.TestCase):
    """Unit tests for generate_llms_assets.strip_front_matter."""

    def test_strips_front_matter_block(self):
        content = (
            "---\n"
            "layout: default\n"
            'title: "Hello"\n'
            "---\n"
            "# Hello World\n"
            "Body text.\n"
        )
        result = generate_llms_assets.strip_front_matter(content)
        self.assertNotIn("layout: default", result)
        self.assertTrue(result.startswith("# Hello World"))

    def test_content_without_front_matter_is_unchanged(self):
        content = "# Just a heading\n\nSome body text.\n"
        result = generate_llms_assets.strip_front_matter(content)
        self.assertEqual(result, content)

    def test_leading_whitespace_before_front_matter_is_handled(self):
        content = "\n\n---\nokf_version: \"0.1\"\n---\nBody\n"
        result = generate_llms_assets.strip_front_matter(content)
        self.assertEqual(result, "Body\n")

    def test_incomplete_front_matter_delimiter_is_left_untouched(self):
        # Only a single '---' delimiter present, no closing delimiter pair
        content = "---\nThis is not valid front matter because there's only one delimiter.\n"
        result = generate_llms_assets.strip_front_matter(content)
        self.assertEqual(result, content)

    def test_empty_string_returns_empty_string(self):
        self.assertEqual(generate_llms_assets.strip_front_matter(""), "")


class TestParseLlmsFile(unittest.TestCase):
    """Unit tests for generate_llms_assets.parse_llms_file."""

    def test_no_sections_returns_empty_sections_dict(self):
        parsed = generate_llms_assets.parse_llms_file("# Title Only\n\n> Summary.\n")
        self.assertEqual(parsed.title, "Title Only")
        self.assertEqual(parsed.summary, "Summary.")
        self.assertEqual(dict(parsed.sections), {})

    def test_crlf_line_endings_are_normalized(self):
        sample_txt = (
            "# CRLF Title\r\n"
            "> CRLF summary.\r\n"
            "\r\n"
            "## Section A\r\n"
            "- [Doc](README.md) : Desc.\r\n"
        )
        parsed = generate_llms_assets.parse_llms_file(sample_txt)
        self.assertEqual(parsed.title, "CRLF Title")
        self.assertEqual(parsed.summary, "CRLF summary.")
        self.assertIn("Section A", parsed.sections)
        self.assertEqual(parsed.sections["Section A"][0]["title"], "Doc")

    def test_multiline_blockquote_summary_is_joined(self):
        sample_txt = (
            "# Title\n"
            "> Line one of summary.\n"
            "> Line two of summary.\n"
        )
        parsed = generate_llms_assets.parse_llms_file(sample_txt)
        self.assertEqual(parsed.summary, "Line one of summary.\nLine two of summary.")

    def test_info_paragraph_preserves_internal_blank_lines(self):
        sample_txt = (
            "# Title\n"
            "> Summary.\n"
            "\n"
            "Info paragraph line one.\n"
            "\n"
            "Info paragraph line two.\n"
        )
        parsed = generate_llms_assets.parse_llms_file(sample_txt)
        self.assertEqual(
            parsed.info,
            "Info paragraph line one.\n\nInfo paragraph line two."
        )

    def test_link_without_description_has_none_desc(self):
        sample_txt = "# Title\n\n## Section A\n- [Doc](docs/foo.md)\n"
        parsed = generate_llms_assets.parse_llms_file(sample_txt)
        link = parsed.sections["Section A"][0]
        self.assertEqual(link["title"], "Doc")
        self.assertEqual(link["url"], "docs/foo.md")
        self.assertIsNone(link["desc"])

    def test_malformed_link_lines_are_skipped(self):
        sample_txt = (
            "# Title\n\n"
            "## Section A\n"
            "This line is not a markdown link and should be ignored.\n"
            "- [Valid Doc](docs/valid.md) : A valid entry.\n"
        )
        parsed = generate_llms_assets.parse_llms_file(sample_txt)
        links = parsed.sections["Section A"]
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["title"], "Valid Doc")

    def test_missing_title_defaults_to_empty_string(self):
        sample_txt = "> Just a summary, no H1 title.\n"
        parsed = generate_llms_assets.parse_llms_file(sample_txt)
        self.assertEqual(parsed.title, "")

    def test_multiple_sections_preserve_order(self):
        sample_txt = (
            "# Title\n\n"
            "## Zebra\n"
            "- [A](a.md)\n\n"
            "## Alpha\n"
            "- [B](b.md)\n"
        )
        parsed = generate_llms_assets.parse_llms_file(sample_txt)
        self.assertEqual(list(parsed.sections.keys()), ["Zebra", "Alpha"])


class TestEscapeXmlText(unittest.TestCase):
    """Unit tests for generate_llms_assets.escape_xml_text."""

    def test_none_returns_empty_string(self):
        self.assertEqual(generate_llms_assets.escape_xml_text(None), "")

    def test_all_special_characters_are_escaped(self):
        raw = '<tag attr="value">Tom & Jerry\'s</tag>'
        escaped = generate_llms_assets.escape_xml_text(raw)
        self.assertEqual(
            escaped,
            "&lt;tag attr=&quot;value&quot;&gt;Tom &amp; Jerry&apos;s&lt;/tag&gt;"
        )
        self.assertNotIn("<", escaped)
        self.assertNotIn(">", escaped)
        self.assertNotIn('"', escaped)

    def test_non_string_input_is_stringified(self):
        self.assertEqual(generate_llms_assets.escape_xml_text(42), "42")

    def test_plain_text_without_special_characters_is_unchanged(self):
        self.assertEqual(generate_llms_assets.escape_xml_text("plain text"), "plain text")


class TestCreateCtx(unittest.TestCase):
    """Unit tests for generate_llms_assets.create_ctx."""

    def setUp(self):
        self._prev_cwd = os.getcwd()
        os.chdir(REPO_ROOT)

    def tearDown(self):
        os.chdir(self._prev_cwd)

    def test_optional_section_excluded_by_default(self):
        sample_txt = (
            "# Title\n\n"
            "## Section A\n"
            "- [Doc 1](README.md)\n\n"
            "## Optional\n"
            "- [Doc 2](AGENTS.md)\n"
        )
        xml_ctx = generate_llms_assets.create_ctx(sample_txt, optional=False)
        self.assertIn('<section title="Section A">', xml_ctx)
        self.assertNotIn('<section title="Optional">', xml_ctx)

    def test_optional_section_included_when_requested(self):
        sample_txt = (
            "# Title\n\n"
            "## optional\n"
            "- [Doc 2](AGENTS.md)\n"
        )
        xml_ctx = generate_llms_assets.create_ctx(sample_txt, optional=True)
        self.assertIn('<section title="optional">', xml_ctx)

    def test_optional_section_matching_is_case_insensitive(self):
        sample_txt = "# Title\n\n## OPTIONAL\n- [Doc](AGENTS.md)\n"
        xml_ctx = generate_llms_assets.create_ctx(sample_txt, optional=False)
        self.assertNotIn('<section title="OPTIONAL">', xml_ctx)

    def test_existing_local_file_content_is_embedded_without_front_matter(self):
        sample_txt = "# Title\n\n## Section A\n- [Legal](docs/legal-notice.md)\n"
        xml_ctx = generate_llms_assets.create_ctx(sample_txt, optional=False)
        self.assertNotIn("okf_version", xml_ctx)
        self.assertIn("Legal Notice", xml_ctx)

    def test_missing_local_file_produces_not_found_message(self):
        sample_txt = "# Title\n\n## Section A\n- [Ghost](docs/does-not-exist-xyz.md)\n"
        xml_ctx = generate_llms_assets.create_ctx(sample_txt, optional=False)
        self.assertIn("File docs/does-not-exist-xyz.md not found.", xml_ctx)

    def test_external_url_produces_external_document_message(self):
        sample_txt = "# Title\n\n## Section A\n- [External](https://example.com/doc)\n"
        xml_ctx = generate_llms_assets.create_ctx(sample_txt, optional=False)
        self.assertIn("External document: https://example.com/doc", xml_ctx)

    def test_directory_path_produces_read_error_message(self):
        sample_txt = "# Title\n\n## Section A\n- [Docs Dir](docs)\n"
        xml_ctx = generate_llms_assets.create_ctx(sample_txt, optional=False)
        self.assertIn("Error reading file docs:", xml_ctx)

    def test_link_with_description_includes_desc_attribute(self):
        sample_txt = "# Title\n\n## Section A\n- [Doc](README.md) : Has description.\n"
        xml_ctx = generate_llms_assets.create_ctx(sample_txt, optional=False)
        self.assertIn('desc="Has description."', xml_ctx)

    def test_link_without_description_omits_desc_attribute(self):
        sample_txt = "# Title\n\n## Section A\n- [Doc](README.md)\n"
        xml_ctx = generate_llms_assets.create_ctx(sample_txt, optional=False)
        self.assertIn('<document title="Doc" url="README.md">', xml_ctx)
        self.assertNotIn("desc=", xml_ctx)

    def test_output_starts_and_ends_with_project_tags(self):
        sample_txt = "# Title\n> Summary.\n"
        xml_ctx = generate_llms_assets.create_ctx(sample_txt, optional=False)
        self.assertTrue(xml_ctx.startswith('<project title="Title" summary="Summary.">'))
        self.assertTrue(xml_ctx.endswith('</project>'))


class TestCompileLlmsFull(unittest.TestCase):
    """Unit tests for generate_llms_assets.compile_llms_full."""

    def setUp(self):
        self._prev_cwd = os.getcwd()
        os.chdir(REPO_ROOT)

    def tearDown(self):
        os.chdir(self._prev_cwd)

    def test_title_summary_and_info_are_rendered(self):
        sample_txt = "# My Project\n> A summary.\n\nSome intro info.\n\n## Section A\n- [Doc](README.md)\n"
        result = generate_llms_assets.compile_llms_full(sample_txt)
        self.assertTrue(result.startswith("# My Project\n\n> A summary.\n\nSome intro info."))
        self.assertIn("# Section: Section A", result)
        self.assertIn("## Doc", result)

    def test_existing_local_file_content_is_embedded_without_front_matter(self):
        sample_txt = "# Title\n\n## Section A\n- [Legal](docs/legal-notice.md)\n"
        result = generate_llms_assets.compile_llms_full(sample_txt)
        self.assertNotIn("okf_version", result)
        self.assertIn("Legal Notice", result)

    def test_missing_local_file_produces_not_found_message(self):
        sample_txt = "# Title\n\n## Section A\n- [Ghost](docs/does-not-exist-xyz.md)\n"
        result = generate_llms_assets.compile_llms_full(sample_txt)
        self.assertIn("*File docs/does-not-exist-xyz.md not found.*", result)

    def test_external_url_produces_markdown_link_message(self):
        sample_txt = "# Title\n\n## Section A\n- [External](https://example.com/doc)\n"
        result = generate_llms_assets.compile_llms_full(sample_txt)
        self.assertIn("External document: [External](https://example.com/doc)", result)

    def test_description_is_rendered_in_italics(self):
        sample_txt = "# Title\n\n## Section A\n- [Doc](README.md) : A helpful description.\n"
        result = generate_llms_assets.compile_llms_full(sample_txt)
        self.assertIn("*A helpful description.*", result)

    def test_sections_are_separated_by_horizontal_rules(self):
        sample_txt = "# Title\n\n## Section A\n- [Doc](README.md)\n"
        result = generate_llms_assets.compile_llms_full(sample_txt)
        self.assertIn("---", result.split("# Section: Section A", 1)[0])
        self.assertIn("---", result.split("# Section: Section A", 1)[1])


class TestGenerateAll(unittest.TestCase):
    """Integration tests for generate_llms_assets.generate_all, which regenerates
    the repository's llms-full.txt and llms-context.xml assets in-place.

    These assertions mirror the pattern used by tests/test_sitemaps.py, which
    also regenerates real repository assets as part of its test run.
    """

    def test_generate_all_produces_matching_root_and_docs_assets(self):
        generate_llms_assets.generate_all()

        root_full = os.path.join(REPO_ROOT, "llms-full.txt")
        docs_full = os.path.join(REPO_ROOT, "docs", "llms-full.txt")
        root_xml = os.path.join(REPO_ROOT, "llms-context.xml")
        docs_xml = os.path.join(REPO_ROOT, "docs", "llms-context.xml")

        for path in (root_full, docs_full, root_xml, docs_xml):
            self.assertTrue(os.path.exists(path))

        with open(root_full, "r", encoding="utf-8") as f1, open(docs_full, "r", encoding="utf-8") as f2:
            self.assertEqual(f1.read(), f2.read())

        with open(root_xml, "r", encoding="utf-8") as f1, open(docs_xml, "r", encoding="utf-8") as f2:
            self.assertEqual(f1.read(), f2.read())

    def test_generate_all_xml_output_is_well_formed(self):
        generate_llms_assets.generate_all()
        root_xml = os.path.join(REPO_ROOT, "llms-context.xml")
        try:
            ET.parse(root_xml)
        except ET.ParseError as e:
            self.fail(f"Regenerated llms-context.xml is not valid XML: {e}")

    def test_generate_all_is_idempotent(self):
        generate_llms_assets.generate_all()
        root_full = os.path.join(REPO_ROOT, "llms-full.txt")
        with open(root_full, "r", encoding="utf-8") as f:
            first_run = f.read()

        generate_llms_assets.generate_all()
        with open(root_full, "r", encoding="utf-8") as f:
            second_run = f.read()

        self.assertEqual(first_run, second_run)


class TestCliEdgeCases(unittest.TestCase):
    """Additional CLI edge case tests for scripts/generate_llms_assets.py."""

    def setUp(self):
        self.script_path = os.path.join(SCRIPTS_DIR, "generate_llms_assets.py")

    def test_help_flag_prints_usage_and_exits_zero(self):
        result = subprocess.run(
            [sys.executable, self.script_path, "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: python3 generate_llms_assets.py", result.stdout)

    def test_short_help_flag_prints_usage_and_exits_zero(self):
        result = subprocess.run(
            [sys.executable, self.script_path, "-h"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: python3 generate_llms_assets.py", result.stdout)

    def test_nonexistent_input_file_exits_nonzero_with_error(self):
        result = subprocess.run(
            [sys.executable, self.script_path, "/nonexistent/path/llms.txt"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Error:", result.stderr)

    def test_optional_flag_defaults_to_false(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            llms_path = os.path.join(tmp_dir, "llms.txt")
            with open(llms_path, "w", encoding="utf-8") as f:
                f.write("# T\n\n## Optional\n- [Doc](README.md)\n")

            result = subprocess.run(
                [sys.executable, self.script_path, llms_path],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                check=True,
            )
            self.assertNotIn('<section title="Optional">', result.stdout)

    def test_optional_flag_true_variants_include_optional_section(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            llms_path = os.path.join(tmp_dir, "llms.txt")
            with open(llms_path, "w", encoding="utf-8") as f:
                f.write("# T\n\n## Optional\n- [Doc](README.md)\n")

            for truthy_value in ["True", "true", "1", "yes", "t"]:
                with self.subTest(value=truthy_value):
                    result = subprocess.run(
                        [sys.executable, self.script_path, llms_path, "--optional", truthy_value],
                        capture_output=True,
                        text=True,
                        cwd=REPO_ROOT,
                        check=True,
                    )
                    self.assertIn('<section title="Optional">', result.stdout)

    def test_optional_flag_false_variants_exclude_optional_section(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            llms_path = os.path.join(tmp_dir, "llms.txt")
            with open(llms_path, "w", encoding="utf-8") as f:
                f.write("# T\n\n## Optional\n- [Doc](README.md)\n")

            for falsy_value in ["False", "false", "0", "no", "nonsense"]:
                with self.subTest(value=falsy_value):
                    result = subprocess.run(
                        [sys.executable, self.script_path, llms_path, "--optional", falsy_value],
                        capture_output=True,
                        text=True,
                        cwd=REPO_ROOT,
                        check=True,
                    )
                    self.assertNotIn('<section title="Optional">', result.stdout)


if __name__ == "__main__":
    unittest.main()
