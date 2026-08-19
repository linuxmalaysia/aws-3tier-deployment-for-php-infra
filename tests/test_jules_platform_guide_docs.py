#!/usr/bin/env python3
"""Unit tests for the Google Jules Platform Guide documentation.

This test suite verifies:
- File presence and OKF v0.1 frontmatter metadata for ``docs/jules-platform-guide.md``.
- Structural content and required Diátaxis headings.
- Index registrations in ``docs/index.md``, ``docs/SUMMARY.md``, ``SUMMARY.md``, and ``llms.txt``.
- Sitemap indexing in ``sitemap.txt`` and ``sitemap.xml``.
"""

- Generated LLM context assets (``llms-context.xml`` and ``llms-full.txt``, root and docs copies).
- Basic sanity of the embedded example code blocks within the guide.
"""

import ast
import os
import re
import sys
import unittest
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import prepare_docs  # noqa: E402

JULES_GUIDE_PATH = os.path.join(REPO_ROOT, "docs", "jules-platform-guide.md")
INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
DOCS_SUMMARY_PATH = os.path.join(REPO_ROOT, "docs", "SUMMARY.md")
ROOT_SUMMARY_PATH = os.path.join(REPO_ROOT, "SUMMARY.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")

ROOT_SITEMAP_TXT = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_TXT = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_XML = os.path.join(REPO_ROOT, "sitemap.xml")
DOCS_SITEMAP_XML = os.path.join(REPO_ROOT, "docs", "sitemap.xml")

ROOT_LLMS_CONTEXT_XML = os.path.join(REPO_ROOT, "llms-context.xml")
DOCS_LLMS_CONTEXT_XML = os.path.join(REPO_ROOT, "docs", "llms-context.xml")
ROOT_LLMS_FULL_TXT = os.path.join(REPO_ROOT, "llms-full.txt")
DOCS_LLMS_FULL_TXT = os.path.join(REPO_ROOT, "docs", "llms-full.txt")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
GH_URL = "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/jules-platform-guide.html"
GB_URL = "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/jules-platform-guide"


def _read(path):
    """Read a UTF-8 text file.
    
    Parameters:
    	path: Path to the file to read.
    
    Returns:
    	str: The file contents.
    """
JULES_ENTRY_DESC = (
    "Detailed technical guide and operational showcase documenting repository "
    "bootstrap, OpenTofu IaC, Ansible automation, GitHub PR review comment "
    "workflows, Jules CLI/API setups, and Google Antigravity multi-agent "
    "orchestration."
)


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_front_matter(content):
    """Parse YAML front matter and body content from a document.
    
    Parameters:
    	content (str): Document content containing front matter delimited by `---`.
    
    Returns:
    	tuple: Parsed front matter metadata and the document body text.
    """
    stripped = content.lstrip()
    parts = stripped.split("---", 2)
    front_matter_text = parts[1]
    body_text = parts[2]
    front_matter = prepare_docs.parse_yaml_front_matter(front_matter_text)
    return front_matter, body_text


class TestJulesPlatformGuideFrontMatter(unittest.TestCase):
    """Tests for the OKF v0.1 front matter of docs/jules-platform-guide.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(JULES_GUIDE_PATH)
        cls.front_matter, cls.body_text = _parse_front_matter(cls.content)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(JULES_GUIDE_PATH))

    def test_starts_with_front_matter_delimiter(self):
        self.assertTrue(self.content.startswith("---\n"))

    def test_required_okf_fields_present(self):
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_layout_is_default(self):
        self.assertEqual(self.front_matter["layout"], "default")

    def test_okf_version_is_expected_value(self):
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_type_field_value(self):
        self.assertEqual(self.front_matter["type"], "Technical Reference Guide")

    def test_title_field_value(self):
        self.assertEqual(
            self.front_matter["title"],
            "Autonomous AI Pair-Programming & Multi-Agent Operations with Google Jules",
        )

    def test_topics_contain_jules_and_ai_agents(self):
        topics = self.front_matter["topics"]
        self.assertIn("jules", topics)
        self.assertIn("ai-agents", topics)
        self.assertIn("dsom", topics)
        self.assertIn("antigravity", topics)

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        self.assertEqual(heading_match.group(1).strip(), self.front_matter["title"])


class TestJulesPlatformGuideContentStructure(unittest.TestCase):
    """Tests for the structural content of docs/jules-platform-guide.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(JULES_GUIDE_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn(
            "# Autonomous AI Pair-Programming & Multi-Agent Operations with Google Jules",
            self.content,
        )

    def test_required_diataxis_sections_present(self):
        headings = [
            "## 1. Overview & Engineering Philosophy",
            "## 2. Step-by-Step Build & Implementation Log",
            "## 3. Collaborative Engineering via GitHub PR Comments",
            "## 4. Advanced Interoperability: Jules API, CLI, & Google Antigravity",
            "## 5. Why Developers Fall in Love with Google Jules",
            "## 6. Verification & Quality Gates",
        ]
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)

    def test_mentions_key_frameworks_and_tools(self):
        self.assertIn("OpenTofu", self.content)
        self.assertIn("Ansible", self.content)
        self.assertIn("IMDSv2", self.content)
        self.assertIn("Termux", self.content)
        self.assertIn("Google Antigravity", self.content)

    def test_concludes_with_dsom_footer(self):
        self.assertIn(
            "*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-05*",
            self.content,
        )


class TestJulesPlatformGuideIndexIntegrations(unittest.TestCase):
    """Tests for index links in docs/index.md, SUMMARY files, and llms.txt."""

    def test_index_md_contains_link(self):
        content = _read(INDEX_PATH)
        self.assertIn("jules-platform-guide.html", content)

    def test_index_md_link_present_with_bold_title_and_description(self):
        content = _read(INDEX_PATH)
        self.assertRegex(
            content,
            re.compile(
                r"\*\*\[Autonomous AI Pair-Programming & Multi-Agent Operations "
                r"with Google Jules\]\(jules-platform-guide\.html\):\*\*"
                r"\s*Comprehensive technical guide documenting end-to-end "
                r"repository creation"
            ),
        )

    def test_index_md_link_appears_in_deployment_cicd_section(self):
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n### |\n---|\Z)",
            _read(INDEX_PATH),
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn("jules-platform-guide.html", section_match.group(1))

    def test_index_md_link_uses_relative_html_url_not_markdown_extension(self):
        content = _read(INDEX_PATH)
        self.assertIn("(jules-platform-guide.html)", content)
        self.assertNotIn("(jules-platform-guide.md)", content)

    def test_index_md_link_appears_exactly_once(self):
        content = _read(INDEX_PATH)
        self.assertEqual(content.count("jules-platform-guide.html"), 1)

    def test_index_md_link_appears_before_wazuh_link(self):
        content = _read(INDEX_PATH)
        jules_idx = content.index("jules-platform-guide.html")
        wazuh_idx = content.index("engineering/wazuh-installation.html")
        self.assertLess(jules_idx, wazuh_idx)

    def test_docs_summary_contains_link(self):
        content = _read(DOCS_SUMMARY_PATH)
        self.assertIn("jules-platform-guide.md", content)

    def test_docs_summary_entry_exact_bullet_format(self):
        content = _read(DOCS_SUMMARY_PATH)
        self.assertIn(
            "* [Autonomous AI Pair-Programming with Google Jules](jules-platform-guide.md)",
            content,
        )

    def test_docs_summary_entry_in_deployment_automation_section(self):
        section_match = re.search(
            r"## Deployment, Automation, and Costing\n(.*?)(?=\n## |\Z)",
            _read(DOCS_SUMMARY_PATH),
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn("jules-platform-guide.md", section_match.group(1))

    def test_docs_summary_entry_is_first_item_in_its_section(self):
        section_match = re.search(
            r"## Deployment, Automation, and Costing\n(.*?)(?=\n## |\Z)",
            _read(DOCS_SUMMARY_PATH),
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        first_bullet = next(
            line for line in section_match.group(1).splitlines() if line.strip()
        )
        self.assertEqual(
            first_bullet,
            "* [Autonomous AI Pair-Programming with Google Jules](jules-platform-guide.md)",
        )

    def test_docs_summary_link_target_resolves_to_existing_file(self):
        # docs/SUMMARY.md links are relative to the docs/ directory.
        target = os.path.join(REPO_ROOT, "docs", "jules-platform-guide.md")
        self.assertTrue(os.path.isfile(target))

    def test_root_summary_contains_link(self):
        content = _read(ROOT_SUMMARY_PATH)
        self.assertIn("docs/jules-platform-guide.md", content)

    def test_root_summary_entry_exact_bullet_format(self):
        content = _read(ROOT_SUMMARY_PATH)
        self.assertIn(
            "* [Autonomous AI Pair-Programming with Google Jules](docs/jules-platform-guide.md)",
            content,
        )

    def test_root_summary_link_appears_before_wazuh_link(self):
        content = _read(ROOT_SUMMARY_PATH)
        jules_idx = content.index("docs/jules-platform-guide.md")
        wazuh_idx = content.index("docs/engineering/wazuh-installation.md")
        self.assertLess(jules_idx, wazuh_idx)

    def test_root_summary_link_target_resolves_to_existing_file(self):
        # Root SUMMARY.md links are relative to the repository root.
        target = os.path.join(REPO_ROOT, "docs", "jules-platform-guide.md")
        self.assertTrue(os.path.isfile(target))

    def test_root_and_docs_summary_entries_appear_exactly_once(self):
        self.assertEqual(
            _read(ROOT_SUMMARY_PATH).count("Autonomous AI Pair-Programming with Google Jules"),
            1,
        )
        self.assertEqual(
            _read(DOCS_SUMMARY_PATH).count("Autonomous AI Pair-Programming with Google Jules"),
            1,
        )

    def test_llms_txt_contains_entry(self):
        content = _read(LLMS_PATH)
        self.assertIn("docs/jules-platform-guide.md", content)

    def test_llms_txt_entry_matches_expected_description(self):
        content = _read(LLMS_PATH)
        self.assertIn(
            f"[Autonomous AI Pair-Programming with Google Jules]"
            f"(docs/jules-platform-guide.md) : {JULES_ENTRY_DESC}",
            content,
        )

    def test_llms_txt_entry_follows_bullet_link_colon_description_format(self):
        content = _read(LLMS_PATH)
        match = re.search(
            r"^- \[Autonomous AI Pair-Programming with Google Jules\]"
            r"\(docs/jules-platform-guide\.md\) : .+$",
            content,
            re.MULTILINE,
        )
        self.assertIsNotNone(
            match, "Entry does not follow the '- [Title](path) : description' format"
        )

    def test_llms_txt_entry_under_deployment_automation_section_heading(self):
        section_match = re.search(
            r"## Deployment, Automation, and Costing\n(.*?)(?=\n## |\Z)",
            _read(LLMS_PATH),
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn("docs/jules-platform-guide.md", section_match.group(1))

    def test_llms_txt_entry_appears_before_wazuh_entry(self):
        content = _read(LLMS_PATH)
        jules_idx = content.index("docs/jules-platform-guide.md")
        wazuh_idx = content.index("docs/engineering/wazuh-installation.md")
        self.assertLess(jules_idx, wazuh_idx)

    def test_llms_txt_entry_appears_exactly_once(self):
        content = _read(LLMS_PATH)
        self.assertEqual(
            content.count("Autonomous AI Pair-Programming with Google Jules"), 1
        )


class TestJulesPlatformGuideSitemapIntegrations(unittest.TestCase):
    """Tests for sitemap indexing of the new guide."""

    def test_text_sitemaps_contain_expected_urls(self):
        for path in [DOCS_SITEMAP_TXT, ROOT_SITEMAP_TXT]:
            with self.subTest(path=path):
                content = _read(path)
                self.assertIn(GH_URL, content)
                self.assertIn(GB_URL, content)

    def test_xml_sitemaps_contain_expected_locs(self):
        for path in [DOCS_SITEMAP_XML, ROOT_SITEMAP_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                locs = [
                    loc.text
                    for loc in root.findall(f"{SITEMAP_NS}url/{SITEMAP_NS}loc")
                ]
                self.assertIn(GH_URL, locs)

    def test_xml_sitemaps_entry_has_required_fields(self):
        for path in [DOCS_SITEMAP_XML, ROOT_SITEMAP_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                matching = [
                    url_el
                    for url_el in root.findall(f"{SITEMAP_NS}url")
                    if url_el.find(f"{SITEMAP_NS}loc").text == GH_URL
                ]
                self.assertEqual(len(matching), 1)
                url_el = matching[0]
                self.assertIsNotNone(url_el.find(f"{SITEMAP_NS}lastmod"))
                self.assertIsNotNone(url_el.find(f"{SITEMAP_NS}changefreq"))
                self.assertIsNotNone(url_el.find(f"{SITEMAP_NS}priority"))


class TestJulesPlatformGuideLlmsContextXmlIntegrations(unittest.TestCase):
    """Tests for the generated ``llms-context.xml`` assets (root and docs copies)."""

    def test_files_exist(self):
        self.assertTrue(os.path.isfile(ROOT_LLMS_CONTEXT_XML))
        self.assertTrue(os.path.isfile(DOCS_LLMS_CONTEXT_XML))

    def test_files_are_well_formed_xml(self):
        for path in [ROOT_LLMS_CONTEXT_XML, DOCS_LLMS_CONTEXT_XML]:
            with self.subTest(path=path):
                try:
                    ET.parse(path)
                except ET.ParseError as exc:
                    self.fail(f"{path} is not valid XML: {exc}")

    def test_document_node_has_expected_attributes(self):
        for path in [ROOT_LLMS_CONTEXT_XML, DOCS_LLMS_CONTEXT_XML]:
            with self.subTest(path=path):
                root = ET.parse(path).getroot()
                doc_nodes = [
                    doc
                    for doc in root.findall(".//document")
                    if doc.get("url") == "docs/jules-platform-guide.md"
                ]
                self.assertEqual(len(doc_nodes), 1)
                doc_node = doc_nodes[0]
                self.assertEqual(
                    doc_node.get("title"),
                    "Autonomous AI Pair-Programming with Google Jules",
                )
                self.assertEqual(doc_node.get("desc"), JULES_ENTRY_DESC)

    def test_document_node_is_nested_in_expected_section(self):
        for path in [ROOT_LLMS_CONTEXT_XML, DOCS_LLMS_CONTEXT_XML]:
            with self.subTest(path=path):
                root = ET.parse(path).getroot()
                sections = root.findall(".//section")
                target_section = next(
                    (
                        s
                        for s in sections
                        if s.get("title") == "Deployment, Automation, and Costing"
                    ),
                    None,
                )
                self.assertIsNotNone(target_section)
                urls_in_section = [
                    doc.get("url") for doc in target_section.findall("document")
                ]
                self.assertIn("docs/jules-platform-guide.md", urls_in_section)

    def test_document_body_contains_escaped_ampersand_heading(self):
        # The embedded heading uses "&amp;" for the literal "&" character,
        # confirming the generator escapes special XML characters correctly.
        for path in [ROOT_LLMS_CONTEXT_XML, DOCS_LLMS_CONTEXT_XML]:
            with self.subTest(path=path):
                content = _read(path)
                self.assertIn(
                    "# Autonomous AI Pair-Programming &amp; Multi-Agent "
                    "Operations with Google Jules",
                    content,
                )

    def test_root_and_docs_copies_are_identical(self):
        self.assertEqual(_read(ROOT_LLMS_CONTEXT_XML), _read(DOCS_LLMS_CONTEXT_XML))


class TestJulesPlatformGuideLlmsFullTxtIntegrations(unittest.TestCase):
    """Tests for the generated ``llms-full.txt`` assets (root and docs copies)."""

    def test_files_exist(self):
        self.assertTrue(os.path.isfile(ROOT_LLMS_FULL_TXT))
        self.assertTrue(os.path.isfile(DOCS_LLMS_FULL_TXT))

    def test_heading_and_description_present(self):
        for path in [ROOT_LLMS_FULL_TXT, DOCS_LLMS_FULL_TXT]:
            with self.subTest(path=path):
                content = _read(path)
                self.assertIn(
                    "## Autonomous AI Pair-Programming with Google Jules", content
                )
                self.assertIn(f"*{JULES_ENTRY_DESC}*", content)

    def test_entry_appears_after_deployment_automation_section_heading(self):
        for path in [ROOT_LLMS_FULL_TXT, DOCS_LLMS_FULL_TXT]:
            with self.subTest(path=path):
                content = _read(path)
                section_idx = content.index(
                    "# Section: Deployment, Automation, and Costing"
                )
                entry_idx = content.index(
                    "## Autonomous AI Pair-Programming with Google Jules"
                )
                self.assertLess(section_idx, entry_idx)

    def test_entry_appears_before_wazuh_entry(self):
        for path in [ROOT_LLMS_FULL_TXT, DOCS_LLMS_FULL_TXT]:
            with self.subTest(path=path):
                content = _read(path)
                jules_idx = content.index(
                    "## Autonomous AI Pair-Programming with Google Jules"
                )
                wazuh_idx = content.index("## Wazuh SIEM & XDR Deployment Guide")
                self.assertLess(jules_idx, wazuh_idx)

    def test_root_and_docs_copies_are_identical(self):
        self.assertEqual(_read(ROOT_LLMS_FULL_TXT), _read(DOCS_LLMS_FULL_TXT))


class TestJulesPlatformGuideEmbeddedCodeBlocks(unittest.TestCase):
    """Sanity checks for the illustrative code samples embedded in the guide."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(JULES_GUIDE_PATH)

    def _extract_fenced_blocks(self, language):
        pattern = re.compile(
            r"```" + re.escape(language) + r"\n(.*?)```", re.DOTALL
        )
        return pattern.findall(self.content)

    def test_python_delegation_script_block_present(self):
        blocks = self._extract_fenced_blocks("python")
        self.assertEqual(len(blocks), 1)

    def test_python_delegation_script_is_syntactically_valid(self):
        """Regression guard: the embedded Antigravity-to-Jules delegation
        script must remain valid, parseable Python source (checked via
        ``ast.parse`` only -- the code is never executed)."""
        blocks = self._extract_fenced_blocks("python")
        self.assertEqual(len(blocks), 1)
        try:
            ast.parse(blocks[0])
        except SyntaxError as exc:
            self.fail(f"Embedded Python code block is not valid Python: {exc}")

    def test_python_delegation_script_references_expected_symbols(self):
        blocks = self._extract_fenced_blocks("python")
        script = blocks[0]
        self.assertIn("JULES_API_KEY", script)
        self.assertIn("JULES_SESSIONS_URL", script)
        self.assertIn("JULES_SOURCES_URL", script)

    def test_hcl_metadata_options_block_present_and_balanced(self):
        blocks = self._extract_fenced_blocks("hcl")
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(block.count("{"), block.count("}"))
        self.assertIn('http_tokens                 = "required"', block)

    def test_bash_blocks_do_not_contain_unresolved_placeholders(self):
        """Negative check: none of the bash example blocks should retain
        template placeholders other than the intentional API-key
        placeholder documented in the guide."""
        blocks = self._extract_fenced_blocks("bash")
        self.assertGreater(len(blocks), 0)
        for block in blocks:
            self.assertNotIn("<REPLACE_ME>", block)
            self.assertNotIn("{{", block)
            self.assertNotIn("}}", block)


class TestJulesPlatformGuideNegativeChecks(unittest.TestCase):
    """Negative/boundary checks guarding against common authoring mistakes."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(JULES_GUIDE_PATH)

    def test_no_unresolved_merge_conflict_markers(self):
        # Match markers only when they occupy an entire line, so that the
        # ASCII-art "<=======>" arrows used in the architecture diagrams are
        # not mistaken for unresolved Git conflict markers.
        for marker in [r"^<{7}", r"^={7}$", r"^>{7}"]:
            self.assertIsNone(
                re.search(marker, self.content, re.MULTILINE),
                f"Unresolved merge conflict marker matching {marker!r} found",
            )

    def test_no_todo_placeholders(self):
        self.assertNotIn("TODO", self.content)
        self.assertNotIn("FIXME", self.content)

    def test_exactly_one_top_level_heading(self):
        # Strip fenced code blocks first so that shell/python comments such
        # as "# Verify installation" are not mistaken for Markdown headings.
        prose_only = re.sub(r"```.*?```", "", self.content, flags=re.DOTALL)
        top_level_headings = re.findall(r"^# [^#].*$", prose_only, re.MULTILINE)
        self.assertEqual(len(top_level_headings), 1)

    def test_numbered_sections_are_sequential(self):
        numbers = [
            int(n)
            for n in re.findall(r"^## (\d+)\. ", self.content, re.MULTILINE)
        ]
        self.assertEqual(numbers, sorted(numbers))
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)))


if __name__ == "__main__":
    unittest.main()
