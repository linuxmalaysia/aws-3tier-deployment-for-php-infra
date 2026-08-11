#!/usr/bin/env python3
"""Unit tests for the ASIMP/Lynis/OpenSCAP security hardening report
documentation pages added in this PR.

This PR introduces three new documentation pages:

* ``docs/engineering/asimp-output.md``
* ``docs/engineering/lynis-output.md``
* ``docs/engineering/openscap-output.md``

and wires them up from several other files:

* ``docs/index.md``       -- adds a new "Security Hardening & Compliance
  Reports (ASIMP)" section containing numbered links to all three new pages
  (plus the pre-existing Security Posture Assessment (SPA) Checklist link,
  which is covered separately by
  ``tests/test_security_posture_assessment_docs.py``).
* ``llms.txt``            -- adds three new AI-agent index entries.
* ``sitemap.txt`` / ``docs/sitemap.txt``   -- adds GitHub Pages and GitBook
  URLs for the three new pages.
* ``sitemap.xml`` / ``docs/sitemap.xml``   -- adds ``<url>`` entries for the
  three new pages.

These files are treated as plain text/XML (rather than requiring a live
Jekyll build) to stay dependency free, following the pattern already used by
``tests/test_security_posture_assessment_docs.py`` and
``tests/test_sitemaps.py``.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_security_hardening_reports_docs
"""
import json
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
import generate_sitemaps  # noqa: E402  (import after sys.path manipulation)

INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.md")
LLMS_PATH = os.path.join(REPO_ROOT, "llms.txt")
ASIMP_MD_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "asimp-output.md")
LYNIS_MD_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "lynis-output.md")
OPENSCAP_MD_PATH = os.path.join(
    REPO_ROOT, "docs", "engineering", "openscap-output.md"
)
ROOT_SITEMAP_TXT = os.path.join(REPO_ROOT, "sitemap.txt")
DOCS_SITEMAP_TXT = os.path.join(REPO_ROOT, "docs", "sitemap.txt")
ROOT_SITEMAP_XML = os.path.join(REPO_ROOT, "sitemap.xml")
DOCS_SITEMAP_XML = os.path.join(REPO_ROOT, "docs", "sitemap.xml")

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

GH_BASE = "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra/"
GB_BASE = "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra/docs/"

GH_ASIMP_URL = GH_BASE + "engineering/asimp-output.html"
GH_LYNIS_URL = GH_BASE + "engineering/lynis-output.html"
GH_OPENSCAP_URL = GH_BASE + "engineering/openscap-output.html"

GB_ASIMP_URL = GB_BASE + "engineering/asimp-output"
GB_LYNIS_URL = GB_BASE + "engineering/lynis-output"
GB_OPENSCAP_URL = GB_BASE + "engineering/openscap-output"

GH_SOP_URL = GH_BASE + "engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.html"
GH_ROOT_FILES_URL = GH_BASE + "engineering/root-files.html"
GH_ROUTE53_URL = GH_BASE + "engineering/route53.html"
GH_CODEIGNITER_URL = GH_BASE + "engineering/codeigniter-php-fpm.html"

GB_SOP_URL = GB_BASE + "engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY"
GB_ROOT_FILES_URL = GB_BASE + "engineering/root-files"
GB_ROUTE53_URL = GB_BASE + "engineering/route53"
GB_CODEIGNITER_URL = GB_BASE + "engineering/codeigniter-php-fpm"


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_front_matter(content):
    stripped = content.lstrip()
    parts = stripped.split("---", 2)
    # parts[0] is empty (before first ---), parts[1] is the front matter body.
    front_matter_text = parts[1]
    body_text = parts[2]
    front_matter = prepare_docs.parse_yaml_front_matter(front_matter_text)
    return front_matter, body_text


class AsimpOutputFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of docs/engineering/asimp-output.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ASIMP_MD_PATH)
        cls.front_matter, cls.body_text = _parse_front_matter(cls.content)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(ASIMP_MD_PATH))

    def test_starts_with_front_matter_delimiter(self):
        self.assertTrue(self.content.startswith("---\n"))

    def test_required_okf_fields_present(self):
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_layout_is_default(self):
        self.assertEqual(self.front_matter["layout"], "default")

    def test_okf_version_is_expected_value(self):
        self.assertEqual(self.front_matter["okf_version"], "0.1")

    def test_title_field_value(self):
        self.assertEqual(
            self.front_matter["title"], "ASIMP Security Audit & Hardening Report"
        )

    def test_type_matches_prepare_docs_inference(self):
        inferred_type = prepare_docs.infer_okf_type(
            "docs/engineering/asimp-output.md"
        )
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_match_authored_values_exactly(self):
        self.assertEqual(
            self.front_matter["topics"],
            ["security", "compliance", "audit", "report", "asimp"],
        )

    def test_topics_have_no_duplicates(self):
        topics = self.front_matter["topics"]
        self.assertEqual(len(topics), len(set(topics)))

    def test_infer_okf_topics_baseline_when_no_existing_topics(self):
        """Regression/boundary: the path contains no recognized keyword
        (vpc, rds, php, etc.), so a stripped-topics fallback would use the
        bare ["aws", "3-tier"] baseline, which differs from the
        manually-curated topics actually shipped in the file."""
        inferred = prepare_docs.infer_okf_topics("docs/engineering/asimp-output.md")
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
        self.assertEqual(heading_match.group(1).strip(), self.front_matter["title"])


class AsimpOutputContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of docs/engineering/asimp-output.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ASIMP_MD_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn(
            "# ASIMP Security Audit & Hardening Report", self.content
        )

    def test_all_five_sections_present_in_ascending_order(self):
        headings = [
            "## 1. System Execution Overview",
            "## 2. Dual-Engine Compliance Scorecard",
            "## 3. JSON Baseline Scores Output",
            "## 4. Executed Remediations & Mitigations",
            "## 5. Security Verification & Audit Evidence",
        ]
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)
        indices = [self.content.index(h) for h in headings]
        self.assertEqual(indices, sorted(indices))

    def test_target_host_and_region_present(self):
        self.assertIn("main-portal-ec2-my-asg", self.content)
        self.assertIn("ap-southeast-5", self.content)

    def test_scorecard_table_contains_expected_kpi_values(self):
        for value in ["75", "62", "88", "85+", "58.4%", "91.2%", "90%+"]:
            with self.subTest(value=value):
                self.assertIn(value, self.content)

    def test_lynis_hardening_index_kpi_status_pass(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\*\*Lynis Hardening Index\*\*:.*?Status: \*\*PASS\*\*",
                re.DOTALL,
            ),
        )

    def test_openscap_compliance_kpi_status_pass(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\*\*OpenSCAP CIS Level 2 Compliance %\*\*:.*?Status: \*\*PASS\*\*",
                re.DOTALL,
            ),
        )

    def test_json_baseline_scores_block_is_valid_json(self):
        match = re.search(r"```json\n(.*?)\n```", self.content, re.DOTALL)
        self.assertIsNotNone(match, "Could not locate the fenced JSON block")
        data = json.loads(match.group(1))
        self.assertEqual(
            data,
            {
                "openscap_before": "58.4",
                "lynis_before": "62",
                "openscap_after": "91.2",
                "lynis_after": "88",
                "timestamp": "2026-08-10T15:30:00Z",
                "environment": "ap-southeast-5-sandbox",
                "privilege_level": "limited-sandbox-mock",
            },
        )

    def test_json_block_appears_within_section_three(self):
        section_three_idx = self.content.index("## 3. JSON Baseline Scores Output")
        section_four_idx = self.content.index(
            "## 4. Executed Remediations & Mitigations"
        )
        json_idx = self.content.index("```json")
        self.assertLess(section_three_idx, json_idx)
        self.assertLess(json_idx, section_four_idx)

    def test_remediations_mention_ssh_lockdown_and_kernel_hardening(self):
        self.assertIn("SSH Service Lockdown", self.content)
        self.assertIn("Kernel Parametric Hardening (`sysctl.conf`)", self.content)
        self.assertIn("AllowTcpForwarding=no", self.content)

    def test_mentions_malaysian_sovereign_data_laws_banner(self):
        self.assertIn(
            "Malaysian sovereign data laws and authorized access limits",
            self.content,
        )

    def test_no_stray_todo_or_placeholder_markers(self):
        for marker in ["TODO", "FIXME", "TBD", "XXX"]:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.content)


class LynisOutputFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of docs/engineering/lynis-output.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LYNIS_MD_PATH)
        cls.front_matter, cls.body_text = _parse_front_matter(cls.content)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(LYNIS_MD_PATH))

    def test_required_okf_fields_present(self):
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_title_field_value(self):
        self.assertEqual(
            self.front_matter["title"], "Lynis Security Audit Output Report"
        )

    def test_type_matches_prepare_docs_inference(self):
        inferred_type = prepare_docs.infer_okf_type(
            "docs/engineering/lynis-output.md"
        )
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_match_authored_values_exactly(self):
        self.assertEqual(
            self.front_matter["topics"],
            ["security", "compliance", "audit", "report", "lynis"],
        )

    def test_timestamp_matches_iso8601_with_offset(self):
        self.assertRegex(
            self.front_matter["timestamp"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$",
        )

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        self.assertEqual(heading_match.group(1).strip(), self.front_matter["title"])


class LynisOutputContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of docs/engineering/lynis-output.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LYNIS_MD_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn("# Lynis Security Audit Output Report", self.content)

    def test_all_four_sections_present_in_ascending_order(self):
        headings = [
            "## 1. Lynis Scan System Identification",
            "## 2. Lynis Scan Output & Findings Log",
            "## 3. Core Suggestions & Warnings Generated",
            "## 4. Total Hardening Index (HI) Over Time",
        ]
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)
        indices = [self.content.index(h) for h in headings]
        self.assertEqual(indices, sorted(indices))

    def test_ssh_hardening_findings_present(self):
        for value in [
            "PermitRootLogin",
            "PasswordAuthentication",
            "MaxAuthTries",
            "AllowTcpForwarding",
        ]:
            with self.subTest(value=value):
                self.assertIn(value, self.content)

    def test_warning_and_suggestion_ids_present_and_unique(self):
        full_ids = re.findall(r"\[((?:WARNING|SUGGESTION)-[A-Z]+-\d{2})\]", self.content)
        self.assertEqual(len(full_ids), 4)
        self.assertEqual(len(full_ids), len(set(full_ids)))
        self.assertEqual(
            full_ids,
            [
                "WARNING-NET-01",
                "SUGGESTION-AUTH-04",
                "SUGGESTION-FILE-08",
                "SUGGESTION-KERN-12",
            ],
        )

    def test_hardening_index_values_present(self):
        for value in ["62", "88", "75", "100"]:
            with self.subTest(value=value):
                self.assertIn(value, self.content)

    def test_mentions_pdpa_section_129_compliance(self):
        self.assertIn("PDPA Section 129", self.content)

    def test_mentions_fail2ban_mitigation_via_jumphost(self):
        self.assertIn("fail2ban", self.content)
        self.assertIn("hardened SSH Jumphost (Bastion)", self.content)

    def test_no_stray_todo_or_placeholder_markers(self):
        for marker in ["TODO", "FIXME", "TBD", "XXX"]:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.content)


class OpenscapOutputFrontMatterTestCase(unittest.TestCase):
    """Tests for the OKF front matter of docs/engineering/openscap-output.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(OPENSCAP_MD_PATH)
        cls.front_matter, cls.body_text = _parse_front_matter(cls.content)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(OPENSCAP_MD_PATH))

    def test_required_okf_fields_present(self):
        for key in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            self.assertIn(key, self.front_matter)

    def test_title_field_value(self):
        self.assertEqual(
            self.front_matter["title"], "OpenSCAP Security Audit Output Report"
        )

    def test_type_matches_prepare_docs_inference(self):
        inferred_type = prepare_docs.infer_okf_type(
            "docs/engineering/openscap-output.md"
        )
        self.assertEqual(inferred_type, "Technical Reference Guide")
        self.assertEqual(self.front_matter["type"], inferred_type)

    def test_topics_match_authored_values_exactly(self):
        self.assertEqual(
            self.front_matter["topics"],
            ["security", "compliance", "audit", "report", "openscap"],
        )

    def test_timestamp_matches_iso8601_with_offset(self):
        self.assertRegex(
            self.front_matter["timestamp"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$",
        )

    def test_title_matches_first_markdown_heading_in_body(self):
        heading_match = prepare_docs.HEADING_PATTERN.search(self.body_text)
        self.assertIsNotNone(heading_match)
        self.assertEqual(heading_match.group(1).strip(), self.front_matter["title"])


class OpenscapOutputContentStructureTestCase(unittest.TestCase):
    """Tests for the structural content of
    docs/engineering/openscap-output.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(OPENSCAP_MD_PATH)

    def test_contains_top_level_heading(self):
        self.assertIn("# OpenSCAP Security Audit Output Report", self.content)

    def test_all_five_sections_present_in_ascending_order(self):
        headings = [
            "## 1. OpenSCAP Scan Specifications",
            "## 2. Rule Evaluation & Compliance Results",
            "## 3. Selected Rule Verification Logs",
            "## 4. OVAL Vulnerability Assessment",
            "## 5. Automated Remediation Shell Script",
        ]
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.content)
        indices = [self.content.index(h) for h in headings]
        self.assertEqual(indices, sorted(indices))

    def test_compliance_summary_table_has_six_data_rows(self):
        section_match = re.search(
            r"### Subsystem Compliance Summary Table\n(.*?)\n---",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        rows = re.findall(r"^\| \*\*[^|]+\*\* \|", section_match.group(1), re.MULTILINE)
        self.assertEqual(len(rows), 6)

    def test_compliance_summary_rows_all_compliant(self):
        section_match = re.search(
            r"### Subsystem Compliance Summary Table\n(.*?)\n---",
            self.content,
            re.DOTALL,
        )
        self.assertIsNotNone(section_match)
        self.assertEqual(
            section_match.group(1).count("✅ Compliant"), 6
        )

    def test_selected_rule_ids_present(self):
        for rule_id in [
            "xccdf_org.ssgproject.content_rule_sshd_disable_root_login",
            "xccdf_org.ssgproject.content_rule_file_permissions_etc_shadow",
            "xccdf_org.ssgproject.content_rule_sysctl_net_ipv4_tcp_syncookies",
        ]:
            with self.subTest(rule_id=rule_id):
                self.assertIn(rule_id, self.content)

    def test_selected_rules_all_marked_fixed(self):
        self.assertEqual(self.content.count("Status: **Fixed**"), 3)

    def test_oval_assessment_reports_zero_vulnerabilities(self):
        self.assertIn("**Security Vulnerabilities Identified**: `0`", self.content)
        self.assertIn("**Tested Packages**: 180", self.content)

    def test_remediation_script_is_bash_and_contains_expected_commands(self):
        match = re.search(r"```bash\n(.*?)\n```", self.content, re.DOTALL)
        self.assertIsNotNone(match, "Could not locate the fenced bash script block")
        script = match.group(1)
        self.assertTrue(script.startswith("#!/bin/bash"))
        self.assertIn("sysctl -q -n -w net.ipv4.tcp_syncookies=1", script)
        self.assertIn("chmod 0600 /etc/shadow", script)
        self.assertIn("systemctl restart ssh", script)

    def test_remediation_script_appears_within_section_five(self):
        section_five_idx = self.content.index(
            "## 5. Automated Remediation Shell Script"
        )
        bash_idx = self.content.index("```bash")
        self.assertLess(section_five_idx, bash_idx)

    def test_no_stray_todo_or_placeholder_markers(self):
        for marker in ["TODO", "FIXME", "TBD", "XXX"]:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.content)


class IndexMdSecurityHardeningSectionTestCase(unittest.TestCase):
    """Tests for the new "Security Hardening & Compliance Reports (ASIMP)"
    section added to docs/index.md."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(INDEX_PATH)
        section_match = re.search(
            r"### Security Hardening & Compliance Reports \(ASIMP\)\n"
            r"(.*?)(?=\n### |\n---|\Z)",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None
        cls.section = section_match.group(1)

    def test_section_heading_present(self):
        self.assertIn(
            "### Security Hardening & Compliance Reports (ASIMP)", self.content
        )

    def test_section_appears_after_engineering_devops_section(self):
        engineering_idx = self.content.index(
            "### Engineering & DevOps Implementation Guides"
        )
        hardening_idx = self.content.index(
            "### Security Hardening & Compliance Reports (ASIMP)"
        )
        self.assertLess(engineering_idx, hardening_idx)

    def test_section_appears_before_infrastructure_submodules_section(self):
        hardening_idx = self.content.index(
            "### Security Hardening & Compliance Reports (ASIMP)"
        )
        submodules_idx = self.content.index("### Infrastructure Submodules")
        self.assertLess(hardening_idx, submodules_idx)

    def test_asimp_link_present_with_expected_description(self):
        self.assertRegex(
            self.section,
            re.compile(
                r"\*\*\[Output of ASIMP\]\(engineering/asimp-output\.html\):\*\*"
                r"\s*Standardized, multi-engine security hardening progress "
                r"and consolidated scorecard report\."
            ),
        )

    def test_lynis_link_present_with_expected_description(self):
        self.assertRegex(
            self.section,
            re.compile(
                r"\*\*\[Output of Lynis\]\(engineering/lynis-output\.html\):\*\*"
                r"\s*Detailed Unix-based host configuration scanning and "
                r"hardening index rating scorecard\."
            ),
        )

    def test_openscap_link_present_with_expected_description(self):
        self.assertRegex(
            self.section,
            re.compile(
                r"\*\*\[Output of OpenSCAP\]\(engineering/openscap-output\.html\):\*\*"
                r"\s*Detailed CIS Level 2 benchmark profile compliance checklist "
                r"and OVAL vulnerability reports\."
            ),
        )

    def test_entries_are_numbered_one_through_four_in_order(self):
        numbers = [
            int(n) for n in re.findall(r"^(\d+)\. \*\*\[", self.section, re.MULTILINE)
        ]
        self.assertEqual(numbers, [1, 2, 3, 4])

    def test_entries_appear_in_expected_order(self):
        titles = [
            "[Security Posture Assessment (SPA) Checklist]",
            "[Output of ASIMP]",
            "[Output of Lynis]",
            "[Output of OpenSCAP]",
        ]
        indices = [self.section.index(t) for t in titles]
        self.assertEqual(indices, sorted(indices))

    def test_no_duplicate_numbers_in_section(self):
        numbers = re.findall(r"^(\d+)\. \*\*\[", self.section, re.MULTILINE)
        self.assertEqual(len(numbers), len(set(numbers)))

    def test_section_wrapped_by_markdownlint_disable_enable_comments(self):
        self.assertIn(
            "### Security Hardening & Compliance Reports (ASIMP)\n"
            "<!-- markdownlint-disable MD029 -->",
            self.content,
        )
        # The section body (captured up to the next "### " or "---") should
        # itself terminate with the matching enable comment.
        self.assertIn("<!-- markdownlint-enable MD029 -->", self.section)

    def test_links_use_relative_html_urls_not_markdown_extension(self):
        for slug in ["asimp-output", "lynis-output", "openscap-output"]:
            with self.subTest(slug=slug):
                self.assertIn(f"(engineering/{slug}.html)", self.section)
                self.assertNotIn(f"(engineering/{slug}.md)", self.section)

    def test_each_new_link_target_file_exists(self):
        for path in [ASIMP_MD_PATH, LYNIS_MD_PATH, OPENSCAP_MD_PATH]:
            with self.subTest(path=path):
                self.assertTrue(os.path.isfile(path))

    def test_each_link_appears_exactly_once_in_whole_document(self):
        for title in ["[Output of ASIMP]", "[Output of Lynis]", "[Output of OpenSCAP]"]:
            with self.subTest(title=title):
                self.assertEqual(self.content.count(title), 1)


class LlmsTxtSecurityHardeningEntriesTestCase(unittest.TestCase):
    """Tests for the three new entries added to llms.txt."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(LLMS_PATH)
        section_match = re.search(
            r"## Core Architectural Documentation \(Engineering\)\n(.*?)(?=\n## |\Z)",
            cls.content,
            re.DOTALL,
        )
        assert section_match is not None
        cls.section = section_match.group(1)

    def test_llms_txt_file_exists(self):
        self.assertTrue(os.path.isfile(LLMS_PATH))

    def test_asimp_entry_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\[Output of ASIMP\]\(docs/engineering/asimp-output\.md\)\s*:"
                r"\s*Standardized, multi-engine security hardening progress "
                r"and consolidated scorecard report\."
            ),
        )

    def test_lynis_entry_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\[Output of Lynis\]\(docs/engineering/lynis-output\.md\)\s*:"
                r"\s*Detailed Unix-based host configuration scanning and "
                r"hardening index rating scorecard\."
            ),
        )

    def test_openscap_entry_present(self):
        self.assertRegex(
            self.content,
            re.compile(
                r"\[Output of OpenSCAP\]\(docs/engineering/openscap-output\.md\)\s*:"
                r"\s*Detailed CIS Level 2 benchmark profile compliance checklist "
                r"and OVAL vulnerability reports\."
            ),
        )

    def test_all_three_entries_under_engineering_architectural_section(self):
        for title in [
            "[Output of ASIMP](docs/engineering/asimp-output.md)",
            "[Output of Lynis](docs/engineering/lynis-output.md)",
            "[Output of OpenSCAP](docs/engineering/openscap-output.md)",
        ]:
            with self.subTest(title=title):
                self.assertIn(title, self.section)

    def test_entries_appear_directly_after_spa_entry_in_order(self):
        spa_idx = self.content.index(
            "[Security Posture Assessment](docs/engineering/security-posture-assessment.md)"
        )
        asimp_idx = self.content.index(
            "[Output of ASIMP](docs/engineering/asimp-output.md)"
        )
        lynis_idx = self.content.index(
            "[Output of Lynis](docs/engineering/lynis-output.md)"
        )
        openscap_idx = self.content.index(
            "[Output of OpenSCAP](docs/engineering/openscap-output.md)"
        )
        self.assertEqual(
            [spa_idx, asimp_idx, lynis_idx, openscap_idx],
            sorted([spa_idx, asimp_idx, lynis_idx, openscap_idx]),
        )

    def test_entries_follow_bullet_link_colon_description_format(self):
        for slug, title in [
            ("asimp-output", "Output of ASIMP"),
            ("lynis-output", "Output of Lynis"),
            ("openscap-output", "Output of OpenSCAP"),
        ]:
            with self.subTest(slug=slug):
                match = re.search(
                    r"^- \[" + re.escape(title) + r"\]"
                    r"\(docs/engineering/" + re.escape(slug) + r"\.md\) : .+$",
                    self.content,
                    re.MULTILINE,
                )
                self.assertIsNotNone(
                    match,
                    f"Entry for {title} does not follow the expected bullet format",
                )

    def test_each_entry_appears_exactly_once(self):
        for title in ["[Output of ASIMP]", "[Output of Lynis]", "[Output of OpenSCAP]"]:
            with self.subTest(title=title):
                self.assertEqual(self.content.count(title), 1)

    def test_entry_target_files_exist(self):
        for path in [ASIMP_MD_PATH, LYNIS_MD_PATH, OPENSCAP_MD_PATH]:
            with self.subTest(path=path):
                self.assertTrue(os.path.isfile(path))


class SitemapTxtSecurityHardeningEntriesTestCase(unittest.TestCase):
    """Tests for the new URLs added to sitemap.txt and docs/sitemap.txt for
    the ASIMP, Lynis, and OpenSCAP output pages."""

    SITEMAP_PATHS = [ROOT_SITEMAP_TXT, DOCS_SITEMAP_TXT]

    @classmethod
    def setUpClass(cls):
        cls.contents = {path: _read(path) for path in cls.SITEMAP_PATHS}

    def test_sitemap_files_exist(self):
        for path in self.SITEMAP_PATHS:
            with self.subTest(path=path):
                self.assertTrue(os.path.isfile(path))

    def test_all_gh_urls_present_in_both_copies(self):
        for path, content in self.contents.items():
            for url in [GH_ASIMP_URL, GH_LYNIS_URL, GH_OPENSCAP_URL]:
                with self.subTest(path=path, url=url):
                    self.assertIn(url, content)

    def test_all_gb_urls_present_in_both_copies(self):
        for path, content in self.contents.items():
            for url in [GB_ASIMP_URL, GB_LYNIS_URL, GB_OPENSCAP_URL]:
                with self.subTest(path=path, url=url):
                    self.assertIn(url, content)

    def test_root_and_docs_copies_are_identical(self):
        self.assertEqual(
            self.contents[ROOT_SITEMAP_TXT], self.contents[DOCS_SITEMAP_TXT]
        )

    def test_each_url_appears_exactly_once_per_copy(self):
        for path, content in self.contents.items():
            for url in [
                GH_ASIMP_URL, GH_LYNIS_URL, GH_OPENSCAP_URL,
                GB_ASIMP_URL, GB_LYNIS_URL, GB_OPENSCAP_URL,
            ]:
                with self.subTest(path=path, url=url):
                    self.assertEqual(content.count(url), 1)

    def test_gh_asimp_url_appears_between_sop_and_root_files(self):
        for path, content in self.contents.items():
            with self.subTest(path=path):
                sop_idx = content.index(GH_SOP_URL)
                asimp_idx = content.index(GH_ASIMP_URL)
                root_files_idx = content.index(GH_ROOT_FILES_URL)
                self.assertLess(sop_idx, asimp_idx)
                self.assertLess(asimp_idx, root_files_idx)

    def test_gh_openscap_and_lynis_urls_appear_between_route53_and_codeigniter(self):
        for path, content in self.contents.items():
            with self.subTest(path=path):
                route53_idx = content.index(GH_ROUTE53_URL)
                openscap_idx = content.index(GH_OPENSCAP_URL)
                lynis_idx = content.index(GH_LYNIS_URL)
                codeigniter_idx = content.index(GH_CODEIGNITER_URL)
                self.assertLess(route53_idx, openscap_idx)
                self.assertLess(openscap_idx, lynis_idx)
                self.assertLess(lynis_idx, codeigniter_idx)

    def test_gb_asimp_url_appears_between_sop_and_root_files(self):
        for path, content in self.contents.items():
            with self.subTest(path=path):
                sop_idx = content.index(GB_SOP_URL)
                asimp_idx = content.index(GB_ASIMP_URL)
                root_files_idx = content.index(GB_ROOT_FILES_URL)
                self.assertLess(sop_idx, asimp_idx)
                self.assertLess(asimp_idx, root_files_idx)

    def test_gb_openscap_and_lynis_urls_appear_between_route53_and_codeigniter(self):
        for path, content in self.contents.items():
            with self.subTest(path=path):
                route53_idx = content.index(GB_ROUTE53_URL)
                openscap_idx = content.index(GB_OPENSCAP_URL)
                lynis_idx = content.index(GB_LYNIS_URL)
                codeigniter_idx = content.index(GB_CODEIGNITER_URL)
                self.assertLess(route53_idx, openscap_idx)
                self.assertLess(openscap_idx, lynis_idx)
                self.assertLess(lynis_idx, codeigniter_idx)

    def test_all_new_urls_are_well_formed_https(self):
        for url in [
            GH_ASIMP_URL, GH_LYNIS_URL, GH_OPENSCAP_URL,
            GB_ASIMP_URL, GB_LYNIS_URL, GB_OPENSCAP_URL,
        ]:
            with self.subTest(url=url):
                self.assertTrue(url.startswith("https://"))
                self.assertNotIn("//", url[8:])


class SitemapXmlSecurityHardeningEntriesTestCase(unittest.TestCase):
    """Tests for the new <url> entries added to sitemap.xml and
    docs/sitemap.xml for the ASIMP, Lynis, and OpenSCAP output pages."""

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
            for url in [GH_ASIMP_URL, GH_LYNIS_URL, GH_OPENSCAP_URL]:
                with self.subTest(path=path, url=url):
                    matches = [
                        u
                        for u in root.findall(f"{SITEMAP_NS}url")
                        if u.find(f"{SITEMAP_NS}loc") is not None
                        and u.find(f"{SITEMAP_NS}loc").text == url
                    ]
                    self.assertEqual(len(matches), 1)

    def test_each_new_url_node_has_expected_fields(self):
        for path in self.XML_PATHS:
            for url in [GH_ASIMP_URL, GH_LYNIS_URL, GH_OPENSCAP_URL]:
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
                    self.assertEqual(priority.text, "0.6")

    def test_new_url_nodes_lastmod_derived_from_git_timestamp(self):
        """Regression: Assert that the <lastmod> element for each of the security
        hardening output pages is dynamically derived from the source file git/mtime
        timestamp, ensuring sitemap updates are accurate and robust."""
        # Map URL to its source markdown file path
        url_to_md_map = {
            GH_ASIMP_URL: ASIMP_MD_PATH,
            GH_LYNIS_URL: LYNIS_MD_PATH,
            GH_OPENSCAP_URL: OPENSCAP_MD_PATH,
        }
        for path in self.XML_PATHS:
            for url in [GH_ASIMP_URL, GH_LYNIS_URL, GH_OPENSCAP_URL]:
                with self.subTest(path=path, url=url):
                    node = self._find_url_node(path, url)
                    self.assertIsNotNone(node)
                    lastmod = node.find(f"{SITEMAP_NS}lastmod")
                    md_path = url_to_md_map[url]
                    expected_date = generate_sitemaps.get_git_timestamp(md_path)
                    self.assertEqual(lastmod.text, expected_date)

    def test_asimp_url_node_appears_between_sop_and_root_files(self):
        for path in self.XML_PATHS:
            with self.subTest(path=path):
                root = self.trees[path].getroot()
                locs = [
                    u.find(f"{SITEMAP_NS}loc").text
                    for u in root.findall(f"{SITEMAP_NS}url")
                    if u.find(f"{SITEMAP_NS}loc") is not None
                ]
                sop_idx = locs.index(GH_SOP_URL)
                asimp_idx = locs.index(GH_ASIMP_URL)
                root_files_idx = locs.index(GH_ROOT_FILES_URL)
                self.assertLess(sop_idx, asimp_idx)
                self.assertLess(asimp_idx, root_files_idx)

    def test_openscap_and_lynis_url_nodes_appear_between_route53_and_codeigniter(self):
        for path in self.XML_PATHS:
            with self.subTest(path=path):
                root = self.trees[path].getroot()
                locs = [
                    u.find(f"{SITEMAP_NS}loc").text
                    for u in root.findall(f"{SITEMAP_NS}url")
                    if u.find(f"{SITEMAP_NS}loc") is not None
                ]
                route53_idx = locs.index(GH_ROUTE53_URL)
                openscap_idx = locs.index(GH_OPENSCAP_URL)
                lynis_idx = locs.index(GH_LYNIS_URL)
                codeigniter_idx = locs.index(GH_CODEIGNITER_URL)
                self.assertLess(route53_idx, openscap_idx)
                self.assertLess(openscap_idx, lynis_idx)
                self.assertLess(lynis_idx, codeigniter_idx)

    def test_root_and_docs_xml_copies_are_identical(self):
        self.assertEqual(
            self.raw_contents[ROOT_SITEMAP_XML], self.raw_contents[DOCS_SITEMAP_XML]
        )

    def test_root_document_lastmod_bumped_to_2026_08_11(self):
        """Sanity check on the surrounding diff: the homepage <url> node
        (unrelated to the three new pages) was bumped forward a day."""
        for path in self.XML_PATHS:
            with self.subTest(path=path):
                root = self.trees[path].getroot()
                homepage_node = self._find_url_node(path, GH_BASE)
                self.assertIsNotNone(homepage_node)
                lastmod = homepage_node.find(f"{SITEMAP_NS}lastmod")
                self.assertEqual(lastmod.text, "2026-08-11")


class CrossFileSecurityHardeningReferenceConsistencyTestCase(unittest.TestCase):
    """Verifies the slugs used for asimp-output, lynis-output, and
    openscap-output are consistent across docs/index.md, llms.txt, and the
    sitemap files."""

    @classmethod
    def setUpClass(cls):
        cls.index_content = _read(INDEX_PATH)
        cls.llms_content = _read(LLMS_PATH)
        cls.sitemap_txt_content = _read(ROOT_SITEMAP_TXT)

    def test_html_slugs_used_in_index(self):
        for slug in ["asimp-output", "lynis-output", "openscap-output"]:
            with self.subTest(slug=slug):
                self.assertIn(f"(engineering/{slug}.html)", self.index_content)

    def test_html_slugs_used_in_sitemap_txt(self):
        for url in [GH_ASIMP_URL, GH_LYNIS_URL, GH_OPENSCAP_URL]:
            with self.subTest(url=url):
                self.assertIn(url, self.sitemap_txt_content)

    def test_markdown_paths_consistent_between_llms_txt_and_filesystem(self):
        for slug, expected_path in [
            ("asimp-output", ASIMP_MD_PATH),
            ("lynis-output", LYNIS_MD_PATH),
            ("openscap-output", OPENSCAP_MD_PATH),
        ]:
            with self.subTest(slug=slug):
                match = re.search(
                    r"\((docs/engineering/" + re.escape(slug) + r"\.md)\)",
                    self.llms_content,
                )
                self.assertIsNotNone(match)
                referenced_path = os.path.join(REPO_ROOT, match.group(1))
                self.assertTrue(os.path.isfile(referenced_path))
                self.assertEqual(
                    os.path.normpath(referenced_path), expected_path
                )


if __name__ == "__main__":
    unittest.main()