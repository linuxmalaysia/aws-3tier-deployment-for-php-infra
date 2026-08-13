#!/usr/bin/env python3
"""
Unit tests for GitBook configuration, Table of Contents, and generated LLM assets.
"""

import os
import sys
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

Introductory text containing &, <, and > symbols to test XML escaping.

## Section 1
- [Doc 1](README.md) : Description.
"""
        xml_ctx = generate_llms_assets.create_ctx(sample_txt, optional=False)
        self.assertIn('<project title="Project Title" summary="Project summary.">', xml_ctx)
        self.assertIn('Introductory text containing &amp;, &lt;, and &gt; symbols', xml_ctx)
        self.assertIn('<section title="Section 1">', xml_ctx)
        self.assertIn('<document title="Doc 1" url="README.md" desc="Description.">', xml_ctx)

        # Verify it parses as valid XML
        try:
            ET.fromstring(xml_ctx)
        except ET.ParseError as e:
            self.fail(f"Generated XML is not valid: {e}")

    def test_file_existence_and_matching(self):
        root_full = os.path.join(REPO_ROOT, "llms-full.txt")
        docs_full = os.path.join(REPO_ROOT, "docs", "llms-full.txt")
        root_xml = os.path.join(REPO_ROOT, "llms-context.xml")
        docs_xml = os.path.join(REPO_ROOT, "docs", "llms-context.xml")
        llms_txt_path = os.path.join(REPO_ROOT, "llms.txt")

        self.assertTrue(os.path.exists(root_full))
        self.assertTrue(os.path.exists(docs_full))
        self.assertTrue(os.path.exists(root_xml))
        self.assertTrue(os.path.exists(docs_xml))
        self.assertTrue(os.path.exists(llms_txt_path))

        # Read the current llms.txt source
        with open(llms_txt_path, "r", encoding="utf-8") as f:
            llms_content = f.read()

        # Generate expected contents using current repo_root base directory
        expected_full = generate_llms_assets.compile_llms_full(llms_content, base_dir=REPO_ROOT)
        expected_xml = generate_llms_assets.create_ctx(llms_content, optional=True, base_dir=REPO_ROOT)

        # Validate both root and docs copies against their generated expected content
        with open(root_full, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), expected_full)
        with open(docs_full, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), expected_full)

        with open(root_xml, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), expected_xml)
        with open(docs_xml, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), expected_xml)

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

if __name__ == "__main__":
    unittest.main()
