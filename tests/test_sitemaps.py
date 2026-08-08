#!/usr/bin/env python3
import os
import sys
import unittest
import xml.etree.ElementTree as ET

# Insert scripts folder in path to allow import
SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import generate_sitemaps

class TestSitemapsAndSEO(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.docs_dir = os.path.join(self.repo_root, "docs")

        # Ensure the generation script runs so files exist for integration testing
        generate_sitemaps.main()

    def test_file_existence(self):
        # Assert files exist in root
        self.assertTrue(os.path.exists(os.path.join(self.repo_root, "sitemap.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.repo_root, "sitemap.xml")))
        self.assertTrue(os.path.exists(os.path.join(self.repo_root, "robots.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.repo_root, ".well-known", "security.txt")))

        # Assert files exist in docs/
        self.assertTrue(os.path.exists(os.path.join(self.docs_dir, "sitemap.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.docs_dir, "sitemap.xml")))
        self.assertTrue(os.path.exists(os.path.join(self.docs_dir, "robots.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.docs_dir, ".well-known", "security.txt")))

    def test_sitemap_txt_structure_and_no_broken_links(self):
        sitemap_txt_path = os.path.join(self.repo_root, "sitemap.txt")
        with open(sitemap_txt_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        # Ensure we have URLs
        self.assertGreater(len(lines), 0)

        gh_count = 0
        gb_count = 0

        for url in lines:
            # All URLs must be well-formed HTTPS links
            self.assertTrue(url.startswith("https://"))

            # Check for no double-slashes in the path
            # (only "https://" is allowed to have double-slashes)
            path_part = url[8:]
            self.assertNotIn("//", path_part, f"Malformed URL contains double-slashes: {url}")

            if "github.io" in url:
                gh_count += 1
            elif "gitbook.io" in url:
                gb_count += 1

        # Assert both GitHub Pages and GitBook domains are populated
        self.assertGreater(gh_count, 0, "No GitHub Pages URLs found in sitemap.txt")
        self.assertGreater(gb_count, 0, "No GitBook URLs found in sitemap.txt")

    def test_sitemap_xml_schema_and_contents(self):
        sitemap_xml_path = os.path.join(self.repo_root, "sitemap.xml")

        # Parse XML to ensure it's valid syntax
        try:
            tree = ET.parse(sitemap_xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            self.fail(f"sitemap.xml is not valid XML: {e}")

        # XML Namespace assertion
        self.assertEqual(root.tag, "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")

        # Check kids
        urls = root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")
        self.assertGreater(len(urls), 0, "sitemap.xml has no <url> tags")

        for u in urls:
            loc = u.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            lastmod = u.find("{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod")
            changefreq = u.find("{http://www.sitemaps.org/schemas/sitemap/0.9}changefreq")
            priority = u.find("{http://www.sitemaps.org/schemas/sitemap/0.9}priority")

            self.assertIsNotNone(loc, "Missing <loc> in sitemap.xml url node")
            self.assertIsNotNone(lastmod, "Missing <lastmod> in sitemap.xml url node")
            self.assertIsNotNone(changefreq, "Missing <changefreq> in sitemap.xml url node")
            self.assertIsNotNone(priority, "Missing <priority> in sitemap.xml url node")

            # The loc must belong to github.io domain only
            url_val = loc.text
            self.assertTrue(url_val.startswith("https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"))

            # Change frequency must be standard values
            self.assertIn(changefreq.text, ["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"])

            # Priority must be between 0.0 and 1.0
            p_val = float(priority.text)
            self.assertTrue(0.0 <= p_val <= 1.0)

    def test_robots_txt_content(self):
        robots_txt_path = os.path.join(self.repo_root, "robots.txt")
        with open(robots_txt_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("User-agent: *", content)
        self.assertIn("Allow: /", content)
        self.assertIn("Sitemap: https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/sitemap.xml", content)

    def test_security_txt_content(self):
        security_txt_path = os.path.join(self.repo_root, ".well-known", "security.txt")
        with open(security_txt_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Contact: mailto:contact@linuxmalaysia.com", content)
        self.assertIn("Preferred-Languages:", content)
        self.assertIn("Canonical: https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/.well-known/security.txt", content)

if __name__ == "__main__":
    unittest.main()
