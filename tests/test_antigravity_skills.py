#!/usr/bin/env python3
"""
Unit tests for the Google Antigravity-compatible Agent Skills in .agents/skills/.

This test suite performs rigorous verification of all Google Antigravity-compatible
Agent Skills configured inside .agents/skills/. It asserts perfect directory
matching, OKF v0.1 and Agent Skills open standard YAML frontmatter correctness,
DSOM AI Protocol footer compliance, and master constitution integrations.
"""

import os
import re
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKILLS_DIR = os.path.join(REPO_ROOT, ".agents", "skills")

EXPECTED_SKILLS = [
    "jules-knowledge",
    "gitbook-llm-assets",
    "asimp-security-audit",
    "disaster-recovery-sovereignty",
    "opentofu-cloud-engineering",
    "cicd-automation-workflows"
]


def _read(path):
    """
    Reads the full UTF-8 contents of the specified file.

    Args:
        path (str): The absolute path of the file to read.

    Returns:
        str: The contents of the file.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _tokenize_flow_sequence(val):
    """
    Parses a flow sequence (e.g., '["item1", "item2, vpc", "item3"]') preserving commas inside quotes.
    """
    tokens = []
    current = []
    in_double_quote = False
    in_single_quote = False
    escaped = False

    i = 0
    while i < len(val):
        c = val[i]
        if escaped:
            current.append(c)
            escaped = False
            i += 1
            continue

        if in_double_quote:
            if c == '\\':
                current.append(c)
                escaped = True
            elif c == '"':
                current.append(c)
                in_double_quote = False
            else:
                current.append(c)
        elif in_single_quote:
            if c == "'":
                current.append(c)
                in_single_quote = False
            else:
                current.append(c)
        else:
            if c == '"':
                in_double_quote = True
                current.append(c)
            elif c == "'":
                in_single_quote = True
                current.append(c)
            elif c == ',':
                tokens.append("".join(current).strip())
                current = []
            else:
                current.append(c)
        i += 1

    tokens.append("".join(current).strip())
    return [t.strip('"').strip("'") for t in tokens if t.strip()]


def _parse_front_matter(content):
    """
    Extracts and parses YAML front matter from a Markdown document without external dependencies.

    This function parses top-level key-values and nested dictionaries (e.g. metadata)
    between the starting and ending --- delimiters. If any malformed or unsupported non-comment
    line is encountered, it returns (None, body_text) to maintain strict validation.

    Args:
        content (str): The raw string content of the Markdown file.

    Extract and parse front matter from a Markdown document.
    
    Parameters:
        content (str): Markdown content whose first line must be the opening
            front-matter delimiter.
    
    Returns:
        tuple: A parsed front-matter dictionary and the remaining document body.
            Returns `(None, content)` when the required delimiters are missing.
    """
    stripped = content.lstrip()
    if not stripped.startswith("---"):
        return None, content

    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, content

    end_idx = -1
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = idx
            break

    if end_idx == -1:
        return None, content

    body_text = "\n".join(lines[end_idx+1:])

    data = {}
    current_section = None
    for line in lines[1:end_idx]:
        if not line.strip() or line.strip().startswith("#"):
            continue

        if line.startswith("  "):
            if not current_section:
                return None, body_text
            sub_line = line.strip()
            match = re.match(r'^([^:]+):\s*(.*)$', sub_line)
            if not match:
                return None, body_text
            k = match.group(1).strip()
            v = match.group(2).strip()
            if v.startswith("[") and v.endswith("]"):
                items = _tokenize_flow_sequence(v[1:-1])
                data[current_section][k] = items
            else:
                data[current_section][k] = v.strip('"').strip("'")
            continue

        match = re.match(r'^([^:]+):\s*(.*)$', line)
        if not match:
            return None, body_text

        k = match.group(1).strip()
        v = match.group(2).strip()
        if not v:
            current_section = k
            data[k] = {}
        else:
            current_section = None
            if v.startswith("[") and v.endswith("]"):
                data[k] = _tokenize_flow_sequence(v[1:-1])
            else:
                data[k] = v.strip('"').strip("'")
        if line.startswith("  ") and current_section:
            # Sub-key inside current_section
            sub_line = line.strip()
            match = re.match(r'^([^:]+):\s*(.*)$', sub_line)
            if match:
                k = match.group(1).strip()
                v = match.group(2).strip().strip('"').strip("'")
                if v.startswith("[") and v.endswith("]"):
                    items = [x.strip().strip('"').strip("'") for x in v[1:-1].split(",") if x.strip()]
                    data[current_section][k] = items
                else:
                    data[current_section][k] = v
            continue

        match = re.match(r'^([^:]+):\s*(.*)$', line)
        if match:
            k = match.group(1).strip()
            v = match.group(2).strip().strip('"').strip("'")
            if not v:
                current_section = k
                data[k] = {}
            else:
                current_section = None
                data[k] = v

    return data, body_text


class TestAntigravitySkills(unittest.TestCase):
    """
    TestCase verifying directory structures and frontmatter formats for skills.
    """

    def test_skills_directories_exist(self):
        """
        Verify that all expected skill directories exist and contain SKILL.md.

        It discovers all immediate directories under the skills root directory
        and asserts that the discovered set perfectly matches EXPECTED_SKILLS.
        Unexpected directories or missing directories cause immediate failures.
        """
        self.assertTrue(os.path.isdir(SKILLS_DIR), "Skills directory does not exist")

        # Discover all immediate subdirectories under SKILLS_DIR
        discovered_skills = []
        for name in os.listdir(SKILLS_DIR):
            path = os.path.join(SKILLS_DIR, name)
            if os.path.isdir(path) and name not in [".", ".."]:
                discovered_skills.append(name)

        # Assert perfect equality of sets to catch unexpected or missing folders
        self.assertEqual(
            set(discovered_skills),
            set(EXPECTED_SKILLS),
            f"Discovered skill directories do not match EXPECTED_SKILLS.\nDiscovered: {discovered_skills}\nExpected: {EXPECTED_SKILLS}"
        )

        # Assert individual SKILL.md files are present
        for skill in EXPECTED_SKILLS:
            skill_folder = os.path.join(SKILLS_DIR, skill)
            skill_md_path = os.path.join(skill_folder, "SKILL.md")
            self.assertTrue(os.path.isfile(skill_md_path), f"SKILL.md does not exist for '{skill}'")

    def test_skills_yaml_frontmatter_rules(self):
        """
        Verify YAML frontmatter constraints and standard fields for each SKILL.md.

        Specifically asserts:
        - Frontmatter block starts exactly on Line 1, Column 1 with ---
        - Preserves and validates both name and description top-level fields
        - Validates OKF v0.1 fields (layout, okf_version, type, title, timestamp, topics)
          exist inside the nested 'metadata' dictionary.
        """
        for skill in EXPECTED_SKILLS:
            skill_md_path = os.path.join(SKILLS_DIR, skill, "SKILL.md")
            content = _read(skill_md_path)

            # Rule: MUST start on Line 1, Column 1 with ---
            self.assertTrue(
                content.startswith("---\n"),
                f"SKILL.md for '{skill}' does not start with front matter delimiter on Line 1, Column 1"
            )

            front_matter, body = _parse_front_matter(content)
            self.assertIsNotNone(front_matter, f"Failed to parse front matter for skill '{skill}'")

            # Check supported Agent Skills top-level fields
            self.assertEqual(front_matter.get("name"), skill, f"name field mismatch in '{skill}' frontmatter")
            self.assertTrue("description" in front_matter, f"description field missing in '{skill}'")

            # Check nested OKF metadata block
            meta = front_matter.get("metadata")
            self.assertIsInstance(meta, dict, f"metadata map missing or malformed in '{skill}'")

            self.assertEqual(meta.get("layout"), "default", f"layout mismatch in '{skill}' metadata")
            self.assertEqual(meta.get("okf_version"), "0.1", f"okf_version mismatch in '{skill}' metadata")
            self.assertEqual(meta.get("type"), "Agent Skill", f"type mismatch in '{skill}' metadata")
            self.assertTrue("title" in meta, f"title missing in '{skill}' metadata")
            self.assertTrue("timestamp" in meta, f"timestamp missing in '{skill}' metadata")
            self.assertTrue("topics" in meta, f"topics missing in '{skill}' metadata")

    def test_skills_conclude_with_dsom_footer(self):
        r"""
        Verify each SKILL.md concludes with the Deep State of Mind AI Protocol footer.

        The dsom_pattern is anchored exactly to the end of the stripped document (\Z)
        to ensure no non-empty content or characters exist after the footer.
        """
        dsom_pattern = r"\*Deep State of Mind \(DSOM\) For My AI Protocol \| Harisfazillah Jamel \(LinuxMalaysia\) \| 2026-08-1[0-9]\*\Z"
        for skill in EXPECTED_SKILLS:
            skill_md_path = os.path.join(SKILLS_DIR, skill, "SKILL.md")
            content = _read(skill_md_path).strip()
            self.assertIsNotNone(
                re.search(dsom_pattern, content),
                f"Skill '{skill}' does not end with the standard DSOM footer anchored at the end. Content tail: {content[-100:]}"
            )

    def test_constitution_and_root_agents_reference_skills(self):
        """
        Verify that master AGENTS.md files contain reference descriptions for each skill.
        """
        for agents_file in ["AGENTS.md", ".agents/AGENTS.md"]:
            path = os.path.join(REPO_ROOT, agents_file)
            self.assertTrue(os.path.isfile(path))
            content = _read(path)
            for skill in EXPECTED_SKILLS:
                self.assertIn(skill, content, f"Skill '{skill}' is not mentioned in {agents_file}")

    def test_parse_front_matter_strict_validation_and_quoted_commas(self):
        """
        Test front-matter parser handling of invalid lines and quoted comma-containing items.
        """
        # Test malformed line returns None
        malformed = "---\nname: skill\ninvalid line without colon\n---\nbody"
        data, _ = _parse_front_matter(malformed)
        self.assertIsNone(data)

        # Test flow sequence with quoted item containing comma
        valid_with_quoted_commas = '---\nname: skill\ntopics: ["aws", "item, with, commas", "networking"]\n---\nbody'
        data, _ = _parse_front_matter(valid_with_quoted_commas)
        self.assertIsNotNone(data)
        self.assertEqual(data.get("topics"), ["aws", "item, with, commas", "networking"])


class TestParseFrontMatterHelper(unittest.TestCase):
    """
    Unit tests for the dependency-free ``_parse_front_matter`` helper.

    These tests exercise the hand-rolled front-matter parser directly (rather
    than through the higher-level skill validation tests) to lock in its
    parsing contract now that the PyYAML dependency has been removed.
    """

    def test_missing_opening_delimiter_returns_none(self):
        """Content that does not start with '---' yields (None, original_content)."""
        content = "name: no-frontmatter\nJust a regular document body."
        data, body = _parse_front_matter(content)
        self.assertIsNone(data)
        self.assertEqual(body, content)

    def test_missing_closing_delimiter_returns_none(self):
        """An unterminated front-matter block (no closing '---') yields (None, content)."""
        content = "---\nname: unterminated\ndescription: oops\n"
        data, body = _parse_front_matter(content)
        self.assertIsNone(data)
        self.assertEqual(body, content)

    def test_leading_blank_line_before_delimiter_returns_none(self):
        """
        A blank line preceding the opening '---' fails the strict Line 1 check
        even though ``content.lstrip()`` would otherwise start with '---'.
        """
        content = "\n---\nname: test\n---\nBody"
        data, body = _parse_front_matter(content)
        self.assertIsNone(data)
        self.assertEqual(body, content)

    def test_basic_top_level_fields_are_parsed(self):
        """Simple scalar top-level fields are parsed into a flat dict."""
        lines = [
            "---",
            "name: test-skill",
            'description: "A skill description"',
            "---",
            "Body content here",
            "More body",
        ]
        content = "\n".join(lines)
        data, body = _parse_front_matter(content)
        self.assertEqual(data, {"name": "test-skill", "description": "A skill description"})
        self.assertEqual(body, "Body content here\nMore body")

    def test_nested_metadata_dict_with_list_value_is_parsed(self):
        """A nested 'metadata:' block with indented sub-keys parses into a dict, and
        bracketed sub-values are expanded into a list of unquoted strings."""
        lines = [
            "---",
            "name: sample",
            "metadata:",
            "  layout: default",
            '  topics: ["a", "b", "c"]',
            "---",
            "Body",
        ]
        content = "\n".join(lines)
        data, body = _parse_front_matter(content)
        self.assertEqual(
            data,
            {"name": "sample", "metadata": {"layout": "default", "topics": ["a", "b", "c"]}},
        )
        self.assertEqual(body, "Body")

    def test_blank_lines_and_comments_are_skipped(self):
        """Blank lines and '#'-prefixed comment lines inside the block are ignored."""
        lines = [
            "---",
            "# this is a comment",
            "",
            "name: sample",
            "---",
            "Body",
        ]
        content = "\n".join(lines)
        data, body = _parse_front_matter(content)
        self.assertEqual(data, {"name": "sample"})
        self.assertEqual(body, "Body")

    def test_single_and_double_quotes_are_stripped(self):
        """Both single- and double-quoted scalar values are unquoted."""
        lines = [
            "---",
            "name: 'single-quoted'",
            'description: "double-quoted"',
            "---",
            "",
        ]
        content = "\n".join(lines)
        data, body = _parse_front_matter(content)
        self.assertEqual(data, {"name": "single-quoted", "description": "double-quoted"})
        self.assertEqual(body, "")

    def test_empty_value_key_creates_nested_dict_section(self):
        """A top-level key with no inline value (e.g. 'metadata:') opens a nested section."""
        lines = [
            "---",
            "metadata:",
            "---",
            "Body",
        ]
        content = "\n".join(lines)
        data, body = _parse_front_matter(content)
        self.assertEqual(data, {"metadata": {}})
        self.assertEqual(body, "Body")

    def test_value_containing_colon_is_preserved(self):
        """Values containing colons (e.g. ISO timestamps) are preserved intact."""
        lines = [
            "---",
            'timestamp: "2026-08-05T22:20:36+08:00"',
            "---",
            "Body",
        ]
        content = "\n".join(lines)
        data, _ = _parse_front_matter(content)
        self.assertEqual(data["timestamp"], "2026-08-05T22:20:36+08:00")

    def test_top_level_bracketed_list_is_not_expanded(self):
        """
        Regression/boundary case: unlike sub-keys nested under a section, a
        bracketed list value declared directly at the top level (not indented
        under a parent key) is NOT expanded into a Python list -- it is kept
        as a raw, quote-stripped string. This documents a real limitation of
        the lightweight parser compared to full YAML semantics.
        """
        lines = [
            "---",
            'topics: ["x", "y"]',
            "---",
            "Body",
        ]
        content = "\n".join(lines)
        data, _ = _parse_front_matter(content)
        self.assertEqual(data["topics"], '["x", "y"]')
        self.assertNotIsInstance(data["topics"], list)

    def test_indented_line_without_active_section_falls_back_to_top_level(self):
        """
        Regression case: an indented line encountered while no section is
        currently open is NOT silently dropped. Because the sub-key branch
        only triggers when ``current_section`` is truthy, the line falls
        through to the top-level regex match, which strips leading
        whitespace from the key name and stores it at the top level.
        """
        lines = [
            "---",
            "  orphan: value",
            "name: test",
            "---",
            "Body",
        ]
        content = "\n".join(lines)
        data, _ = _parse_front_matter(content)
        self.assertEqual(data, {"orphan": "value", "name": "test"})

    def test_line_without_colon_is_ignored(self):
        """A malformed line with no colon separator is silently skipped."""
        lines = [
            "---",
            "this line has no colon at all",
            "name: test",
            "---",
            "Body",
        ]
        content = "\n".join(lines)
        data, _ = _parse_front_matter(content)
        self.assertEqual(data, {"name": "test"})

    def test_empty_front_matter_block_returns_empty_dict(self):
        """An entirely empty front-matter block (immediately closed) returns an empty dict."""
        lines = ["---", "---", "Body"]
        content = "\n".join(lines)
        data, body = _parse_front_matter(content)
        self.assertEqual(data, {})
        self.assertEqual(body, "Body")

    def test_real_jules_knowledge_skill_frontmatter_parses_as_expected(self):
        """
        Integration-style check: parsing the real jules-knowledge SKILL.md
        file with the new dependency-free parser yields the same structural
        shape previously guaranteed by PyYAML's safe_load.
        """
        skill_md_path = os.path.join(SKILLS_DIR, "jules-knowledge", "SKILL.md")
        content = _read(skill_md_path)
        data, body = _parse_front_matter(content)

        self.assertIsNotNone(data)
        self.assertEqual(data.get("name"), "jules-knowledge")
        self.assertIn("description", data)

        metadata = data.get("metadata")
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata.get("layout"), "default")
        self.assertEqual(metadata.get("okf_version"), "0.1")
        self.assertEqual(metadata.get("type"), "Agent Skill")
        self.assertIsInstance(metadata.get("topics"), list)
        self.assertEqual(metadata.get("topics"), ["aws", "3-tier", "ai-agents", "instructions"])

        # The body should not include any of the front matter delimiters.
        self.assertNotIn("---\nname: jules-knowledge", body)


class TestJulesKnowledgeDsomSection(unittest.TestCase):
    """
    Content assertions for the newly added Deep State of Mind (DSOM) section
    (Section 12) inside `.agents/skills/jules-knowledge/SKILL.md`.
    """

    @classmethod
    def setUpClass(cls):
        cls.skill_md_path = os.path.join(SKILLS_DIR, "jules-knowledge", "SKILL.md")
        cls.content = _read(cls.skill_md_path)

    def test_dsom_section_heading_present(self):
        """Verify the new Section 12 heading is present in the document."""
        self.assertIn(
            "## 12. Deep State of Mind (DSOM) For My AI Framework & Sovereign AI Protocol",
            self.content,
        )

    def test_tri_phasic_mind_cognitive_pipeline_documented(self):
        """Verify the Tri-Phasic Mind cognitive model is documented with all three states."""
        self.assertIn("Tri-Phasic Mind Cognitive Execution Pipeline", self.content)
        for state in ("Active State (The Conscious Mind)", "Twilight State (The Subconscious Mind)",
                      "Deep State (The Unconscious / Dream Mind)"):
            self.assertIn(state, self.content)

    def test_sovereign_memory_stratification_plane_documented(self):
        """Verify the memory stratification layers are all documented."""
        self.assertIn("Sovereign Memory Stratification Plane", self.content)
        for layer in ("Sensory Memory", "Working Memory", "Episodic Memory", "Semantic Memory"):
            self.assertIn(layer, self.content)

    def test_nineteen_entry_points_are_enumerated(self):
        """
        Verify exactly 19 numbered DSOM Entry Points are enumerated under item 48,
        matching the manifest's claim of '19 Entry Points'.
        """
        self.assertIn("The 19 Sovereign DSOM Entry Points", self.content)
        # The 19 sub-bullets use 4-space indentation with a single asterisk
        # (italic), distinguishing them from the outer bold (**) numbered
        # knowledge items (45-48) which are not indented.
        entry_point_lines = re.findall(r"^ {4}(\d+)\.\s+\*[^*]", self.content, re.MULTILINE)
        numbers = [int(n) for n in entry_point_lines]
        self.assertEqual(numbers, list(range(1, 20)))

    def test_numbered_items_45_through_48_present(self):
        """Verify the four new numbered knowledge items (45-48) were appended."""
        for item_number in (45, 46, 47, 48):
            self.assertIn(f"{item_number}. **", self.content)

    def test_document_still_ends_with_dsom_footer_after_new_section(self):
        """Verify the DSOM footer remains the very last content after the new section was appended."""
        stripped = self.content.strip()
        self.assertTrue(
            stripped.endswith(
                "*Deep State of Mind (DSOM) For My AI Protocol | Harisfazillah Jamel (LinuxMalaysia) | 2026-08-13*"
            )
        )


if __name__ == "__main__":
    unittest.main()
