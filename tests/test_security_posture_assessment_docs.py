#!/usr/bin/env python3
"""Unit tests for the "Security Posture Assessment (SPA) Requirement
Checklist" documentation added in this PR.

This PR introduces a new documentation page
(``docs/engineering/security-posture-assessment.md``) and wires it up from
several other files:

* ``docs/index.md``   -- adds a numbered bullet link pointing at
  ``engineering/security-posture-assessment.html``.
* ``llms.txt``        -- adds an AI-agent index entry pointing at
  ``docs/engineering/security-posture-assessment.md``.
* ``sitemap.txt`` / ``docs/sitemap.txt``   -- adds GitHub Pages and GitBook
  URLs for the new page.
* ``sitemap.xml`` / ``docs/sitemap.xml``   -- adds a ``<url>`` entry for the
  new page.

These files are treated as plain text/XML (rather than requiring a live
Jekyll build) to stay dependency free, following the pattern already used by
``tests/test_production_costing_docs.py`` and ``tests/test_sitemaps.py``.
The tests pin down the exact cross-references between the changed files and
validate the internal structural consistency of the new SPA checklist
content.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_security_posture_assessment_docs
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

import prepare_docs  # noqa: E402  (import after sys.path manipulation)

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
SPA_MD_PATH = os.path.join(
    REPO_ROOT, "docs", "engineering", "security-posture-assessment.md"
)
ROOT_SITEMAP_TXT = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_TXT = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_XML = os.path.join(REPO_ROOT, "sitemap.xml")
DOCS_SITEMAP_XML = os.path.join(REPO_ROOT, "docs", "sitemap.xml")
ROOT_SECURITY_TXT = os.path.join(REPO_ROOT, ".well-known", "security.txt")

GH_URL = (
    "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
    "engineering/security-posture-assessment.html"
)
GB_URL = (
    "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/"
    "docs/engineering/security-posture-assessment"
)
JUMPHOST_GH_URL = (
    "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
    "engineering/jumphost.html"
)
SCRIPTS_GH_URL = (
    "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
    "engineering/scripts.html"
)
JUMPHOST_GB_URL = (
    "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/"
    "docs/engineering/jumphost"
)
SCRIPTS_GB_URL = (
    "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/"
    "docs/engineering/scripts"
)

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

AUDIT_IDS = [
    "NET-01", "NET-02", "NET-03", "NET-04",
    "SG-01", "SG-02", "SG-03", "SG-04",
    "HST-01", "HST-02", "HST-03", "HST-04",
    "APP-01", "APP-02", "APP-03", "APP-04",
    "DAT-01", "DAT-02", "DAT-03", "DAT-04",
    "MON-01", "MON-02", "MON-03", "MON-04",
]

TIER_HEADINGS = [
    "### Tier 1: Perimeter & Edge Network Security",
    "### Tier 2: Microsegmentation & Security Groups",
    "### Tier 3: Host Hardening & OS Configuration",
    "### Tier 4: Application & Runtime Security (Nginx + PHP-FPM)",
    "### Tier 5: Data Security, Encryption & Privacy Compliance",
    "### Tier 6: Monitoring, Auditability & Incident Response",
]


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class SecurityPostureAssessmentMarkdownFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of
    docs/engineering/security-posture-assessment.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(SPA_MD_PATH)
        stripped = cls.content.lstrip()
        parts = stripped.split("---", 2)
        # parts[0] is empty (before first ---), parts[1] is the front matter body.
        cls.front_matter_text = parts[1]
        cls.body_text = parts[2]
        cls.front_matter = prepare_docs.parse_yaml_front_matter(cls.front_matter_text)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(SPA_MD_PATH))

    def test_starts_with_front_matter_delimiter(self):
        self.assertTrue(self.content.startswith("---\n"))

    def test_required_okf_fields_present(self):
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_okf_version_is_expected_value(self):
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_layout_is_default(self):
        self.assertEqual(self.front_matter["layout"], "default")

    def test_title_field_value(self):
        self.assertEqual(
            self.front_matter["title"],
            "Security Posture Assessment (SPA) Requirement Checklist",
        )

    def test_type_matches_prepare_docs_inference(self):
        """docs/*.md files that aren't index.md or under docs/modules are
        inferred as 'Technical Reference Guide' by prepare_docs.py; the
        front matter of the new doc should match that convention."""
        inferred_type = prepare_docs.infer_okf_type(
            "docs/engineering/security-posture-assessment.md"
        )
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_is_a_list_of_strings(self):
        topics = self.front_matter["topics"]
        self.assertIsInstance(topics, list)
        self.assertTrue(all(isinstance(t, str) for t in topics))

    def test_topics_match_authored_values_exactly(self):
        self.assertEqual(
            self.front_matter["topics"],
            ["security", "compliance", "assessment", "aws", "malaysia"],
        )

    def test_topics_have_no_duplicates(self):
        topics = self.front_matter["topics"]
        self.assertEqual(len(topics), len(set(topics)))

    def test_infer_okf_topics_baseline_when_no_existing_topics(self):
        """Regression/boundary check: unlike many other docs in this repo,
        this file's path contains no recognized keyword (vpc, rds, php,
        etc.), so if the manually-authored topics were ever stripped,
        prepare_docs.infer_okf_topics would fall back to the bare
        ["aws", "3-tier"] baseline -- notably *without* "3-tier" present in
        the manually-curated topics list actually shipped in this file."""
        inferred = prepare_docs.infer_okf_topics(
            "docs/engineering/security-posture-assessment.md"
        )
        self.assertEqual(inferred, ["aws", "3-tier"])
        self.assertNotIn("3-tier", self.front_matter["topics"])

    def test_timestamp_matches_iso8601_with_offset(self):
        self.assertRegex(
            self.front_matter["timestamp"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$",
        )

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        heading_text = heading_match.group(1).strip()
        self.assertEqual(heading_text, self.front_matter["title"])


class SecurityPostureAssessmentContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of
    docs/engineering/security-posture-assessment.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(SPA_MD_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn(
            "# Security Posture Assessment (SPA) Requirement Checklist",
            self.content,
        )

    def test_contains_executive_summary_section(self):
        self.assertIn("## 1. Executive Security Blueprint Summary", self.content)

    def test_contains_checklist_section(self):
        self.assertIn("## 2. SPA Requirement Checklist", self.content)

    def test_contains_sla_timeline_section(self):
        self.assertIn("## 3. Vulnerability Remediation & SLA Timeline", self.content)

    def test_contains_signoff_section(self):
        self.assertIn("## 4. SPA Sign-Off and Verification Statement", self.content)

    def test_top_level_sections_appear_in_ascending_order(self):
        headings = [
            "## 1. Executive Security Blueprint Summary",
            "## 2. SPA Requirement Checklist",
            "## 3. Vulnerability Remediation & SLA Timeline",
            "## 4. SPA Sign-Off and Verification Statement",
        ]
        indices = [self.content.index(h) for h in headings]
        self.assertEqual(indices, sorted(indices))

    def test_all_six_tier_headings_present(self):
        for heading in TIER_HEADINGS:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)

    def test_tier_headings_appear_in_ascending_order(self):
        indices = [self.content.index(h) for h in TIER_HEADINGS]
        self.assertEqual(indices, sorted(indices))

    def test_tier_headings_appear_between_checklist_and_sla_sections(self):
        checklist_idx = self.content.index("## 2. SPA Requirement Checklist")
        sla_idx = self.content.index("## 3. Vulnerability Remediation & SLA Timeline")
        for heading in TIER_HEADINGS:
            tier_idx = self.content.index(heading)
            self.assertLess(checklist_idx, tier_idx)
            self.assertLess(tier_idx, sla_idx)

    def test_primary_region_is_stated(self):
        self.assertIn("ap-southeast-5", self.content)

    def test_mentions_pdpa_compliance(self):
        self.assertIn(
            "Malaysian Personal Data Protection Act (PDPA)", self.content
        )

    def test_no_stray_todo_or_placeholder_markers(self):
        for marker in ["TODO", "FIXME", "TBD", "XXX"]:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.content)


class SecurityPostureAssessmentChecklistTableTestCase(unittest.TestCase):
    """Tests for the Section 2 SPA Requirement Checklist tables."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(SPA_MD_PATH)
        cls.tier_sections = re.split(r"### Tier \d+: ", cls.content)[1:]

    def test_exactly_six_tier_sections(self):
        self.assertEqual(len(self.tier_sections), 6)

    def test_audit_id_count_and_values(self):
        matches = re.findall(r"\|\s*\*\*([A-Z]+-\d{2})\*\*\s*\|", self.content)
        self.assertEqual(matches, AUDIT_IDS)

    def test_audit_ids_are_unique(self):
        matches = re.findall(r"\|\s*\*\*([A-Z]+-\d{2})\*\*\s*\|", self.content)
        self.assertEqual(len(matches), len(set(matches)))

    def test_each_tier_has_exactly_four_data_rows(self):
        for i, section in enumerate(self.tier_sections, start=1):
            # Stop at the next "---" horizontal rule which separates tiers.
            body = section.split("\n---", 1)[0]
            data_rows = re.findall(r"^\|\s*\*\*[A-Z]+-\d{2}\*\*\s*\|", body, re.MULTILINE)
            with self.subTest(tier=i):
                self.assertEqual(len(data_rows), 4)

    def test_each_tier_has_header_and_separator_row(self):
        for i, section in enumerate(self.tier_sections, start=1):
            body = section.split("\n---", 1)[0]
            with self.subTest(tier=i):
                self.assertIn(
                    "| Audit ID | Security Control Area | Detailed Requirement "
                    "Specification | Implementation Status | Verification Method |",
                    body,
                )
                self.assertIn("| :--- | :--- | :--- | :--- | :--- |", body)

    def test_all_implementation_statuses_fully_implemented(self):
        self.assertEqual(
            self.content.count("✅ Fully Implemented"), len(AUDIT_IDS)
        )

    def test_no_incomplete_or_failed_status_markers(self):
        for marker in ["❌", "⚠️", "Partial", "Not Implemented", "In Progress"]:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.content)

    def test_mon03_references_well_known_security_txt(self):
        self.assertIn(
            "`.well-known/security.txt`", self.content
        )


class SecurityPostureAssessmentSlaTimelineTestCase(unittest.TestCase):
    """Tests for the Section 3 Vulnerability Remediation & SLA Timeline."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(SPA_MD_PATH)
        section_match = re.search(
            r"## 3\. Vulnerability Remediation & SLA Timeline\n(.*?)\n---",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None
        cls.section = section_match.group(1)

    def test_all_four_severity_bullets_present(self):
        expected = [
            "* **Critical Vulnerabilities (CVSS v3 9.0 - 10.0):** Remediation "
            "required within **24 Hours**.",
            "* **High Vulnerabilities (CVSS v3 7.0 - 8.9):** Remediation "
            "required within **7 Days**.",
            "* **Medium Vulnerabilities (CVSS v3 4.0 - 6.9):** Remediation "
            "required within **30 Days**.",
            "* **Low Vulnerabilities (CVSS v3 0.1 - 3.9):** Remediation "
            "required within **90 Days**.",
        ]
        for bullet in expected:
            with self.subTest(bullet=bullet):
                self.assertIn(bullet, self.section)

    def test_severity_bullets_appear_in_descending_severity_order(self):
        order = ["Critical", "High", "Medium", "Low"]
        indices = [self.section.index(f"**{sev} Vulnerabilities") for sev in order]
        self.assertEqual(indices, sorted(indices))

    def test_cvss_ranges_are_contiguous_and_cover_0_to_10(self):
        ranges = re.findall(r"CVSS v3 ([\d.]+) - ([\d.]+)", self.section)
        self.assertEqual(len(ranges), 4)
        # Ordered Critical -> High -> Medium -> Low; low bound of one tier
        # should immediately precede the high bound of the next lower tier.
        numeric_ranges = [(float(lo), float(hi)) for lo, hi in ranges]
        self.assertEqual(numeric_ranges[0], (9.0, 10.0))
        self.assertEqual(numeric_ranges[1], (7.0, 8.9))
        self.assertEqual(numeric_ranges[2], (4.0, 6.9))
        self.assertEqual(numeric_ranges[3], (0.1, 3.9))

    def test_remediation_windows_increase_as_severity_decreases(self):
        """Regression: remediation SLA time budgets must strictly increase
        (in hours) as severity decreases from Critical to Low."""

        def _to_hours(value, unit):
            value = float(value)
            return value * 24 if unit.lower().startswith("day") else value

        matches = re.findall(
            r"Remediation required within \*\*(\d+) (Hour|Day)s?\*\*", self.section
        )
        self.assertEqual(len(matches), 4)
        hours = [_to_hours(v, u) for v, u in matches]
        self.assertEqual(hours, [24, 168, 720, 2160])
        self.assertEqual(hours, sorted(hours))


class SecurityPostureAssessmentSecurityTxtCrossReferenceTestCase(unittest.TestCase):
    """Verifies the MON-03 checklist row references the same canonical
    security.txt URL that is actually published at the repository root."""

    @classmethod
    def setUpClass(cls):
        cls.spa_content = _read(SPA_MD_PATH)
        cls.security_txt_content = _read(ROOT_SECURITY_TXT)

    def test_security_txt_file_exists(self):
        self.assertTrue(os.path.isfile(ROOT_SECURITY_TXT))

    def test_mon03_url_matches_security_txt_canonical(self):
        mon03_match = re.search(
            r"\*\*MON-03\*\*.*?Query `(https://\S+/\.well-known/security\.txt)`",
            self.spa_content,
        )
        self.assertIsNotNone(mon03_match, "Could not locate MON-03 verification URL")
        mon03_url = mon03_match.group(1)

        canonical_match = re.search(r"Canonical:\s*(\S+)", self.security_txt_content)
        self.assertIsNotNone(canonical_match)
        self.assertEqual(mon03_url, canonical_match.group(1))


class IndexMdSecurityPostureAssessmentLinkTestCase(unittest.TestCase):
    """Tests for the new link added to docs/index.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)

    def test_index_file_exists(self):
        self.assertTrue(os.path.isfile(INDEX_PATH))

    def test_link_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\*\*\[Security Posture Assessment \(SPA\) Checklist\]"
                r"\(engineering/security-posture-assessment\.html\):\*\*"
                r"\s*Comprehensive security controls audit checklist, "
                r"governance roadmap, and SLA timeline\."
            ),
        )

    def test_link_is_numbered_twelve(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"^12\. \*\*\[Security Posture Assessment \(SPA\) Checklist\]",
                re.MULTILINE,
            ),
        )

    def test_link_appears_after_codeigniter_link(self):
        codeigniter_idx = self.content.index(
            "[CodeIgniter Deployment Guide](engineering/codeigniter-php-fpm.html)"
        )
        spa_idx = self.content.index(
            "[Security Posture Assessment (SPA) Checklist]"
            "(engineering/security-posture-assessment.html)"
        )
        self.assertLess(codeigniter_idx, spa_idx)

    def test_link_appears_in_engineering_devops_section(self):
        section_match = re.search(
            r"### Engineering & DevOps Implementation Guides\n(.*?)(?=\n### |\n---|\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[Security Posture Assessment (SPA) Checklist]"
            "(engineering/security-posture-assessment.html)",
            section_match.group(1),
        )

    def test_link_uses_relative_html_url_not_markdown_extension(self):
        self.assertIn("(engineering/security-posture-assessment.html)", self.content)
        self.assertNotIn("(engineering/security-posture-assessment.md)", self.content)

    def test_link_target_file_exists(self):
        self.assertTrue(os.path.isfile(SPA_MD_PATH))

    def test_link_appears_exactly_once(self):
        self.assertEqual(
            self.content.count("[Security Posture Assessment (SPA) Checklist]"), 1
        )


class LlmsTxtSecurityPostureAssessmentEntryTestCase(unittest.TestCase):
    """Tests for the new entry added to llms.txt."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LLMS_PATH)

    def test_llms_txt_file_exists(self):
        self.assertTrue(os.path.isfile(LLMS_PATH))

    def test_entry_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\[Security Posture Assessment\]"
                r"\(docs/engineering/security-posture-assessment\.md\)\s*:"
                r"\s*Comprehensive Security Posture Assessment \(SPA\) "
                r"requirement checklist, governance roadmap, and SLA "
                r"remediation timelines for ap-southeast-5\."
            ),
        )

    def test_entry_under_engineering_architectural_section(self):
        section_match = re.search(
            r"## Core Architectural Documentation \(Engineering\)\n(.*?)(?=\n## |\Z)",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertIn(
            "[Security Posture Assessment]"
            "(docs/engineering/security-posture-assessment.md)",
            section_match.group(1),
        )

    def test_entry_appears_directly_after_codeigniter_entry(self):
        codeigniter_idx = self.content.index(
            "[CodeIgniter Deployment Guide](docs/engineering/codeigniter-php-fpm.md)"
        )
        spa_idx = self.content.index(
            "[Security Posture Assessment]"
            "(docs/engineering/security-posture-assessment.md)"
        )
        self.assertLess(codeigniter_idx, spa_idx)
        between = self.content[codeigniter_idx:spa_idx]
        self.assertEqual(between.count("\n"), 1)
        self.assertNotIn("\n- [", between.strip("\n"))

    def test_entry_target_file_exists(self):
        self.assertTrue(os.path.isfile(SPA_MD_PATH))

    def test_entry_follows_bullet_link_colon_description_format(self):
        match = re.search(
            r"^- \[Security Posture Assessment\]"
            r"\(docs/engineering/security-posture-assessment\.md\) : .+$",
            self.content,
            re.MULTILINE,
        )
        self.assertIsNotNone(
            match, "Entry does not follow the '- [Title](path) : description' format"
        )

    def test_entry_appears_exactly_once(self):
        self.assertEqual(
            self.content.count("[Security Posture Assessment]"), 1
        )


class CrossFileReferenceConsistencyTestCase(unittest.TestCase):
    """Verifies the slug used for security-posture-assessment is consistent
    across docs/index.md, llms.txt, and the sitemap files."""

    @classmethod
    def setUpClass(cls):
        cls.index_content = _read(INDEX_PATH)
        cls.llms_content = _read(LLMS_PATH)
        cls.sitemap_txt_content = _read(ROOT_SITEMAP_TXT)

    def test_html_slug_used_in_index(self):
        self.assertIn(
            "(engineering/security-posture-assessment.html)", self.index_content
        )

    def test_html_slug_used_in_sitemap_txt(self):
        self.assertIn(GH_URL, self.sitemap_txt_content)

    def test_markdown_path_consistent_between_llms_txt_and_filesystem(self):
        match = re.search(
            r"\[Security Posture Assessment\]"
            r"\((docs/engineering/security-posture-assessment\.md)\)",
            self.llms_content,
        )
        self.assertIsNotNone(match)
        referenced_path = os.path.join(REPO_ROOT, match.group(1))
        self.assertTrue(os.path.isfile(referenced_path))
        self.assertEqual(os.path.normpath(referenced_path), SPA_MD_PATH)


class SitemapTxtSecurityPostureAssessmentEntryTestCase(unittest.TestCase):
    """Tests for the new URLs added to sitemap.txt and docs/sitemap.txt."""

    SITEMAP_PATHS = [ROOT_SITEMAP_TXT, DOCS_SITEMAP_TXT]

    @classmethod
    def setUpClass(cls):
        cls.contents = {path: _read(path) for path in cls.SITEMAP_PATHS}

    def test_sitemap_files_exist(self):
        for path in self.SITEMAP_PATHS:
            with self.subTest(path=path):
                self.assertTrue(os.path.isfile(path))

    def test_gh_url_present_in_both_copies(self):
        for path, content in self.contents.items():
            with self.subTest(path=path):
                self.assertIn(GH_URL, content)

    def test_gb_url_present_in_both_copies(self):
        for path, content in self.contents.items():
            with self.subTest(path=path):
                self.assertIn(GB_URL, content)

    def test_root_and_docs_copies_are_identical(self):
        self.assertEqual(
            self.contents[ROOT_SITEMAP_TXT], self.contents[DOCS_SITEMAP_TXT]
        )

    def test_gh_url_appears_exactly_once_per_copy(self):
        for path, content in self.contents.items():
            with self.subTest(path=path):
                self.assertEqual(content.count(GH_URL), 1)

    def test_gb_url_appears_exactly_once_per_copy(self):
        for path, content in self.contents.items():
            with self.subTest(path=path):
                self.assertEqual(content.count(GB_URL), 1)

    def test_gh_url_appears_between_jumphost_and_scripts(self):
        for path, content in self.contents.items():
            with self.subTest(path=path):
                jumphost_idx = content.index(JUMPHOST_GH_URL)
                spa_idx = content.index(GH_URL)
                scripts_idx = content.index(SCRIPTS_GH_URL)
                self.assertLess(jumphost_idx, spa_idx)
                self.assertLess(spa_idx, scripts_idx)

    def test_gb_url_appears_between_jumphost_and_scripts(self):
        for path, content in self.contents.items():
            with self.subTest(path=path):
                jumphost_idx = content.index(JUMPHOST_GB_URL)
                spa_idx = content.index(GB_URL)
                scripts_idx = content.index(SCRIPTS_GB_URL)
                self.assertLess(jumphost_idx, spa_idx)
                self.assertLess(spa_idx, scripts_idx)

    def test_gh_url_is_well_formed(self):
        self.assertTrue(GH_URL.startswith("https://"))
        self.assertNotIn("//", GH_URL[8:])

    def test_gb_url_is_well_formed(self):
        self.assertTrue(GB_URL.startswith("https://"))
        self.assertNotIn("//", GB_URL[8:])


class SitemapXmlSecurityPostureAssessmentEntryTestCase(unittest.TestCase):
    """Tests for the new <url> entry added to sitemap.xml and
    docs/sitemap.xml."""

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

    def test_new_url_node_present_exactly_once_per_copy(self):
        for path in self.XML_PATHS:
            with self.subTest(path=path):
                root = self.trees[path].getroot()
                matches = [
                    u
                    for u in root.findall(f"{SITEMAP_NS}url")
                    if u.find(f"{SITEMAP_NS}loc") is not None
                    and u.find(f"{SITEMAP_NS}loc").text == GH_URL
                ]
                self.assertEqual(len(matches), 1)

    def test_new_url_node_has_expected_fields(self):
        for path in self.XML_PATHS:
            with self.subTest(path=path):
                node = self._find_url_node(path, GH_URL)
                self.assertIsNotNone(node)

                lastmod = node.find(f"{SITEMAP_NS}lastmod")
                changefreq = node.find(f"{SITEMAP_NS}changefreq")
                priority = node.find(f"{SITEMAP_NS}priority")

                self.assertIsNotNone(lastmod)
                self.assertIsNotNone(changefreq)
                self.assertIsNotNone(priority)

                self.assertRegex(lastmod.text, r"^\d{4}-\d{2}-\d{2}$")
                self.assertEqual(changefreq.text, "weekly")
                self.assertEqual(priority.text, "0.6")

    def test_new_url_node_appears_between_jumphost_and_scripts(self):
        for path in self.XML_PATHS:
            with self.subTest(path=path):
                root = self.trees[path].getroot()
                locs = [
                    u.find(f"{SITEMAP_NS}loc").text
                    for u in root.findall(f"{SITEMAP_NS}url")
                    if u.find(f"{SITEMAP_NS}loc") is not None
                ]
                jumphost_idx = locs.index(JUMPHOST_GH_URL)
                spa_idx = locs.index(GH_URL)
                scripts_idx = locs.index(SCRIPTS_GH_URL)
                self.assertLess(jumphost_idx, spa_idx)
                self.assertLess(spa_idx, scripts_idx)

    def test_root_and_docs_xml_copies_are_identical(self):
        self.assertEqual(
            self.raw_contents[ROOT_SITEMAP_XML], self.raw_contents[DOCS_SITEMAP_XML]
        )


class SecurityPostureAssessmentScopeTargetChecklistTestCase(unittest.TestCase):
    """Tests for the new "Assessment Scope & Target Checklist (SPA Target
    System Format)" table added to Section 2 of
    docs/engineering/security-posture-assessment.md."""

    SCOPE_ROWS = [
        (1, "Internal Penetration Test"),
        (2, "External Penetration Test"),
        (3, "Web Application Security Assessment"),
        (4, "Host Vulnerability Assessment"),
        (5, "Database Security Assessment"),
        (6, "Network Device Assessment"),
    ]

    @classmethod
    def setUpClass(cls):
        cls.content = _read(SPA_MD_PATH)
        section_match = re.search(
            r"### Assessment Scope & Target Checklist \(SPA Target System "
            r"Format\)\n(.*?)\n---",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None, (
            "Could not locate the Assessment Scope & Target Checklist table"
        )
        cls.section = section_match.group(1)

    def test_section_heading_present(self):
        self.assertIn(
            "### Assessment Scope & Target Checklist (SPA Target System Format)",
            self.content,
        )

    def test_heading_appears_between_checklist_intro_and_tier_1(self):
        checklist_idx = self.content.index("## 2. SPA Requirement Checklist")
        scope_idx = self.content.index(
            "### Assessment Scope & Target Checklist (SPA Target System Format)"
        )
        tier1_idx = self.content.index(
            "### Tier 1: Perimeter & Edge Network Security"
        )
        self.assertLess(checklist_idx, scope_idx)
        self.assertLess(scope_idx, tier1_idx)

    def test_table_header_row_present(self):
        self.assertIn(
            "| No. | Scope | Description | Information Required (Answer) |",
            self.section,
        )

    def test_table_separator_row_present(self):
        self.assertIn("| :--- | :--- | :--- | :--- |", self.section)

    def test_exactly_six_data_rows(self):
        rows = re.findall(r"^\|\s*\d+\s*\|", self.section, re.MULTILINE)
        self.assertEqual(len(rows), 6)

    def test_row_numbers_sequential_one_through_six(self):
        numbers = re.findall(r"^\|\s*(\d+)\s*\|", self.section, re.MULTILINE)
        self.assertEqual([int(n) for n in numbers], [1, 2, 3, 4, 5, 6])

    def test_all_expected_scope_names_present_in_ascending_order(self):
        indices = [self.section.index(name) for _, name in self.SCOPE_ROWS]
        self.assertEqual(indices, sorted(indices))

    def test_each_row_pairs_number_with_expected_scope_name(self):
        for number, name in self.SCOPE_ROWS:
            with self.subTest(number=number, name=name):
                self.assertRegex(
                    self.section,
                    re.compile(
                        r"^\|\s*" + str(number) + r"\s*\|\s*"
                        + re.escape(name) + r"\s*\|",
                        re.MULTILINE,
                    ),
                )

    def test_internal_pentest_requires_single_internal_ip(self):
        self.assertIn("**1 Internal IP**", self.section)

    def test_internal_pentest_notes_asg_ip_may_change(self):
        self.assertIn(
            "The IP will be given once needed. Due to AWS ASG it may change.",
            self.section,
        )

    def test_external_pentest_requires_single_public_url(self):
        self.assertIn("**1 public URL**", self.section)

    def test_external_pentest_target_domains_present(self):
        for domain in ["pbtpay.kpkt.gov.my", "secure-app.enterprise.gov.my"]:
            with self.subTest(domain=domain):
                self.assertIn(domain, self.section)

    def test_web_app_assessment_targets_single_application(self):
        self.assertIn("**1 Application**", self.section)

    def test_web_app_assessment_target_matches_external_pentest_domain(self):
        """Regression: the Web Application Security Assessment target should
        reference the same domain used as the External Penetration Test
        target, since both describe the same public-facing application."""
        web_app_row_match = re.search(
            r"^\|\s*3\s*\|\s*Web Application Security Assessment\s*\|"
            r".*?\|\s*(.*?)\s*\|\s*$",
            self.section,
            re.MULTILINE,
        )
        self.assertIsNotNone(web_app_row_match)
        self.assertIn("pbtpay.kpkt.gov.my", web_app_row_match.group(1))

    def test_host_vulnerability_targets_single_instance(self):
        self.assertIn("**1 instance**", self.section)

    def test_host_vulnerability_references_asg_instance_name(self):
        self.assertIn("main-portal-ec2-my-asg", self.section)

    def test_host_vulnerability_references_hardened_ubuntu_base(self):
        self.assertIn("hardened Ubuntu 26.04 LTS Base", self.section)

    def test_database_assessment_lists_three_repositories(self):
        self.assertIn(
            "**3 Data repositories / storage services**", self.section
        )

    def test_database_assessment_enumerates_expected_services(self):
        for service in [
            "**RDS MariaDB** (Default database tier)",
            "**ElastiCache - Valkey** (In-memory session and cache)",
            "**Amazon Elastic File System (EFS)** (Shared persistent storage)",
        ]:
            with self.subTest(service=service):
                self.assertIn(service, self.section)

    def test_network_device_assessment_targets_load_balancers_and_firewalls(self):
        self.assertIn("**Load Balancers & Firewalls**", self.section)

    def test_network_device_assessment_enumerates_four_expected_components(self):
        for component in [
            "**AWS ALB - External** (`pbtpay-ny-alb`)",
            "**AWS ALB - Internal** (`pbtpay-internal-alb`)",
            "**AWS WAFv2 Web ACL** (Perimeter Layer-7 Protection)",
            "**Security Groups** (Microsegmentation Firewalls)",
        ]:
            with self.subTest(component=component):
                self.assertIn(component, self.section)

    def test_scope_descriptions_are_non_empty_for_every_row(self):
        descriptions = re.findall(
            r"^\|\s*\d+\s*\|\s*[^|]+\|\s*([^|]+?)\s*\|\s*[^|]+\|\s*$",
            self.section,
            re.MULTILINE,
        )
        self.assertEqual(len(descriptions), 6)
        for description in descriptions:
            self.assertTrue(description.strip())

    def test_no_stray_todo_or_placeholder_markers_in_scope_table(self):
        for marker in ["TODO", "FIXME", "TBD", "XXX"]:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.section)


class SecurityPostureAssessmentSignOffSectionStructureTestCase(unittest.TestCase):
    """Tests for the Section 4 restructuring: the previously separate
    top-level "## 4. Audit Evidence and Sign-Off Block" and
    "## 5. SPA Sign-Off and Verification Statement" headings were merged
    into a single top-level "## 4. SPA Sign-Off and Verification Statement"
    section containing two "###" subsections."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(SPA_MD_PATH)

    def test_top_level_section_four_heading_present(self):
        self.assertIn(
            "## 4. SPA Sign-Off and Verification Statement", self.content
        )

    def test_no_top_level_section_five_heading(self):
        self.assertNotRegex(self.content, re.compile(r"^## 5\.", re.MULTILINE))

    def test_only_four_top_level_numbered_sections_exist(self):
        headings = re.findall(r"^## \d+\.", self.content, re.MULTILINE)
        self.assertEqual(headings, ["## 1.", "## 2.", "## 3.", "## 4."])

    def test_audit_evidence_subsection_is_h3_not_h2(self):
        self.assertIn("### Audit Evidence and Sign-Off Block", self.content)
        self.assertNotIn(
            "## 4. Audit Evidence and Sign-Off Block", self.content
        )

    def test_spa_signoff_subsection_is_h3(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"^### SPA Sign-Off and Verification Statement$",
                re.MULTILINE,
            ),
        )

    def test_subsections_appear_in_order_after_top_level_heading(self):
        top_idx = self.content.index(
            "## 4. SPA Sign-Off and Verification Statement"
        )
        audit_idx = self.content.index(
            "### Audit Evidence and Sign-Off Block"
        )
        subsection_idx = self.content.index(
            "### SPA Sign-Off and Verification Statement"
        )
        self.assertLess(top_idx, audit_idx)
        self.assertLess(audit_idx, subsection_idx)

    def test_exactly_two_h3_subsections_within_section_four(self):
        section_four = self.content[
            self.content.index("## 4. SPA Sign-Off and Verification Statement"):
        ]
        subheadings = re.findall(r"^### .+$", section_four, re.MULTILINE)
        self.assertEqual(
            subheadings,
            [
                "### Audit Evidence and Sign-Off Block",
                "### SPA Sign-Off and Verification Statement",
            ],
        )

    def test_section_four_is_the_last_top_level_section_in_the_document(self):
        heading = "## 4. SPA Sign-Off and Verification Statement"
        remaining = self.content[
            self.content.index(heading) + len(heading):
        ]
        self.assertNotRegex(remaining, re.compile(r"^## ", re.MULTILINE))


class IndexMdEngineeringGuidesNumberingRegressionTestCase(unittest.TestCase):
    """Regression check documenting the current numbering in the
    "Engineering & DevOps Implementation Guides" list: entries 1-11 are
    followed directly by entry 17 for the SPA Checklist link, with no
    entries numbered 12-16."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)
        section_match = re.search(
            r"### Engineering & DevOps Implementation Guides\n(.*?)"
            r"(?=\n### |\n---|\Z)",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None
        cls.section = section_match.group(1)

    def test_numbered_items_are_one_through_eleven_then_seventeen(self):
        numbers = [
            int(n)
            for n in re.findall(r"^(\d+)\. \*\*\[", self.section, re.MULTILINE)
        ]
        self.assertEqual(numbers, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 17])

    def test_no_duplicate_numbers_in_section(self):
        numbers = re.findall(r"^(\d+)\. \*\*\[", self.section, re.MULTILINE)
        self.assertEqual(len(numbers), len(set(numbers)))

    def test_last_entry_before_spa_is_codeigniter_numbered_eleven(self):
        self.assertRegex(
            self.section,
            re.compile(
                r"^11\. \*\*\[CodeIgniter Deployment Guide\]",
                re.MULTILINE,
            ),
        )


if __name__ == "__main__":
    unittest.main()