#!/usr/bin/env python3
"""Unit tests for the ASIMP for AI Agents documentation added in this PR.

This PR introduces a new documentation page:
* ``docs/engineering/asimp-for-ai-agents.md``

And integrates it across several files:
* ``docs/index.md``       -- adds a bulleted link pointing at
  ``engineering/asimp-for-ai-agents.html``.
* ``llms.txt``            -- adds an AI-agent index entry pointing at
  ``docs/engineering/asimp-for-ai-agents.md``.
* ``sitemap.txt`` / ``docs/sitemap.txt``   -- adds GitHub Pages and GitBook
  URLs for the new page.
* ``sitemap.xml`` / ``docs/sitemap.xml``   -- adds a ``<url>`` entry for the
  new page.

These files are treated as plain text/XML (rather than requiring a live
Jekyll build) to stay dependency free.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_asimp_for_ai_agents_docs
"""
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
import generate_sitemaps  # noqa: E402

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
ASIMP_AI_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "asimp-for-ai-agents.md")
ROOT_SITEMAP_TXT = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_TXT = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_XML = os.path.join(REPO_ROOT, "sitemap.xml")
DOCS_SITEMAP_XML = os.path.join(REPO_ROOT, "docs", "sitemap.xml")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

GH_BASE = "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
GB_BASE = "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/"

GH_URL = GH_BASE + "engineering/asimp-for-ai-agents.html"
GB_URL = GB_BASE + "engineering/asimp-for-ai-agents"


def _read(path):
    """Read and return the UTF-8 text content of a file.
    
    Parameters:
    	path: The path to the file to read.
    
    Returns:
    	str: The file's text content.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_front_matter(content):
    """
    Parse YAML front matter and the document body from Markdown content.
    
    Parameters:
        content (str): Markdown content containing YAML front matter delimited by `---`.
    
    Returns:
        tuple: A pair containing the parsed front matter and the remaining body text.
    """
    stripped = content.lstrip()
    parts = stripped.split("---", 2)
    front_matter_text = parts[1]
    body_text = parts[2]
    front_matter = prepare_docs.parse_yaml_front_matter(front_matter_text)
    return front_matter, body_text


class AsimpAiFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of docs/engineering/asimp-for-ai-agents.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ASIMP_AI_PATH)
        cls.front_matter, cls.body_text = _parse_front_matter(cls.content)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(ASIMP_AI_PATH))

    def test_starts_with_front_matter_delimiter(self):
        self.assertTrue(self.content.startswith("---\n"))

    def test_required_okf_fields_present(self):
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_layout_is_default(self):
        self.assertEqual(self.front_matter["layout"], "default")

    def test_okf_version_is_expected_value(self):
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_title_field_value(self):
        self.assertEqual(
            self.front_matter["title"],
            "ASIMP for AI Agents: Cognitive Twin Integration & Persistent Memory Guide",
        )

    def test_type_matches_prepare_docs_inference(self):
        inferred_type = prepare_docs.infer_okf_type(
            "docs/engineering/asimp-for-ai-agents.md"
        )
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_match_authored_values_exactly(self):
        self.assertEqual(
            self.front_matter["topics"],
            ["security", "compliance", "ai-agents", "dsom", "asimp"],
        )

    def test_timestamp_matches_iso8601_with_offset(self):
        self.assertRegex(
            self.front_matter["timestamp"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$",
        )

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        self.assertEqual(heading_match.group(1).strip(), self.front_matter["title"])

    def test_topics_have_no_duplicates(self):
        topics = self.front_matter["topics"]
        self.assertEqual(len(topics), len(set(topics)))

    def test_topics_is_nonempty_list(self):
        self.assertIsInstance(self.front_matter["topics"], list)
        self.assertGreater(len(self.front_matter["topics"]), 0)

    def test_infer_okf_topics_preserves_authored_topics(self):
        # Regression: prepare_docs.infer_okf_topics must not overwrite
        # explicitly authored topics with path-derived inferred ones,
        # since this document already ships with curated topics.
        authored_topics = self.front_matter["topics"]
        preserved = prepare_docs.infer_okf_topics(
            "docs/engineering/asimp-for-ai-agents.md", authored_topics
        )
        self.assertEqual(preserved, authored_topics)

    def test_okf_version_is_string_type(self):
        # Boundary/negative check: okf_version must remain the literal
        # string "0.1", not be coerced to a float by the YAML parser.
        self.assertIsInstance(self.front_matter["okf_version"], str)
        self.assertEqual(self.front_matter["okf_version"], "0.1")


class AsimpAiContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of docs/engineering/asimp-for-ai-agents.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ASIMP_AI_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn(
            "# ASIMP for AI Agents: Cognitive Twin Integration & Persistent Memory Guide",
            self.content,
        )

    def test_sections_present(self):
        headings = [
            "## 1. Executive Summary & Core Philosophy",
            "## 2. Spatial Memory Anchors (`.agents/brain/` & Gateway)",
            "## 3. The 5-Step Local Knowledge-First Discovery Protocol",
            "## 4. Token Performance & Progressive Disclosure",
            "## 5. Step-by-Step Implementation Sequence of ASIMP with DSOM",
            "## 6. Verification and Audit Ledger",
        ]
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)

    def test_mentions_dsom_and_asimp(self):
        self.assertIn("Deep State of Mind", self.content)
        self.assertIn("ASIMP", self.content)

    def test_mentions_agents_and_brain_folders(self):
        self.assertIn(".agents/AGENTS.md", self.content)
        self.assertIn("AGENTS.md", self.content)
        self.assertIn(".agents/brain/", self.content)

    def test_mermaid_diagram_present_with_five_steps(self):
        self.assertIn("```mermaid", self.content)
        self.assertIn("graph TD", self.content)
        for step in [
            "Step 1: Local Metadata Search",
            "Step 2: Targeted File Reading",
            "Step 3: Temporal Verification",
            "Step 4: Human Verification Gate",
            "Step 5: Safe Terminal Execution",
        ]:
            with self.subTest(step=step):
                self.assertIn(step, self.content)

    def test_discovery_protocol_steps_numbered_one_to_five(self):
        # Extract the "N. **Step N: ...**" enumerated list items and confirm
        # they are present and sequential from 1 to 5.
        numbers = re.findall(r"^(\d+)\. \*\*Step \d+:", self.content, re.MULTILINE)
        self.assertEqual([int(n) for n in numbers], [1, 2, 3, 4, 5])

    def test_implementation_sequence_steps_numbered_one_to_eleven(self):
        # Scope strictly to Section 5's body (up to the next top-level
        # section) so the shared "Step N" numbering used in Section 3 does
        # not leak into this assertion.
        section_match = re.search(
            r"## 5\. Step-by-Step Implementation Sequence of ASIMP with DSOM\n"
            r"(.*?)(?=\n## 6\.|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        numbers = re.findall(r"^(\d+)\. \*\*", section_match.group(1), re.MULTILINE)
        self.assertEqual([int(n) for n in numbers], list(range(1, 12)))

    def test_mentions_constitutional_rules(self):
        for phrase in [
            "27 Core Constitutional AI Laws",
            "Rule 1 (Zero-Global Memory)",
            "Rule 20 (Local Knowledge-First Discovery)",
            "Rule 21 (Temporal Verification Gate)",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.content)

    def test_mentions_verification_test_command(self):
        self.assertIn("python3 -m unittest discover -s tests", self.content)

    def test_footer_attribution_present(self):
        self.assertIn(
            "*Deep State of Mind (DSOM) For My AI Protocol | "
            "Harisfazillah Jamel (LinuxMalaysia) | 2026-08-12*",
            self.content,
        )

    def test_does_not_contain_placeholder_text(self):
        for placeholder in ["TODO", "TBD", "Lorem ipsum", "FIXME"]:
            with self.subTest(placeholder=placeholder):
                self.assertNotIn(placeholder, self.content)

    def test_referenced_agent_memory_files_exist_in_repo(self):
        # The guide makes concrete claims about specific files that back
        # the DSOM spatial memory architecture; verify those files are
        # real so the documentation is not describing a non-existent layout.
        referenced_paths = [
            os.path.join(REPO_ROOT, "AGENTS.md"),
            os.path.join(REPO_ROOT, ".agents", "AGENTS.md"),
            os.path.join(REPO_ROOT, ".agents", "brain", "active_context_manifest.md"),
        ]
        for path in referenced_paths:
            with self.subTest(path=path):
                self.assertTrue(os.path.isfile(path), f"Referenced file missing: {path}")


class IndexMdIntegrationTestCase(unittest.TestCase):
    """Tests for index.md link and placement."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)

    def test_link_present(self):
        self.assertIn(
            "[ASIMP for AI Agents: Cognitive Twin Integration & Persistent Memory Guide]"
            "(engineering/asimp-for-ai-agents.html)",
            self.content,
        )

    def test_appears_in_deployment_cicd_section(self) -> None:
        section_match = re.search(
            r"### Deployment & CI/CD\n(.*?)(?=\n### |\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[ASIMP for AI Agents: Cognitive Twin Integration & Persistent Memory Guide]"
            "(engineering/asimp-for-ai-agents.html)",
            section_match.group(1),
        )

    def test_link_occurs_exactly_once(self):
        # Negative/regression check: guard against accidental duplicate
        # insertion of the new bullet entry.
        self.assertEqual(
            self.content.count("engineering/asimp-for-ai-agents.html"), 1
        )

    def test_link_appears_before_aws_cli_guide_entry(self):
        asimp_pos = self.content.find("engineering/asimp-for-ai-agents.html")
        aws_cli_pos = self.content.find("engineering/aws-cli-guide.html")
        self.assertNotEqual(asimp_pos, -1)
        self.assertNotEqual(aws_cli_pos, -1)
        self.assertLess(asimp_pos, aws_cli_pos)


class LlmsTxtIntegrationTestCase(unittest.TestCase):
    """Tests for llms.txt integration."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LLMS_PATH)

    def test_entry_present(self) -> None:
        self.assertIn(
            "[ASIMP for AI Agents](docs/engineering/asimp-for-ai-agents.md)",
            self.content,
        )

    def test_entry_occurs_exactly_once(self):
        self.assertEqual(
            self.content.count("docs/engineering/asimp-for-ai-agents.md"), 1
        )

    def test_entry_under_deployment_automation_costing_heading(self):
        section_match = re.search(
            r"## Deployment, Automation, and Costing\n(.*?)(?=\n## |\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[ASIMP for AI Agents](docs/engineering/asimp-for-ai-agents.md)",
            section_match.group(1),
        )

    def test_entry_appears_before_aws_cli_guide_entry(self):
        asimp_pos = self.content.find("docs/engineering/asimp-for-ai-agents.md")
        aws_cli_pos = self.content.find("docs/engineering/aws-cli-guide.md")
        self.assertNotEqual(asimp_pos, -1)
        self.assertNotEqual(aws_cli_pos, -1)
        self.assertLess(asimp_pos, aws_cli_pos)


class SitemapIntegrationTestCase(unittest.TestCase):
    """Tests for sitemaps txt/xml integration."""

    def test_text_sitemaps_contain_expected_urls(self) -> None:
        for path in [DOCS_SITEMAP_TXT, ROOT_SITEMAP_TXT]:
            with self.subTest(path=path):
                content = _read(path)
                self.assertIn(GH_URL, content)
                self.assertIn(GB_URL, content)

    def test_xml_sitemaps_contain_expected_locs(self) -> None:
        for path in [DOCS_SITEMAP_XML, ROOT_SITEMAP_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                locs = [
                    loc.text
                    for loc in root.findall(f"{SITEMAP_NS}url/{SITEMAP_NS}loc")
                ]
                self.assertIn(GH_URL, locs)

    def test_root_and_docs_txt_sitemaps_are_identical(self):
        # The generator writes the same content to both the repo root and
        # docs/ copies; a mismatch would indicate one copy was updated but
        # not the other.
        self.assertEqual(_read(ROOT_SITEMAP_TXT), _read(DOCS_SITEMAP_TXT))

    def test_root_and_docs_xml_sitemaps_are_identical(self):
        self.assertEqual(_read(ROOT_SITEMAP_XML), _read(DOCS_SITEMAP_XML))

    def test_no_duplicate_urls_in_text_sitemaps(self):
        for path in [DOCS_SITEMAP_TXT, ROOT_SITEMAP_TXT]:
            with self.subTest(path=path):
                content = _read(path)
                self.assertEqual(content.count(GH_URL), 1)
                self.assertEqual(content.count(GB_URL), 1)

    def test_no_duplicate_locs_in_xml_sitemaps(self):
        for path in [DOCS_SITEMAP_XML, ROOT_SITEMAP_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                locs = [
                    loc.text
                    for loc in root.findall(f"{SITEMAP_NS}url/{SITEMAP_NS}loc")
                ]
                self.assertEqual(locs.count(GH_URL), 1)

    def test_gh_url_ordered_between_opentofu_migration_and_jumphost(self):
        opentofu_url = GH_BASE + "engineering/opentofu-migration.html"
        jumphost_url = GH_BASE + "engineering/jumphost.html"
        for path in [DOCS_SITEMAP_TXT, ROOT_SITEMAP_TXT]:
            with self.subTest(path=path):
                lines = [
                    line.strip() for line in _read(path).splitlines() if line.strip()
                ]
                self.assertIn(opentofu_url, lines)
                self.assertIn(GH_URL, lines)
                self.assertIn(jumphost_url, lines)
                self.assertLess(lines.index(opentofu_url), lines.index(GH_URL))
                self.assertLess(lines.index(GH_URL), lines.index(jumphost_url))

    def test_gb_url_ordered_between_opentofu_migration_and_jumphost(self):
        opentofu_url = GB_BASE + "engineering/opentofu-migration"
        jumphost_url = GB_BASE + "engineering/jumphost"
        for path in [DOCS_SITEMAP_TXT, ROOT_SITEMAP_TXT]:
            with self.subTest(path=path):
                lines = [
                    line.strip() for line in _read(path).splitlines() if line.strip()
                ]
                self.assertIn(opentofu_url, lines)
                self.assertIn(GB_URL, lines)
                self.assertIn(jumphost_url, lines)
                self.assertLess(lines.index(opentofu_url), lines.index(GB_URL))
                self.assertLess(lines.index(GB_URL), lines.index(jumphost_url))

    def test_xml_url_entry_has_expected_field_values(self):
        for path in [DOCS_SITEMAP_XML, ROOT_SITEMAP_XML]:
            with self.subTest(path=path):
                tree = ET.parse(path)
                root = tree.getroot()
                matched_entry = None
                for url_node in root.findall(f"{SITEMAP_NS}url"):
                    loc = url_node.find(f"{SITEMAP_NS}loc")
                    if loc is not None and loc.text == GH_URL:
                        matched_entry = url_node
                        break
                self.assertIsNotNone(matched_entry, f"No <url> entry found for {GH_URL} in {path}")

                lastmod = matched_entry.find(f"{SITEMAP_NS}lastmod")
                changefreq = matched_entry.find(f"{SITEMAP_NS}changefreq")
                priority = matched_entry.find(f"{SITEMAP_NS}priority")

                self.assertIsNotNone(lastmod)
                self.assertIsNotNone(changefreq)
                self.assertIsNotNone(priority)

                self.assertRegex(lastmod.text, r"^\d{4}-\d{2}-\d{2}$")
                self.assertEqual(changefreq.text, "weekly")
                self.assertEqual(priority.text, "0.6")

    def test_xml_url_entry_is_within_valid_priority_bounds(self):
        # Boundary sanity check independent of the specific expected value:
        # priority must remain within the sitemap protocol's [0.0, 1.0] range.
        tree = ET.parse(ROOT_SITEMAP_XML)
        root = tree.getroot()
        for url_node in root.findall(f"{SITEMAP_NS}url"):
            loc = url_node.find(f"{SITEMAP_NS}loc")
            if loc is not None and loc.text == GH_URL:
                priority = url_node.find(f"{SITEMAP_NS}priority")
                p_val = float(priority.text)
                self.assertGreaterEqual(p_val, 0.0)
                self.assertLessEqual(p_val, 1.0)
                break
        else:
            self.fail(f"No <url> entry found for {GH_URL}")


if __name__ == "__main__":
    unittest.main()
