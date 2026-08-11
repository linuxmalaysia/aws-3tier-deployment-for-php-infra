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


if __name__ == "__main__":
    unittest.main()
