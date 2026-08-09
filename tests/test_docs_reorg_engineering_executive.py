#!/usr/bin/env python3
"""Unit tests for the Engineering/Executive documentation reorganization PR.

This PR relocates most technical documentation from a flat ``docs/`` layout
into two persona-scoped subdirectories:

* ``docs/engineering/`` -- implementation, security, and CI/CD guides
  (including the ``docs/engineering/modules/`` infrastructure submodule
  docs).
* ``docs/executive/``   -- financial, roadmap, and compliance blueprints.

For every relocated file, a short bold "category tag" line (e.g.
``**[DEVOPS EXECUTION]**`` or ``**[SECURITY & COMPLIANCE]**``) was inserted
immediately after the OKF YAML front matter and before the first Markdown
heading.

In addition:

* ``README.md`` reorganizes its documentation catalog into four numbered
  sections and rewrites every link to point at the new
  ``docs/engineering/...`` / ``docs/executive/...`` paths.
* ``docs/_config.yml`` rewrites its Jekyll navbar entries to the new paths
  and drops three navbar items (``Root Files``, ``Scripts``,
  ``CI/CD Pipeline``) that no longer have a dedicated top-level page.
* ``.agents/skills/jules-knowledge/SKILL.md`` updates every inline
  ``docs/...`` file-path reference used in its numbered knowledge items to
  the new ``docs/engineering/...`` / ``docs/executive/...`` locations.
* ``docs/engineering/architecture.md`` gains a brand new
  "AI Agent Data Flow & Zero-Trust Integration" section (with a Mermaid
  sequence diagram) that did not exist before this PR.

These tests are dependency-free (no PyYAML) and reuse ``scripts/prepare_docs``
for front-matter parsing, following the pattern already used by
``tests/test_performance_analysis_docs.py`` and
``tests/test_production_costing_docs.py``.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_docs_reorg_engineering_executive
"""
import os
import re
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import prepare_docs  # noqa: E402  (import after sys.path manipulation)

DOCS_DIR = os.path.join(REPO_ROOT, "docs")
ENGINEERING_DIR = os.path.join(DOCS_DIR, "engineering")
EXECUTIVE_DIR = os.path.join(DOCS_DIR, "executive")
README_PATH = os.path.join(REPO_ROOT, "README.md")
CONFIG_PATH = os.path.join(DOCS_DIR, "_config.yml")
SKILL_PATH = os.path.join(REPO_ROOT, ".agents", "skills", "jules-knowledge", "SKILL.md")

FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)

# Relative (to docs/) old-path -> new-path mapping for every file relocated
# by this PR that is in scope for these tests.
RELOCATED_FILES = {
    "SOP-KNOWLEDGE-FIRST-DISCOVERY.md": "engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.md",
    "ami-design.md": "engineering/ami-design.md",
    "architecture.md": "engineering/architecture.md",
    "asg-separation-of-concern.md": "engineering/asg-separation-of-concern.md",
    "cicd.md": "engineering/cicd.md",
    "codeigniter-php-fpm.md": "engineering/codeigniter-php-fpm.md",
    "developer-design-mapping.md": "engineering/developer-design-mapping.md",
    "github-detach-fork.md": "engineering/github-detach-fork.md",
    "gitlab-efs-cicd.md": "engineering/gitlab-efs-cicd.md",
    "jumphost.md": "engineering/jumphost.md",
    "modules/alb.md": "engineering/modules/alb.md",
    "modules/asg.md": "engineering/modules/asg.md",
    "modules/elasticache.md": "engineering/modules/elasticache.md",
    "modules/fusio.md": "engineering/modules/fusio.md",
    "modules/jumphost.md": "engineering/modules/jumphost.md",
    "modules/rds.md": "engineering/modules/rds.md",
    "modules/security_groups.md": "engineering/modules/security_groups.md",
    "modules/standalone_ec2.md": "engineering/modules/standalone_ec2.md",
    "modules/vpc.md": "engineering/modules/vpc.md",
    "modules/waf.md": "engineering/modules/waf.md",
    "opentofu-migration.md": "engineering/opentofu-migration.md",
    "performance-analysis.md": "engineering/performance-analysis.md",
}

# New-path (relative to docs/) -> expected bold category tag text (without
# the surrounding "**[" / "]**" markers).
EXPECTED_TAGS = {
    "engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.md": "SECURITY & COMPLIANCE",
    "engineering/ami-design.md": "DEVOPS EXECUTION",
    "engineering/architecture.md": "DEVOPS EXECUTION",
    "engineering/asg-separation-of-concern.md": "DEVOPS EXECUTION",
    "engineering/cicd.md": "DEVOPS EXECUTION",
    "engineering/codeigniter-php-fpm.md": "DEVOPS EXECUTION",
    "engineering/developer-design-mapping.md": "DEVOPS EXECUTION",
    "engineering/github-detach-fork.md": "DEVOPS EXECUTION",
    "engineering/gitlab-efs-cicd.md": "DEVOPS EXECUTION",
    "engineering/jumphost.md": "SECURITY & COMPLIANCE",
    "engineering/modules/alb.md": "DEVOPS EXECUTION",
    "engineering/modules/asg.md": "DEVOPS EXECUTION",
    "engineering/modules/elasticache.md": "DEVOPS EXECUTION",
    "engineering/modules/fusio.md": "DEVOPS EXECUTION",
    "engineering/modules/jumphost.md": "DEVOPS EXECUTION",
    "engineering/modules/rds.md": "DEVOPS EXECUTION",
    "engineering/modules/security_groups.md": "DEVOPS EXECUTION",
    "engineering/modules/standalone_ec2.md": "DEVOPS EXECUTION",
    "engineering/modules/vpc.md": "DEVOPS EXECUTION",
    "engineering/modules/waf.md": "DEVOPS EXECUTION",
    "engineering/opentofu-migration.md": "DEVOPS EXECUTION",
    "engineering/performance-analysis.md": "DEVOPS EXECUTION",
}


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _split_front_matter(text):
    """Split a Markdown document into (front_matter_dict, body_text).

    Raises AssertionError if the document does not open with a ``---``
    delimited YAML front matter block, mirroring the OKF Rule 6 requirement
    documented in docs/engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.md.
    """
    match = FRONT_MATTER_RE.match(text)
    assert match is not None, "document does not start with '---' front matter"
    fm_text = "---\n" + match.group(1) + "\n---"
    body = match.group(2)
    return prepare_docs.parse_yaml_front_matter(fm_text), body


def _first_nonblank_line(body):
    for line in body.splitlines():
        if line.strip():
            return line.strip()
    return ""


class DocsRelocationTestCase(unittest.TestCase):
    """Every listed file must now live under docs/engineering/ and must no
    longer exist at its old flat docs/ location."""

    def test_relocated_files_exist_at_new_path(self):
        for old_rel, new_rel in RELOCATED_FILES.items():
            with self.subTest(old=old_rel, new=new_rel):
                new_path = os.path.join(DOCS_DIR, new_rel)
                self.assertTrue(
                    os.path.isfile(new_path),
                    f"expected relocated file to exist at docs/{new_rel}",
                )

    def test_old_flat_paths_no_longer_exist(self):
        for old_rel in RELOCATED_FILES:
            with self.subTest(old=old_rel):
                old_path = os.path.join(DOCS_DIR, old_rel)
                self.assertFalse(
                    os.path.isfile(old_path),
                    f"stale file still present at old location docs/{old_rel}",
                )

    def test_engineering_modules_directory_replaces_flat_modules_directory(self):
        self.assertTrue(os.path.isdir(os.path.join(ENGINEERING_DIR, "modules")))
        self.assertFalse(os.path.isdir(os.path.join(DOCS_DIR, "modules")))

    def test_relocated_files_cover_all_expected_tag_entries(self):
        """Regression: every file we expect a category tag on must also be
        present in the relocation map (keeps the two data tables in sync)."""
        relocated_new_paths = set(RELOCATED_FILES.values())
        self.assertEqual(relocated_new_paths, set(EXPECTED_TAGS.keys()))


class CategoryTagTestCase(unittest.TestCase):
    """Every relocated file must carry a bold '**[CATEGORY]**' tag line
    directly after its OKF front matter and before its first heading."""

    def test_tag_present_immediately_after_front_matter(self):
        for rel_path, expected_tag in EXPECTED_TAGS.items():
            with self.subTest(path=rel_path):
                full_path = os.path.join(DOCS_DIR, rel_path)
                text = _read(full_path)
                _, body = _split_front_matter(text)
                first_line = _first_nonblank_line(body)
                self.assertEqual(
                    first_line,
                    f"**[{expected_tag}]**",
                    f"{rel_path}: expected tag '**[{expected_tag}]**' as the "
                    f"first non-blank line of the body, got {first_line!r}",
                )

    def test_tag_precedes_first_markdown_heading(self):
        for rel_path, expected_tag in EXPECTED_TAGS.items():
            with self.subTest(path=rel_path):
                full_path = os.path.join(DOCS_DIR, rel_path)
                text = _read(full_path)
                _, body = _split_front_matter(text)
                tag_line = f"**[{expected_tag}]**"
                tag_idx = body.index(tag_line)
                heading_match = re.search(r"^#", body, re.MULTILINE)
                self.assertIsNotNone(heading_match, f"{rel_path}: no Markdown heading found")
                self.assertLess(
                    tag_idx,
                    heading_match.start(),
                    f"{rel_path}: category tag must appear before the first heading",
                )

    def test_only_known_category_values_are_used(self):
        allowed = {"DEVOPS EXECUTION", "SECURITY & COMPLIANCE"}
        self.assertTrue(set(EXPECTED_TAGS.values()).issubset(allowed))

    def test_tag_appears_exactly_once_per_file(self):
        for rel_path, expected_tag in EXPECTED_TAGS.items():
            with self.subTest(path=rel_path):
                full_path = os.path.join(DOCS_DIR, rel_path)
                text = _read(full_path)
                self.assertEqual(text.count(f"**[{expected_tag}]**"), 1)


class FrontMatterStillValidTestCase(unittest.TestCase):
    """The relocation + tag insertion must not have corrupted the OKF front
    matter of any of the affected files."""

    REQUIRED_KEYS = ("layout", "okf_version", "type", "title", "timestamp", "topics")

    def test_front_matter_has_all_required_okf_keys(self):
        for rel_path in EXPECTED_TAGS:
            with self.subTest(path=rel_path):
                full_path = os.path.join(DOCS_DIR, rel_path)
                fm, _ = _split_front_matter(_read(full_path))
                for key in self.REQUIRED_KEYS:
                    self.assertIn(key, fm, f"{rel_path}: missing OKF key '{key}'")

    def test_topics_is_a_non_empty_list(self):
        for rel_path in EXPECTED_TAGS:
            with self.subTest(path=rel_path):
                full_path = os.path.join(DOCS_DIR, rel_path)
                fm, _ = _split_front_matter(_read(full_path))
                self.assertIsInstance(fm["topics"], list)
                self.assertGreater(len(fm["topics"]), 0)

    def test_layout_is_default(self):
        for rel_path in EXPECTED_TAGS:
            with self.subTest(path=rel_path):
                full_path = os.path.join(DOCS_DIR, rel_path)
                fm, _ = _split_front_matter(_read(full_path))
                self.assertEqual(fm["layout"], "default")

    def test_sop_front_matter_with_unquoted_type_still_parses(self):
        """Regression/edge case: the SOP file uses an unquoted scalar
        (``type: standard_operating_procedure``) unlike the quoted
        ``type: "Technical Reference Guide"`` used elsewhere. Both forms
        must parse identically via prepare_docs.parse_yaml_front_matter."""
        full_path = os.path.join(ENGINEERING_DIR, "SOP-KNOWLEDGE-FIRST-DISCOVERY.md")
        fm, _ = _split_front_matter(_read(full_path))
        self.assertEqual(fm["type"], "standard_operating_procedure")
        self.assertIn("okf", fm["topics"])


class ArchitectureAiAgentSectionTestCase(unittest.TestCase):
    """Tests for the new 'AI Agent Data Flow & Zero-Trust Integration'
    section added to docs/engineering/architecture.md."""

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(ENGINEERING_DIR, "architecture.md")
        cls.content = _read(cls.path)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(self.path))

    def test_new_section_heading_present(self):
        self.assertIn("## AI Agent Data Flow & Zero-Trust Integration", self.content)

    def test_mermaid_sequence_diagram_present(self):
        self.assertIn("```mermaid", self.content)
        self.assertIn("sequenceDiagram", self.content)

    def test_mermaid_diagram_participants_present(self):
        for participant in [
            "actor Agent as Google Agent / MCP Gateway",
            "participant WAF as AWS WAF v2",
            "participant ALB as Application Load Balancer",
            "participant RAG as RAGFlow ASG (Private Subnet)",
            "participant EFS as Amazon EFS (Model Weight Cache)",
            "participant DB as RDS PostgreSQL (pgvector)",
        ]:
            with self.subTest(participant=participant):
                self.assertIn(participant, self.content)

    def test_link_to_ragflow_langfuse_guide_present(self):
        self.assertIn(
            "**[AI Agent Data Flow & Zero-Trust Handshake Guide](ragflow-langfuse.html)**",
            self.content,
        )

    def test_new_section_appears_between_schematic_and_network_isolation(self):
        schematic_idx = self.content.index("## Architectural Schematic")
        ai_section_idx = self.content.index("## AI Agent Data Flow & Zero-Trust Integration")
        isolation_idx = self.content.index("## Network Isolation Layers")
        self.assertLess(schematic_idx, ai_section_idx)
        self.assertLess(ai_section_idx, isolation_idx)

    def test_pdpa_alignment_mentions_region(self):
        self.assertIn("ap-southeast-5", self.content)
        self.assertIn("PDPA", self.content)


class SkillMdKnowledgeItemPathsTestCase(unittest.TestCase):
    """Tests for the inline docs/... path updates in
    .agents/skills/jules-knowledge/SKILL.md."""

    # (expected up-to-date path, forbidden stale path) pairs, one per
    # numbered knowledge item touched by this PR.
    PATH_PAIRS = [
        ("docs/engineering/developer-design-mapping.md", "docs/developer-design-mapping.md"),
        ("docs/engineering/asg-separation-of-concern.md", "docs/asg-separation-of-concern.md"),
        ("docs/engineering/postgresql-comparison.md", "docs/postgresql-comparison.md"),
        ("docs/engineering/jumphost.md", "docs/jumphost.md"),
        ("docs/engineering/ami-design.md", "docs/ami-design.md"),
        ("docs/engineering/ragflow-langfuse.md", "docs/ragflow-langfuse.md"),
        ("docs/executive/dr-options.md", "docs/dr-options.md"),
        ("docs/executive/hybrid-onprem.md", "docs/hybrid-onprem.md"),
        ("docs/executive/costing.md", "docs/costing.md"),
        ("docs/engineering/gitlab-efs-cicd.md", "docs/gitlab-efs-cicd.md"),
        ("docs/engineering/opentofu-migration.md", "docs/opentofu-migration.md"),
        ("docs/engineering/route53.md", "docs/route53.md"),
    ]

    @classmethod
    def setUpClass(cls):
        cls.content = _read(SKILL_PATH)

    def test_skill_file_exists(self):
        self.assertTrue(os.path.isfile(SKILL_PATH))

    def test_updated_paths_present(self):
        for expected_path, _stale_path in self.PATH_PAIRS:
            with self.subTest(path=expected_path):
                self.assertIn(
                    f"`{expected_path}`",
                    self.content,
                    f"expected SKILL.md to reference `{expected_path}`",
                )

    def test_stale_flat_paths_absent(self):
        for _expected_path, stale_path in self.PATH_PAIRS:
            with self.subTest(path=stale_path):
                self.assertNotIn(
                    f"`{stale_path}`",
                    self.content,
                    f"stale reference `{stale_path}` should have been rewritten",
                )

    def test_referenced_target_files_exist_on_disk(self):
        for expected_path, _stale_path in self.PATH_PAIRS:
            with self.subTest(path=expected_path):
                full_path = os.path.join(REPO_ROOT, expected_path)
                self.assertTrue(
                    os.path.isfile(full_path),
                    f"SKILL.md references `{expected_path}` but that file does not exist",
                )

    def test_dr_options_item_25_26_27_all_use_executive_path(self):
        """Regression: three separate numbered items (25, 26, 27) all point
        at docs/executive/dr-options.md; make sure none regressed."""
        self.assertEqual(
            self.content.count("`docs/executive/dr-options.md`"), 3
        )

    def test_costing_item_29_30_both_use_executive_path(self):
        self.assertEqual(self.content.count("`docs/executive/costing.md`"), 2)

    def test_terraform_module_paths_untouched(self):
        """Sanity check: terraform/modules/* paths (unrelated to the docs
        reorg) must remain unaffected by this change."""
        self.assertIn("`terraform/modules/standalone_ec2/`", self.content)
        self.assertIn("`terraform/modules/jumphost/`", self.content)


class ReadmeDocumentationPortalTestCase(unittest.TestCase):
    """Tests for the reorganized 'Documentation Portal Index' section of
    README.md."""

    LINK_RE = re.compile(r"\]\((docs/[^)\s]+\.md)\)")

    @classmethod
    def setUpClass(cls):
        cls.content = _read(README_PATH)

    def test_readme_exists(self):
        self.assertTrue(os.path.isfile(README_PATH))

    def test_four_numbered_sections_present_in_order(self):
        headers = [
            "### 1. Conceptual Alignment & Architecture (Engineering)",
            "### 2. Infrastructure Submodules (Engineering)",
            "### 3. Advanced Operational Guides (Engineering)",
            "### 4. Strategic Financial Blueprints (Executive)",
        ]
        positions = [self.content.index(h) for h in headers]
        self.assertEqual(positions, sorted(positions))

    def test_all_markdown_doc_links_resolve_to_existing_files(self):
        links = self.LINK_RE.findall(self.content)
        self.assertGreater(len(links), 0, "no docs/*.md links found in README.md")
        for link in links:
            with self.subTest(link=link):
                self.assertTrue(
                    os.path.isfile(os.path.join(REPO_ROOT, link)),
                    f"README.md links to {link} but that file does not exist",
                )

    def test_all_doc_links_use_engineering_or_executive_prefix(self):
        """Regression: no link should still point at the old flat docs/
        layout (e.g. docs/architecture.md instead of
        docs/engineering/architecture.md)."""
        links = self.LINK_RE.findall(self.content)
        for link in links:
            with self.subTest(link=link):
                self.assertTrue(
                    link.startswith("docs/engineering/") or link.startswith("docs/executive/"),
                    f"{link} does not use the new engineering/executive prefix",
                )

    def test_stale_flat_links_absent(self):
        stale_links = [
            "docs/architecture.md",
            "docs/costing.md",
            "docs/production-costing.md",
            "docs/dr-options.md",
            "docs/hybrid-onprem.md",
            "docs/ami-design.md",
            "docs/gitlab-efs-cicd.md",
            "docs/route53.md",
            "docs/jumphost.md",
            "docs/postgresql-comparison.md",
            "docs/opentofu-migration.md",
            "docs/codeigniter-php-fpm.md",
            "docs/developer-design-mapping.md",
            "docs/asg-separation-of-concern.md",
            "docs/modules/vpc.md",
        ]
        for stale in stale_links:
            with self.subTest(stale=stale):
                self.assertNotIn(f"]({stale})", self.content)

    def test_ai_agent_data_flow_entry_present(self):
        self.assertIn(
            "**[AI Agent Data Flow & Zero-Trust Handshake](docs/engineering/ragflow-langfuse.md):**",
            self.content,
        )

    def test_ai_agent_entry_between_architecture_and_opentofu_links(self):
        arch_idx = self.content.index("[System Architecture Details](docs/engineering/architecture.md)")
        ai_idx = self.content.index("[AI Agent Data Flow & Zero-Trust Handshake]")
        opentofu_idx = self.content.index("[OpenTofu Migration Guide](docs/engineering/opentofu-migration.md)")
        self.assertLess(arch_idx, ai_idx)
        self.assertLess(ai_idx, opentofu_idx)

    def test_strategic_financial_blueprints_order(self):
        section_match = re.search(
            r"### 4\. Strategic Financial Blueprints \(Executive\)\n(.*?)(?=\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section = section_match.group(1)
        ordered_links = [
            "docs/executive/aws-adoption-roadmap.md",
            "docs/executive/dr-options.md",
            "docs/executive/hybrid-onprem.md",
            "docs/executive/costing.md",
            "docs/executive/production-costing.md",
        ]
        positions = [section.index(link) for link in ordered_links]
        self.assertEqual(positions, sorted(positions))

    def test_cost_figures_preserved(self):
        for figure in ["~$141.47", "~$898.54", "~$418.60", "~$1,037.73"]:
            with self.subTest(figure=figure):
                self.assertIn(figure, self.content)

    def test_infrastructure_submodules_section_uses_engineering_modules_path(self):
        section_match = re.search(
            r"### 2\. Infrastructure Submodules \(Engineering\)\n(.*?)(?=\n###|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        section = section_match.group(1)
        for module in ["vpc", "security_groups", "waf", "alb", "asg", "rds", "elasticache", "jumphost", "standalone_ec2"]:
            with self.subTest(module=module):
                self.assertIn(f"docs/engineering/modules/{module}.md", section)


class DocsConfigNavbarTestCase(unittest.TestCase):
    """Tests for the rewritten Jekyll navbar in docs/_config.yml."""

    NAVBAR_ENTRY_RE = re.compile(r'-\s*title:\s*"([^"]+)"\s*\n\s*url:\s*"([^"]+)"')

    EXPECTED_NAVBAR = [
        ("Home", "/"),
        ("Architecture", "/engineering/architecture.html"),
        ("Roadmap", "/executive/aws-adoption-roadmap.html"),
        ("AI Handshake", "/engineering/ragflow-langfuse.html"),
        ("Costing", "/executive/costing.html"),
        ("Production Costing", "/executive/production-costing.html"),
        ("Route 53", "/engineering/route53.html"),
        ("Secure Access", "/engineering/jumphost.html"),
        ("GitLab EFS CI/CD", "/engineering/gitlab-efs-cicd.html"),
        ("Disaster Recovery", "/executive/dr-options.html"),
        ("RDS vs Percona", "/engineering/postgresql-comparison.html"),
    ]

    @classmethod
    def setUpClass(cls):
        cls.content = _read(CONFIG_PATH)

    def test_config_file_exists(self):
        self.assertTrue(os.path.isfile(CONFIG_PATH))

    def test_navbar_entries_match_expected_list_and_order(self):
        entries = self.NAVBAR_ENTRY_RE.findall(self.content)
        self.assertEqual(entries, self.EXPECTED_NAVBAR)

    def test_removed_navbar_entries_absent(self):
        for removed_title in ["Root Files", "Scripts", "CI/CD Pipeline"]:
            with self.subTest(title=removed_title):
                self.assertNotIn(f'title: "{removed_title}"', self.content)

    def test_removed_navbar_urls_absent(self):
        for removed_url in ['"/root-files.html"', '"/scripts.html"', '"/cicd.html"']:
            with self.subTest(url=removed_url):
                self.assertNotIn(removed_url, self.content)

    def test_old_unprefixed_architecture_url_absent(self):
        """Regression: only the new '/engineering/architecture.html' value
        should exist; the bare '/architecture.html' quoted value must not."""
        self.assertNotIn('"/architecture.html"', self.content)

    def test_every_navbar_target_doc_exists(self):
        for title, url in self.EXPECTED_NAVBAR:
            if url == "/":
                continue
            with self.subTest(title=title, url=url):
                rel_md_path = url.lstrip("/").replace(".html", ".md")
                full_path = os.path.join(DOCS_DIR, rel_md_path)
                self.assertTrue(
                    os.path.isfile(full_path),
                    f"navbar entry {title!r} points at {url} but docs/{rel_md_path} does not exist",
                )

    def test_navbar_entry_count_unchanged_semantics(self):
        """There are exactly 11 navbar entries (Home + 10 documentation
        pages) after dropping the three removed root-level pages."""
        entries = self.NAVBAR_ENTRY_RE.findall(self.content)
        self.assertEqual(len(entries), 11)


if __name__ == "__main__":
    unittest.main()