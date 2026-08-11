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

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def _read(path):
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
        self.assertEqual(fm["timestamp"], "2026-08-11T12:00:00+08:00")

        # Assert timestamp exists and uses the required quoted representation in the raw file
        raw_lines = parts[1].splitlines()
        timestamp_line = [l.strip() for l in raw_lines if l.strip().startswith("timestamp:")]
        self.assertTrue(len(timestamp_line) > 0)
        self.assertEqual(timestamp_line[0], 'timestamp: "2026-08-11T12:00:00+08:00"')

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
        self.assertEqual(fm["timestamp"], "2026-08-11T12:00:00+08:00")

        # Assert timestamp exists and uses the required quoted representation in the raw file
        raw_lines = parts[1].splitlines()
        timestamp_line = [l.strip() for l in raw_lines if l.strip().startswith("timestamp:")]
        self.assertTrue(len(timestamp_line) > 0)
        self.assertEqual(timestamp_line[0], 'timestamp: "2026-08-11T12:00:00+08:00"')

    def test_legal_notice_sections(self):
        content = _read(LEGAL_MD_PATH)
        self.assertIn("1. Educational and Training Purpose", content)
        self.assertIn("2. Reliance on Critical Assumptions", content)
        self.assertIn("3. Privacy Statement & Data Protection", content)
        self.assertIn("4. Assumption of Risk & Liability Disclaimer", content)
        self.assertIn("based entirely on assumptions", content)
        self.assertIn("strictly for training, educational, and planning proposal purposes", content)
        self.assertIn("Use of this project, its code, and its documents is at your own risk", content)
        self.assertIn("Under no circumstances shall the project contributors", content)
        self.assertIn("Reasonable efforts have been made to ensure that all references", content)

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

    def test_sitemap_publication(self):
        sitemaps_txt = [
            os.path.join(REPO_ROOT, "sitemap.txt"),
            os.path.join(REPO_ROOT, "docs", "sitemap.txt")
        ]
        sitemaps_xml = [
            os.path.join(REPO_ROOT, "sitemap.xml"),
            os.path.join(REPO_ROOT, "docs", "sitemap.xml")
        ]

        expected_txt_urls = [
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/aws-vs-self-hosted-review.html",
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/legal-notice.html",
            "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/aws-vs-self-hosted-review",
            "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/legal-notice"
        ]

        expected_xml_urls = [
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/aws-vs-self-hosted-review.html",
            "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/legal-notice.html"
        ]

        for s_path in sitemaps_txt:
            content = _read(s_path)
            for url in expected_txt_urls:
                self.assertEqual(content.count(url), 1, f"URL {url} count is not 1 in {s_path}")

        import datetime
        for s_path in sitemaps_xml:
            content = _read(s_path)
            for url in expected_xml_urls:
                loc_tag = f"<loc>{url}</loc>"
                self.assertEqual(content.count(loc_tag), 1, f"XML tag {loc_tag} count is not 1 in {s_path}")

            # Parse XML and validate lastmod format and values
            tree = ET.parse(s_path)
            root = tree.getroot()
            for url in expected_xml_urls:
                url_node = None
                for u in root.findall(f"{SITEMAP_NS}url"):
                    loc = u.find(f"{SITEMAP_NS}loc")
                    if loc is not None and loc.text == url:
                        url_node = u
                        break
                self.assertIsNotNone(url_node, f"URL {url} node not found in {s_path}")
                lastmod = url_node.find(f"{SITEMAP_NS}lastmod").text
                # Retain the YYYY-MM-DD format check via assertRegex
                self.assertRegex(lastmod, r"^\d{4}-\d{2}-\d{2}$")
                # Parse with datetime.date.fromisoformat(), causing impossible calendar dates to fail
                try:
                    datetime.date.fromisoformat(lastmod)
                except ValueError as e:
                    self.fail(f"Invalid lastmod date {lastmod} in {s_path}: {e}")


if __name__ == "__main__":
    unittest.main()
