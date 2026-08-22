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

    Returns:
        tuple: (dict or None, str) representing the parsed YAML dict (or None
               if malformed/non-mapping) and the remaining document body.
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


if __name__ == "__main__":
    unittest.main()
