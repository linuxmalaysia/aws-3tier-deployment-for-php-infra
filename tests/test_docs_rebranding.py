"""
Unit tests for the PHP CodeIgniter rebranding changes in this PR across:
    - AGENTS.md
    - README.md
    - llms.txt
    - docs/index.md
    - docs/developer-design-mapping.md

This PR retired the old "AI & Web Infra" / RAGFlow / LangFuse / antigravity
branding (and the standalone Server01/02/03 AI-tier naming scheme) in favor of
a PHP CodeIgniter web application served by Nginx + PHP-FPM. It also removed
docs/antigravity-skills.md and docs/ragflow-langfuse.md and added the new
docs/codeigniter-php-fpm.md guide. These tests verify the rebranding is
complete, internally consistent, and free of dangling references/links to the
removed documentation pages.
"""
import os
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

AGENTS_PATH = os.path.join(REPO_ROOT, "AGENTS.md")
README_PATH = os.path.join(REPO_ROOT, "README.md")
LLMS_TXT_PATH = os.path.join(REPO_ROOT, "llms.txt")
DOCS_INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
DEV_DESIGN_MAPPING_PATH = os.path.join(REPO_ROOT, "docs", "developer-design-mapping.md")

# Files that were deleted as part of this PR's rebranding; nothing in the
# remaining docs should still link to them.
REMOVED_DOC_LINKS = ("antigravity-skills.md", "ragflow-langfuse.md")

# Old branding/naming terms that should have been fully retired.
LEGACY_TERMS = ("RAGFlow", "LangFuse", "AI Tier", "AI Infra", "AI-tier")


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class RebrandingFilesExistTest(unittest.TestCase):
    def test_all_expected_files_exist(self):
        for path in (AGENTS_PATH, README_PATH, LLMS_TXT_PATH, DOCS_INDEX_PATH, DEV_DESIGN_MAPPING_PATH):
            self.assertTrue(os.path.isfile(path), f"missing expected file: {path}")

    def test_removed_docs_no_longer_exist(self):
        for name in REMOVED_DOC_LINKS:
            path = os.path.join(REPO_ROOT, "docs", name)
            self.assertFalse(os.path.isfile(path), f"{name} should have been removed by this PR")


class NoDanglingLinksToRemovedDocsTest(unittest.TestCase):
    """Ensure no remaining documentation references the deleted pages."""

    def setUp(self):
        self.contents = {
            "AGENTS.md": _load(AGENTS_PATH),
            "README.md": _load(README_PATH),
            "llms.txt": _load(LLMS_TXT_PATH),
            "docs/index.md": _load(DOCS_INDEX_PATH),
            "docs/developer-design-mapping.md": _load(DEV_DESIGN_MAPPING_PATH),
        }

    def test_no_file_references_removed_docs(self):
        for filename, content in self.contents.items():
            for removed in REMOVED_DOC_LINKS:
                self.assertNotIn(
                    removed, content,
                    f"{filename} still references removed doc: {removed}",
                )

    def test_no_file_contains_legacy_ai_branding_terms(self):
        for filename, content in self.contents.items():
            for term in LEGACY_TERMS:
                self.assertNotIn(
                    term, content,
                    f"{filename} still contains legacy branding term: {term!r}",
                )


class AgentsMdContentTest(unittest.TestCase):
    def setUp(self):
        self.content = _load(AGENTS_PATH)

    def test_title_references_php_and_web_infra(self):
        self.assertIn("AWS 3-Tier Deployment for PHP & Web Infra", self.content)

    def test_mission_mentions_codeigniter_and_nginx_php_fpm(self):
        self.assertIn("PHP CodeIgniter web applications", self.content)
        self.assertIn("Nginx and PHP-FPM", self.content)

    def test_architecture_class_mentions_nginx_php_fpm(self):
        self.assertIn("ASG with Nginx + PHP-FPM", self.content)

    def test_target_os_mentions_ubuntu_and_amazon_linux(self):
        self.assertIn("Ubuntu 26.04 LTS", self.content)
        self.assertIn("Amazon Linux 2023", self.content)

    def test_caching_layer_mentions_codeigniter_nodes(self):
        self.assertIn("shared session and cache store for CodeIgniter nodes", self.content)


class ReadmeContentTest(unittest.TestCase):
    def setUp(self):
        self.content = _load(README_PATH)

    def test_title_references_php_codeigniter(self):
        self.assertIn(
            "# AWS 3-Tier Deployment for PHP CodeIgniter Web Application (with OpenTofu)",
            self.content,
        )

    def test_repo_clone_url_updated_to_php_infra_repo(self):
        self.assertIn(
            "https://github.com/linuxmalaysia/aws-3tier-deployment-for-php-infra.git",
            self.content,
        )

    def test_architecture_diagram_shows_nginx_php_fpm_frontend(self):
        self.assertIn("Frontend Nginx", self.content)
        self.assertIn("+ PHP-FPM", self.content)

    def test_database_ingress_mentions_mysql_and_postgresql_ports(self):
        self.assertIn("port 3306 (MySQL)", self.content)
        self.assertIn("5432 (PostgreSQL)", self.content)

    def test_documentation_index_links_to_codeigniter_guide(self):
        self.assertIn("docs/codeigniter-php-fpm.md", self.content)

    def test_documentation_index_does_not_link_to_removed_antigravity_skills_page(self):
        self.assertNotIn("antigravity-skills", self.content)


class LlmsTxtContentTest(unittest.TestCase):
    def setUp(self):
        self.content = _load(LLMS_TXT_PATH)

    def test_title_references_php_codeigniter(self):
        self.assertIn(
            "# AWS 3-Tier Deployment for PHP CodeIgniter Web Application (with OpenTofu)",
            self.content,
        )

    def test_references_codeigniter_deployment_guide(self):
        self.assertIn("docs/codeigniter-php-fpm.md", self.content)

    def test_project_resource_links_are_relative_markdown_paths(self):
        # Sanity check that every square-bracket link target referencing docs/
        # points to an existing file relative to the repo root.
        import re
        for match in re.finditer(r"\]\((docs/[^)]+\.md)\)", self.content):
            rel_path = match.group(1)
            full_path = os.path.join(REPO_ROOT, rel_path)
            self.assertTrue(os.path.isfile(full_path), f"broken link target: {rel_path}")


class DocsIndexContentTest(unittest.TestCase):
    def setUp(self):
        self.content = _load(DOCS_INDEX_PATH)

    def test_has_jekyll_front_matter(self):
        self.assertTrue(self.content.startswith("---\n"))
        self.assertIn("layout: default", self.content)
        self.assertIn('title: "AWS Secure 3-Tier Architecture Documentation"', self.content)

    def test_technical_overview_mentions_nginx_php_fpm_codeigniter(self):
        self.assertIn("Nginx + PHP-FPM (CodeIgniter PHP Application)", self.content)

    def test_documentation_index_links_to_codeigniter_guide_html(self):
        self.assertIn("codeigniter-php-fpm.html", self.content)


class DeveloperDesignMappingContentTest(unittest.TestCase):
    def setUp(self):
        self.content = _load(DEV_DESIGN_MAPPING_PATH)

    def test_describes_three_separate_standalone_servers(self):
        self.assertIn("three separate, standalone Ubuntu 26.04 LTS servers", self.content)

    def test_no_longer_describes_four_separate_servers(self):
        self.assertNotIn("four separate", self.content)

    def test_uses_application_servers_terminology(self):
        self.assertIn("application servers", self.content.lower())


if __name__ == "__main__":
    unittest.main()