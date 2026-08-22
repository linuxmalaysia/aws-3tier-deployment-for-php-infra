#!/usr/bin/env python3
"""Unit tests for the Active Context Manifest spatial memory anchor.

This test suite verifies that `.agents/brain/active_context_manifest.md` (the
Deep State of Mind (DSOM) "Working Memory" anchor):

* Exists and carries valid OKF v0.1 style front matter.
* Declares the updated Active Session Focus goal describing the DSOM
  Sovereign Framework adoption, the 19 Entry Points, the Tri-Phasic Mind
  cognitive model, and memory stratification architecture.
* Records the newly added Session Progress Checkpoints introduced by this
  change (dependency-free YAML parsing fix, DSOM entry point codification,
  and the manifest self-update), while preserving the pre-existing
  checkpoints and the still-pending checklist items.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_active_context_manifest
"""

import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANIFEST_PATH = os.path.join(REPO_ROOT, ".agents", "brain", "active_context_manifest.md")


def _read(path):
    """Read and return the full UTF-8 contents of the specified file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class TestActiveContextManifestFile(unittest.TestCase):
    """Basic presence and front matter checks for the manifest file."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(MANIFEST_PATH)

    def test_manifest_file_exists(self):
        """Verify the manifest file exists on disk."""
        self.assertTrue(os.path.isfile(MANIFEST_PATH))

    def test_starts_with_front_matter_delimiter(self):
        """Verify the manifest starts with the front matter delimiter on Line 1."""
        self.assertTrue(self.content.startswith("---\n"))

    def test_front_matter_contains_required_okf_fields(self):
        """Verify the raw front matter block declares the standard OKF fields."""
        parts = self.content.split("---", 2)
        self.assertGreaterEqual(len(parts), 3, "Missing front matter delimiters")
        raw_fm = parts[1]
        for field in ("layout", "okf_version", "type", "title", "timestamp", "topics", "description"):
            pattern = re.compile(rf"^{re.escape(field)}:", re.MULTILINE)
            self.assertRegex(
                raw_fm,
                pattern,
                f"'{field}' field missing from manifest front matter",
            )

    def test_front_matter_okf_version_and_layout(self):
        """Verify layout and okf_version retain their expected literal values."""
        parts = self.content.split("---", 2)
        raw_fm = parts[1]
        self.assertRegex(raw_fm, re.compile(r'^layout:\s*default\s*$', re.MULTILINE))
        self.assertRegex(raw_fm, re.compile(r'^okf_version:\s*"0\.1"\s*$', re.MULTILINE))


class TestActiveSessionFocusGoal(unittest.TestCase):
    """Tests for the updated 'Active Session Focus' goal statement."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(MANIFEST_PATH)

    def test_goal_line_present(self):
        """Verify the exact updated Goal bullet is present verbatim."""
        expected_goal = (
            "* **Goal:** Fully adopt the Deep State of Mind (DSOM) For My AI Sovereign "
            "Framework across Jules Knowledge (`.agents/skills/jules-knowledge/SKILL.md`) "
            "and spatial memory anchors, codifying the 19 Entry Points, Tri-Phasic Mind "
            "cognitive model, and memory stratification architecture."
        )
        self.assertIn(expected_goal, self.content)

    def test_goal_mentions_key_dsom_concepts(self):
        """Verify the goal statement references each core DSOM concept keyword."""
        for keyword in (
            "Deep State of Mind (DSOM) For My AI Sovereign Framework",
            "jules-knowledge/SKILL.md",
            "19 Entry Points",
            "Tri-Phasic Mind cognitive model",
            "memory stratification architecture",
        ):
            self.assertIn(keyword, self.content)

    def test_workspace_line_unchanged(self):
        """Verify the Workspace bullet was not altered by this change."""
        self.assertIn(
            "* **Workspace:** AWS 3-Tier PHP CodeIgniter Infrastructure deployment via OpenTofu.",
            self.content,
        )


class TestSessionProgressCheckpoints(unittest.TestCase):
    """Tests for the 'Session Progress Checkpoints' checklist section."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(MANIFEST_PATH)
        section_match = re.search(
            r"## 3\. Session Progress Checkpoints\n\n(.*?)\Z",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None, "Session Progress Checkpoints section not found"
        cls.checklist_section = section_match.group(1)

    def test_new_checked_items_added(self):
        """Verify the three new completed checkpoints introduced by this PR are present and checked."""
        for item in (
            "- [x] Fix `tests/test_antigravity_skills.py` to use dependency-free YAML frontmatter parsing",
            "- [x] Codify 19 DSOM Entry Points and Tri-Phasic Mind Cognitive Pipeline into `jules-knowledge` skill",
            "- [x] Update Spatial Memory Anchor `.agents/brain/active_context_manifest.md`",
        ):
            self.assertIn(item, self.checklist_section)

    def test_preexisting_checked_items_preserved(self):
        """Verify checkpoints that already existed before this change remain intact."""
        for item in (
            "- [x] Create `.agents/AGENTS.md` (Sovereign Constitution)",
            "- [x] Edit root `AGENTS.md` (Gateway to sovereign rules and Agent Skills ecosystem)",
            "- [x] Create `docs/SOP-KNOWLEDGE-FIRST-DISCOVERY.md` (SOP for Local Knowledge-First Discovery)",
            "- [x] Create `.agents/brain/active_context_manifest.md` (Active Context Index)",
            "- [x] Implement comprehensive suite of 5 custom Antigravity Agent Skills in `.agents/skills/`",
            "- [x] Add Agent Skills validation unit tests under `tests/test_antigravity_skills.py`",
        ):
            self.assertIn(item, self.checklist_section)

    def test_pending_items_updated_and_present(self):
        """Verify the still-pending checklist items are present, including the renamed unit-test entry."""
        self.assertIn("- [ ] Run `python3 scripts/prepare_docs.py` (Validate and compile OKF frontmatter)", self.checklist_section)
        self.assertIn("- [ ] Run Python unit tests suite", self.checklist_section)
        self.assertIn("- [ ] Complete pre-commit checklist and submit changes", self.checklist_section)
        # The old, less-specific wording should no longer be present standalone.
        self.assertNotIn("- [ ] Run Python unit tests\n", self.checklist_section)

    def test_checked_and_unchecked_item_counts(self):
        """Verify the checklist has exactly 9 completed and 3 pending items after this change."""
        checked = re.findall(r"^- \[x\]", self.checklist_section, re.MULTILINE)
        unchecked = re.findall(r"^- \[ \]", self.checklist_section, re.MULTILINE)
        self.assertEqual(len(checked), 9)
        self.assertEqual(len(unchecked), 3)

    def test_checklist_item_order_preserved(self):
        """Verify the three new items were appended in order, immediately before the pending items."""
        lines = [line for line in self.checklist_section.splitlines() if line.strip()]
        expected_tail = [
            "- [x] Add Agent Skills validation unit tests under `tests/test_antigravity_skills.py`",
            "- [x] Fix `tests/test_antigravity_skills.py` to use dependency-free YAML frontmatter parsing",
            "- [x] Codify 19 DSOM Entry Points and Tri-Phasic Mind Cognitive Pipeline into `jules-knowledge` skill",
            "- [x] Update Spatial Memory Anchor `.agents/brain/active_context_manifest.md`",
            "- [ ] Run `python3 scripts/prepare_docs.py` (Validate and compile OKF frontmatter)",
            "- [ ] Run Python unit tests suite",
            "- [ ] Complete pre-commit checklist and submit changes",
        ]
        self.assertEqual(lines[-len(expected_tail):], expected_tail)


if __name__ == "__main__":
    unittest.main()