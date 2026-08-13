#!/usr/bin/env python3
"""
Unit tests for the Google Antigravity-compatible Agent Skills in .agents/skills/.
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
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_front_matter(content):
    stripped = content.lstrip()
    if not stripped.startswith("---"):
        return None, ""
    parts = stripped.split("---", 2)
    if len(parts) < 3:
        return None, ""
    front_matter_text = parts[1]
    body_text = parts[2]

    # Simple YAML key-value parser
    front_matter = {}
    current_key = None
    for line in front_matter_text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.strip().startswith("-") and current_key:
            val = line.strip().lstrip("-").strip().strip('"').strip("'")
            if current_key not in front_matter or not isinstance(front_matter[current_key], list):
                front_matter[current_key] = []
            front_matter[current_key].append(val)
            continue

        match = re.match(r"^([^:]+):\s*(.*)$", line)
        if match:
            current_key = match.group(1).strip()
            val = match.group(2).strip().strip('"').strip("'")
            if val.startswith("[") and val.endswith("]"):
                items = [x.strip().strip('"').strip("'") for x in val[1:-1].split(",")]
                front_matter[current_key] = [x for x in items if x]
            else:
                front_matter[current_key] = val
    return front_matter, body_text


class TestAntigravitySkills(unittest.TestCase):

    def test_skills_directories_exist(self):
        """Verify that all expected skill directories and their SKILL.md exist."""
        self.assertTrue(os.path.isdir(SKILLS_DIR), "Skills directory does not exist")
        for skill in EXPECTED_SKILLS:
            skill_folder = os.path.join(SKILLS_DIR, skill)
            self.assertTrue(os.path.isdir(skill_folder), f"Skill folder '{skill}' does not exist")
            skill_md_path = os.path.join(skill_folder, "SKILL.md")
            self.assertTrue(os.path.isfile(skill_md_path), f"SKILL.md does not exist for '{skill}'")

    def test_skills_yaml_frontmatter_rules(self):
        """Verify frontmatter constraints and standard fields for each SKILL.md."""
        for skill in EXPECTED_SKILLS:
            skill_md_path = os.path.join(SKILLS_DIR, skill, "SKILL.md")
            content = _read(skill_md_path)

            # Rule: MUST start on Line 1, Column 1 with ---
            self.assertTrue(content.startswith("---\n"), f"SKILL.md for '{skill}' does not start with front matter delimiter on Line 1")

            front_matter, body = _parse_front_matter(content)
            self.assertIsNotNone(front_matter, f"Failed to parse front matter for '{skill}'")

            # Check required OKF v0.1 fields
            self.assertEqual(front_matter.get("layout"), "default", f"layout mismatch in '{skill}'")
            self.assertEqual(front_matter.get("okf_version"), "0.1", f"okf_version mismatch in '{skill}'")
            self.assertEqual(front_matter.get("type"), "Agent Skill", f"type mismatch in '{skill}'")
            self.assertTrue("title" in front_matter, f"title missing in '{skill}'")
            self.assertTrue("timestamp" in front_matter, f"timestamp missing in '{skill}'")
            self.assertTrue("topics" in front_matter, f"topics missing in '{skill}'")

            # Check required Antigravity fields
            self.assertEqual(front_matter.get("name"), skill, f"name field mismatch in '{skill}' frontmatter")
            self.assertTrue("description" in front_matter, f"description field missing in '{skill}'")

    def test_skills_conclude_with_dsom_footer(self):
        """Verify each SKILL.md concludes with the Deep State of Mind AI Protocol footer."""
        dsom_pattern = r"\*Deep State of Mind \(DSOM\) For My AI Protocol \| Harisfazillah Jamel \(LinuxMalaysia\) \| 2026-08-1[0-9]\*"
        for skill in EXPECTED_SKILLS:
            skill_md_path = os.path.join(SKILLS_DIR, skill, "SKILL.md")
            content = _read(skill_md_path).strip()
            lines = content.splitlines()
            last_lines = "\n".join(lines[-3:])
            self.assertIsNotNone(re.search(dsom_pattern, last_lines), f"Skill '{skill}' does not end with the standard DSOM footer. Last lines were: {last_lines}")

    def test_constitution_and_root_agents_reference_skills(self):
        """Verify that master AGENTS.md files contain reference descriptions for each skill."""
        for agents_file in ["AGENTS.md", ".agents/AGENTS.md"]:
            path = os.path.join(REPO_ROOT, agents_file)
            self.assertTrue(os.path.isfile(path))
            content = _read(path)
            for skill in EXPECTED_SKILLS:
                self.assertIn(skill, content, f"Skill '{skill}' is not mentioned in {agents_file}")


if __name__ == "__main__":
    unittest.main()
