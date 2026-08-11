#!/usr/bin/env python3
"""Unit tests for the Legal Notice and Strategic Review documents added in this PR.
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

import prepare_docs

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
REVIEW_MD_PATH = os.path.join(REPO_ROOT, "docs", "aws-vs-self-hosted-review.md")
LEGAL_MD_PATH = os.path.join(REPO_ROOT, "docs", "legal-notice.md")
LAYOUT_PATH = os.path.join(REPO_ROOT, "docs", "_layouts", "default.html")

ROOT_SITEMAP_TXT = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_TXT = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_XML = os.path.join(REPO_ROOT, "sitemap.xml")
DOCS_SITEMAP_XML = os.path.join(REPO_ROOT, "docs", "sitemap.xml")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

GH_BASE = "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
GB_BASE = "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/"

GH_REVIEW_URL = GH_BASE + "aws-vs-self-hosted-review.html"
GH_LEGAL_URL = GH_BASE + "legal-notice.html"
GB_REVIEW_URL = GB_BASE + "aws-vs-self-hosted-review"
GB_LEGAL_URL = GB_BASE + "legal-notice"
GH_HYBRID_ONPREM_URL = GH_BASE + "executive/hybrid-onprem.html"


def _read(path):
    """Read and return the UTF-8 text contents of a file.
    
    Parameters:
    	path: Path to the file to read.
    
    Returns:
    	str: The file contents."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class LegalNoticeAndStrategicReviewTestCase(unittest.TestCase):
    def test_files_exist(self):
        self.assertTrue(os.path.isfile(REVIEW_MD_PATH))
        self.assertTrue(os.path.isfile(LEGAL_MD_PATH))

    def test_front_matter_okf_review(self):
        content = _read(REVIEW_MD_PATH)
        self.assertTrue(content.startswith("---\n"))
        parts = content.split("---", 2)
        fm = prepare_docs.parse_yaml_front_matter(parts[1])
        self.assertEqual(fm["layout"], "default")
        self.assertEqual(fm["okf_version"], "0.1")
        self.assertEqual(fm["type"], "Technical Reference Guide")
        self.assertEqual(
            fm["title"],
            "Strategic Comparative Review: AWS-Native Managed Platform vs. Self-Hosted Custom Stack",
        )
        self.assertEqual(fm["topics"], ["aws", "3-tier", "on-premises", "comparison"])

    def test_front_matter_okf_legal(self):
        content = _read(LEGAL_MD_PATH)
        self.assertTrue(content.startswith("---\n"))
        parts = content.split("---", 2)
        fm = prepare_docs.parse_yaml_front_matter(parts[1])
        self.assertEqual(fm["layout"], "default")
        self.assertEqual(fm["okf_version"], "0.1")
        self.assertEqual(fm["type"], "Technical Reference Guide")
        self.assertEqual(
            fm["title"],
            "Legal Notice, Critical Assumptions & Disclaimer of Liability",
        )
        self.assertEqual(fm["topics"], ["aws", "3-tier", "legal", "disclaimer"])

    def test_legal_notice_sections(self):
        content = _read(LEGAL_MD_PATH)
        self.assertIn("1. Educational and Training Purpose", content)
        self.assertIn("2. Reliance on Critical Assumptions", content)
        self.assertIn("3. Privacy Statement & Data Protection", content)
        self.assertIn("4. Assumption of Risk & Liability Disclaimer", content)
        self.assertIn("based entirely on assumptions", content)
        self.assertIn("strictly for training, educational, and planning proposal purposes", content)
        self.assertIn("Use of this project, its code, and its documents is at your own risk", content)
        self.assertIn("We are not going to be responsible or liable", content)
        self.assertIn("We have done our best to protect anyone and organisation", content)

    def test_footer_link_in_layout(self):
        layout = _read(LAYOUT_PATH)
        self.assertIn("Legal Notice &amp; Disclaimer", layout)
        self.assertIn("legal-notice.html", layout)

    def test_links_in_index(self):
        index = _read(INDEX_PATH)
        self.assertIn("[Strategic Comparative Review: AWS-Native Managed Platform vs. Self-Hosted Custom Stack](aws-vs-self-hosted-review.html)", index)
        self.assertIn("[Legal Notice, Critical Assumptions & Disclaimer of Liability](legal-notice.html)", index)

    def test_indexed_in_llms_txt(self):
        llms = _read(LLMS_PATH)
        self.assertIn("[Strategic Comparative Review](docs/aws-vs-self-hosted-review.md)", llms)
        self.assertIn("[Legal Notice & Disclaimer](docs/legal-notice.md)", llms)

    def test_front_matter_timestamps_match_expected_value(self):
        for path in (REVIEW_MD_PATH, LEGAL_MD_PATH):
            with self.subTest(path=path):
                content = _read(path)
                parts = content.split("---", 2)
                fm = prepare_docs.parse_yaml_front_matter(parts[1])
                self.assertEqual(fm["timestamp"], "2026-08-11T12:00:00+08:00")

    def test_front_matter_topics_share_common_aws_and_3tier_tags(self):
        for path in (REVIEW_MD_PATH, LEGAL_MD_PATH):
            with self.subTest(path=path):
                content = _read(path)
                parts = content.split("---", 2)
                fm = prepare_docs.parse_yaml_front_matter(parts[1])
                self.assertIn("aws", fm["topics"])
                self.assertIn("3-tier", fm["topics"])

    def test_index_and_llms_titles_are_intentionally_distinct(self):
        """Regression: docs/index.md uses the full document title, while
        llms.txt intentionally uses a shortened title for the AI-agent
        index. Guard against accidentally collapsing the two."""
        index = _read(INDEX_PATH)
        llms = _read(LLMS_PATH)
        self.assertIn(
            "[Strategic Comparative Review: AWS-Native Managed Platform vs. Self-Hosted Custom Stack]",
            index,
        )
        self.assertNotIn(
            "[Strategic Comparative Review: AWS-Native Managed Platform vs. Self-Hosted Custom Stack]",
            llms,
        )
        self.assertIn("[Strategic Comparative Review]", llms)


class LegalNoticeTableOfContentsAnchorTestCase(unittest.TestCase):
    """Regression tests ensuring the in-page Table of Contents anchors in
    docs/legal-notice.md actually resolve to real headings using the
    standard GitHub-flavoured Markdown heading-slug algorithm."""

    HEADING_PATTERN = re.compile(r"^##\s+(\d+\.\s+.+)$", re.MULTILINE)
    TOC_LINK_PATTERN = re.compile(r"^\*\s+\[(.+?)\]\(#(.+?)\)$", re.MULTILINE)

    @staticmethod
    def _slugify(heading):
        # Mirrors GitHub-flavoured Markdown's heading-slug algorithm:
        # lowercase, strip punctuation (retaining spaces/hyphens), then
        # replace each individual space with a hyphen WITHOUT collapsing
        # consecutive hyphens (e.g. "Statement & Data" -> "statement--data"
        # once the "&" is stripped out, leaving the surrounding spaces).
        s = heading.lower().strip()
        s = re.sub(r"[^\w\s-]", "", s)
        s = s.replace(" ", "-")
        return s

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LEGAL_MD_PATH)
        cls.headings = cls.HEADING_PATTERN.findall(cls.content)
        cls.toc_links = cls.TOC_LINK_PATTERN.findall(cls.content)

    def test_exactly_four_numbered_sections_and_toc_entries(self):
        self.assertEqual(len(self.headings), 4)
        self.assertEqual(len(self.toc_links), 4)

    def test_each_heading_has_matching_toc_anchor(self):
        expected_slugs = {self._slugify(h) for h in self.headings}
        actual_slugs = {slug for _text, slug in self.toc_links}
        self.assertEqual(expected_slugs, actual_slugs)

    def test_toc_link_text_matches_heading_text(self):
        toc_texts = [text for text, _slug in self.toc_links]
        self.assertEqual(sorted(toc_texts), sorted(self.headings))


class AwsVsSelfHostedReviewContentTestCase(unittest.TestCase):
    """Content-level tests for docs/aws-vs-self-hosted-review.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(REVIEW_MD_PATH)

    def test_all_five_numbered_sections_present(self):
        for heading in [
            "## 1. Executive Summary & The Big Picture",
            "## 2. Technical Comparison Per Layer",
            "## 3. Sovereign Compliance & Legal Audits",
            "## 4. Comprehensive Financial Blueprint (TCO Comparison)",
            "## 5. Strategic Recommendation Matrix",
        ]:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)

    def test_compliance_risk_codes_present(self):
        for code in ["TS-05", "TS-06", "TS-04"]:
            with self.subTest(code=code):
                self.assertIn(code, self.content)

    def test_pdpa_and_region_references_present(self):
        self.assertIn("ap-southeast-5", self.content)
        self.assertIn("Malaysian Personal Data Protection Act (PDPA) 2010", self.content)
        self.assertIn("Section 129 PDPA", self.content)

    def test_one_year_tco_totals_present(self):
        self.assertIn("**$19,395.72 USD**", self.content)
        self.assertIn("**$26,005.56 USD**", self.content)

    def test_three_year_tco_totals_present(self):
        self.assertIn("Total 3-Year TCO: $39,430.80 USD (RM 177,438.60 MYR)", self.content)
        self.assertIn("Total 3-Year TCO: $78,016.80 USD (RM 351,075.60 MYR)", self.content)

    def test_architectural_mapping_table_header_present(self):
        self.assertIn(
            "| Architectural Layer | AWS-Native Managed Solution | Self-Hosted / Custom Stack "
            "| Strategic Trade-Off | Compliance & Risk Code |",
            self.content,
        )

    def test_footer_boilerplate_present(self):
        self.assertIn("CmsForNerd Infrastructure:", self.content)
        self.assertIn("Copyright © 2005 - 2026 Harisfazillah Jamel", self.content)
        self.assertIn("[ REL: 3.5.1 ] | [ STD: RFC_9116 ] | [ ENV: OPENTOFU_1.6 ] | [ VIEW: STANDARD ]", self.content)

    def test_code_fenced_diagrams_are_balanced(self):
        # Every opening ```text fence must have a matching closing ``` fence.
        fence_count = self.content.count("```")
        self.assertEqual(fence_count % 2, 0, "Unbalanced ``` code fences in review document")


class DefaultLayoutFooterRegressionTestCase(unittest.TestCase):
    """Regression tests to guard the docs/_layouts/default.html footer edit:
    ensure the pre-existing infrastructure link and other footer boilerplate
    remain untouched while the new Legal Notice link is correctly wired."""

    @classmethod
    def setUpClass(cls):
        cls.layout = _read(LAYOUT_PATH)

    def test_original_infrastructure_link_preserved(self):
        self.assertIn('href="https://linuxmalaysia.com"', self.layout)
        self.assertIn(">linuxmalaysia.com</a>", self.layout)

    def test_legal_notice_link_uses_relative_url_liquid_filter(self):
        self.assertIn("{{ '/legal-notice.html' | relative_url }}", self.layout)

    def test_bullet_separator_between_footer_links(self):
        pattern = re.compile(
            r">linuxmalaysia\.com</a>\s*&bull;\s*<a href=\"\{\{ '/legal-notice\.html' \| relative_url \}\}\""
        )
        self.assertRegex(self.layout, pattern)

    def test_legal_notice_reference_appears_exactly_once(self):
        self.assertEqual(self.layout.count("legal-notice.html"), 1)

    def test_other_footer_lines_unchanged(self):
        self.assertIn("Copyright &copy; 2005 - 2026 Harisfazillah Jamel<br>", self.layout)
        self.assertIn(
            "[ REL: 3.5.1 ] | [ STD: RFC_9116 ] | [ ENV: OPENTOFU_1.6 ] | [ VIEW: STANDARD ]<br>",
            self.layout,
        )
        self.assertIn(
            "Rendered: Statically Compiled at Build-time | MEM: 0 KB (Zero-runtime database-free)",
            self.layout,
        )


class SitemapTxtNewPageEntriesTestCase(unittest.TestCase):
    """Tests for the new sitemap.txt / docs/sitemap.txt entries introduced
    for the Strategic Review and Legal Notice pages."""

    SITEMAP_PATHS = [ROOT_SITEMAP_TXT, DOCS_SITEMAP_TXT]

    @classmethod
    def setUpClass(cls):
        cls.contents = {path: _read(path) for path in cls.SITEMAP_PATHS}

    def test_sitemap_files_exist(self):
        for path in self.SITEMAP_PATHS:
            with self.subTest(path=path):
                self.assertTrue(os.path.isfile(path))

    def test_gh_urls_present_in_both_copies(self):
        for path, content in self.contents.items():
            for url in [GH_REVIEW_URL, GH_LEGAL_URL]:
                with self.subTest(path=path, url=url):
                    self.assertIn(url, content)

    def test_gb_urls_present_in_both_copies(self):
        for path, content in self.contents.items():
            for url in [GB_REVIEW_URL, GB_LEGAL_URL]:
                with self.subTest(path=path, url=url):
                    self.assertIn(url, content)

    def test_root_and_docs_copies_are_identical(self):
        self.assertEqual(
            self.contents[ROOT_SITEMAP_TXT], self.contents[DOCS_SITEMAP_TXT]
        )

    def test_each_new_url_appears_exactly_once_per_copy(self):
        for path, content in self.contents.items():
            for url in [GH_REVIEW_URL, GH_LEGAL_URL, GB_REVIEW_URL, GB_LEGAL_URL]:
                with self.subTest(path=path, url=url):
                    self.assertEqual(content.count(url), 1)

    def test_new_gh_urls_ordered_after_homepage_and_before_hybrid_onprem(self):
        for path, content in self.contents.items():
            with self.subTest(path=path):
                homepage_idx = content.index(GH_BASE)
                review_idx = content.index(GH_REVIEW_URL)
                legal_idx = content.index(GH_LEGAL_URL)
                hybrid_idx = content.index(GH_HYBRID_ONPREM_URL)
                self.assertLess(homepage_idx, review_idx)
                self.assertLess(review_idx, legal_idx)
                self.assertLess(legal_idx, hybrid_idx)

    def test_all_new_urls_are_well_formed_https(self):
        for url in [GH_REVIEW_URL, GH_LEGAL_URL, GB_REVIEW_URL, GB_LEGAL_URL]:
            with self.subTest(url=url):
                self.assertTrue(url.startswith("https://"))
                self.assertNotIn("//", url[8:])


class SitemapXmlNewPageEntriesTestCase(unittest.TestCase):
    """Tests for the new <url> nodes added to sitemap.xml / docs/sitemap.xml
    for the Strategic Review and Legal Notice pages."""

    XML_PATHS = [ROOT_SITEMAP_XML, DOCS_SITEMAP_XML]

    @classmethod
    def setUpClass(cls):
        cls.raw_contents = {path: _read(path) for path in cls.XML_PATHS}
        cls.trees = {path: ET.parse(path) for path in cls.XML_PATHS}

    def test_xml_files_exist(self):
        for path in self.XML_PATHS:
            with self.subTest(path=path):
                self.assertTrue(os.path.isfile(path))

    def test_xml_parses_without_error(self):
        for path in self.XML_PATHS:
            with self.subTest(path=path):
                try:
                    ET.parse(path)
                except ET.ParseError as e:
                    self.fail(f"{path} is not valid XML: {e}")

    def _find_url_node(self, path, loc_value):
        root = self.trees[path].getroot()
        for u in root.findall(f"{SITEMAP_NS}url"):
            loc = u.find(f"{SITEMAP_NS}loc")
            if loc is not None and loc.text == loc_value:
                return u
        return None

    def test_each_new_url_node_present_exactly_once_per_copy(self):
        for path in self.XML_PATHS:
            root = self.trees[path].getroot()
            for url in [GH_REVIEW_URL, GH_LEGAL_URL]:
                with self.subTest(path=path, url=url):
                    matches = [
                        u
                        for u in root.findall(f"{SITEMAP_NS}url")
                        if u.find(f"{SITEMAP_NS}loc") is not None
                        and u.find(f"{SITEMAP_NS}loc").text == url
                    ]
                    self.assertEqual(len(matches), 1)

    def test_new_url_nodes_have_expected_priority_and_changefreq(self):
        for path in self.XML_PATHS:
            for url in [GH_REVIEW_URL, GH_LEGAL_URL]:
                with self.subTest(path=path, url=url):
                    node = self._find_url_node(path, url)
                    self.assertIsNotNone(node)

                    lastmod = node.find(f"{SITEMAP_NS}lastmod")
                    changefreq = node.find(f"{SITEMAP_NS}changefreq")
                    priority = node.find(f"{SITEMAP_NS}priority")

                    self.assertIsNotNone(lastmod)
                    self.assertIsNotNone(changefreq)
                    self.assertIsNotNone(priority)

                    self.assertRegex(lastmod.text, r"^\d{4}-\d{2}-\d{2}$")
                    self.assertEqual(changefreq.text, "weekly")
                    # Top-level documentation pages get a higher priority
                    # (0.8) than nested engineering/executive pages (0.6).
                    self.assertEqual(priority.text, "0.8")

    def test_new_url_nodes_appear_between_homepage_and_hybrid_onprem(self):
        for path in self.XML_PATHS:
            with self.subTest(path=path):
                root = self.trees[path].getroot()
                locs = [
                    u.find(f"{SITEMAP_NS}loc").text
                    for u in root.findall(f"{SITEMAP_NS}url")
                    if u.find(f"{SITEMAP_NS}loc") is not None
                ]
                homepage_idx = locs.index(GH_BASE)
                review_idx = locs.index(GH_REVIEW_URL)
                legal_idx = locs.index(GH_LEGAL_URL)
                hybrid_idx = locs.index(GH_HYBRID_ONPREM_URL)
                self.assertLess(homepage_idx, review_idx)
                self.assertLess(review_idx, legal_idx)
                self.assertLess(legal_idx, hybrid_idx)

    def test_root_and_docs_xml_copies_are_identical(self):
        self.assertEqual(
            self.raw_contents[ROOT_SITEMAP_XML], self.raw_contents[DOCS_SITEMAP_XML]
        )

    def test_new_pages_have_higher_priority_than_nested_pages(self):
        for path in self.XML_PATHS:
            with self.subTest(path=path):
                review_node = self._find_url_node(path, GH_REVIEW_URL)
                hybrid_node = self._find_url_node(path, GH_HYBRID_ONPREM_URL)
                review_priority = float(review_node.find(f"{SITEMAP_NS}priority").text)
                hybrid_priority = float(hybrid_node.find(f"{SITEMAP_NS}priority").text)
                self.assertGreater(review_priority, hybrid_priority)


class CrossFileReviewAndLegalReferenceConsistencyTestCase(unittest.TestCase):
    """Verifies the slugs used for aws-vs-self-hosted-review and
    legal-notice are consistent across docs/index.md, llms.txt, and the
    sitemap files."""

    @classmethod
    def setUpClass(cls):
        cls.index_content = _read(INDEX_PATH)
        cls.llms_content = _read(LLMS_PATH)
        cls.sitemap_txt_content = _read(ROOT_SITEMAP_TXT)

    def test_html_slugs_used_in_index(self):
        for slug in ["aws-vs-self-hosted-review", "legal-notice"]:
            with self.subTest(slug=slug):
                self.assertIn(f"]({slug}.html)", self.index_content)

    def test_html_slugs_used_in_sitemap_txt(self):
        for url in [GH_REVIEW_URL, GH_LEGAL_URL]:
            with self.subTest(url=url):
                self.assertIn(url, self.sitemap_txt_content)

    def test_markdown_paths_consistent_between_llms_txt_and_filesystem(self):
        for slug, expected_path in [
            ("aws-vs-self-hosted-review", REVIEW_MD_PATH),
            ("legal-notice", LEGAL_MD_PATH),
        ]:
            with self.subTest(slug=slug):
                match = re.search(
                    r"\((docs/" + re.escape(slug) + r"\.md)\)",
                    self.llms_content,
                )
                self.assertIsNotNone(match)
                referenced_path = os.path.join(REPO_ROOT, match.group(1))
                self.assertTrue(os.path.isfile(referenced_path))
                self.assertEqual(
                    os.path.normpath(referenced_path), expected_path
                )

    def test_new_index_links_appear_after_aws_vs_onprem_and_before_prerequisites(self):
        aws_vs_onprem_idx = self.index_content.index(
            "engineering/aws-vs-onprem-comparison.html"
        )
        review_idx = self.index_content.index("aws-vs-self-hosted-review.html")
        legal_idx = self.index_content.index("legal-notice.html")
        prerequisites_idx = self.index_content.index("## Prerequisites")
        self.assertLess(aws_vs_onprem_idx, review_idx)
        self.assertLess(review_idx, legal_idx)
        self.assertLess(legal_idx, prerequisites_idx)

    def test_new_llms_entries_appear_after_github_detach_fork_and_before_automation_scripts(self):
        github_detach_idx = self.llms_content.index("github-detach-fork.md")
        review_idx = self.llms_content.index("aws-vs-self-hosted-review.md")
        legal_idx = self.llms_content.index("legal-notice.md")
        scripts_idx = self.llms_content.index("Automation Scripts Portal")
        self.assertLess(github_detach_idx, review_idx)
        self.assertLess(review_idx, legal_idx)
        self.assertLess(legal_idx, scripts_idx)

    def test_each_new_page_referenced_exactly_once_in_index(self):
        for anchor in [
            "(aws-vs-self-hosted-review.html)",
            "(legal-notice.html)",
        ]:
            with self.subTest(anchor=anchor):
                self.assertEqual(self.index_content.count(anchor), 1)


if __name__ == "__main__":
    unittest.main()
