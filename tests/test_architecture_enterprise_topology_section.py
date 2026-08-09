#!/usr/bin/env python3
"""Unit tests for the new "Multi-AZ Enterprise Costing Topology vs. Baseline
Deployment" section appended to ``docs/engineering/architecture.md``.

This PR adds a closing section to the System Architecture guide that
reconciles the differences between the document's Baseline Deployment
Topology (single unified ASG, single database engine, single-node Valkey)
and the Separate Enterprise-Scale Costing Topology documented in
``docs/executive/production-costing.md`` (nine functional ASGs, dual
managed database engines, and a Multi-AZ Valkey replication cluster).

These files are treated as plain text (rather than parsed with a YAML/HTML
library) to stay dependency free, following the pattern already used by
other doc-consistency test modules in this repository.

Run with:
    python3 -m unittest discover -s tests
or:
    python3 -m unittest tests.test_architecture_enterprise_topology_section
"""
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARCHITECTURE_PATH = os.path.join(REPO_ROOT, "docs", "engineering", "architecture.md")
PROD_COSTING_PATH = os.path.join(REPO_ROOT, "docs", "executive", "production-costing.md")

SECTION_HEADING = "## Multi-AZ Enterprise Costing Topology vs. Baseline Deployment"


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class ArchitectureNewSectionPresenceTestCase(unittest.TestCase):
    """Tests confirming the new section exists and is correctly appended at
    the end of the document."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ARCHITECTURE_PATH)

    def test_file_exists(self):
        self.assertTrue(os.path.isfile(ARCHITECTURE_PATH))

    def test_section_heading_present(self):
        self.assertIn(SECTION_HEADING, self.content)

    def test_section_heading_appears_exactly_once(self):
        self.assertEqual(self.content.count(SECTION_HEADING), 1)

    def test_section_is_the_final_section_in_the_document(self):
        """Regression: the new section was appended after the pre-existing
        'Routing Configuration' -> 'Database Route Table' content, so it
        must be the last heading in the file."""
        headings = re.findall(r"^##+ .+$", self.content, re.MULTILINE)
        self.assertTrue(headings, "Expected at least one heading in the document")
        self.assertEqual(headings[-1], SECTION_HEADING)

    def test_section_appears_after_database_route_table_section(self):
        db_route_idx = self.content.index("### Database Route Table")
        section_idx = self.content.index(SECTION_HEADING)
        self.assertLess(db_route_idx, section_idx)

    def test_section_preceded_by_horizontal_rule(self):
        idx = self.content.index(SECTION_HEADING)
        preceding = self.content[:idx].rstrip("\n")
        self.assertTrue(preceding.endswith("---"))


class ArchitectureNewSectionContentTestCase(unittest.TestCase):
    """Tests for the body content of the new comparative topology section."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ARCHITECTURE_PATH)
        section_match = re.search(
            re.escape(SECTION_HEADING) + r"\n(.*)\Z", cls.content, re.DOTALL
        )
        assert section_match is not None
        cls.section = section_match.group(1)

    def test_describes_baseline_as_developer_first_design_mirror(self):
        self.assertIn("**Baseline Deployment Topology**", self.section)
        self.assertIn(
            "mirrors the developer's original design using standard instances",
            self.section,
        )

    def test_describes_separate_enterprise_scale_costing_topology(self):
        self.assertIn("**Separate Enterprise-Scale Costing Topology**", self.section)

    def test_links_to_production_costing_estimate(self):
        self.assertIn(
            "[Production Costing Estimate](../executive/production-costing.html)",
            self.section,
        )

    def test_link_notes_source_markdown_file(self):
        self.assertIn(
            "rendered from `docs/executive/production-costing.md`", self.section
        )

    def test_link_target_markdown_file_exists(self):
        self.assertTrue(os.path.isfile(PROD_COSTING_PATH))

    def test_relative_link_resolves_to_the_correct_file_on_disk(self):
        # docs/engineering/architecture.md -> ../executive/production-costing.html
        # should resolve to docs/executive/production-costing.md
        architecture_dir = os.path.dirname(ARCHITECTURE_PATH)
        resolved = os.path.normpath(
            os.path.join(architecture_dir, "../executive/production-costing.md")
        )
        self.assertEqual(resolved, PROD_COSTING_PATH)

    def test_three_key_distinctions_are_numbered_one_through_three(self):
        items = re.findall(r"^\d+\.\s+\*\*", self.section, re.MULTILINE)
        self.assertEqual(len(items), 3)

    def test_distinction_one_is_asg_segregation(self):
        self.assertIn("**ASG Segregation:**", self.section)
        self.assertIn("single unified Auto Scaling Group", self.section)
        self.assertIn("nine (9) distinct functional ASGs", self.section)
        self.assertIn("Separation of Concerns", self.section)

    def test_distinction_two_is_database_engine_redundancy(self):
        self.assertIn("**Database Engine Redundancy:**", self.section)
        self.assertIn("single primary database engine", self.section)
        self.assertIn("RDS MariaDB with an active single-AZ Read Replica", self.section)
        self.assertIn("Multi-AZ RDS PostgreSQL vector database", self.section)

    def test_distinction_three_is_caching_multi_node_clustering(self):
        self.assertIn("**Caching Multi-Node Clustering:**", self.section)
        self.assertIn("single-node Valkey cache", self.section)
        self.assertIn("three-node `cache.r6g.2xlarge`", self.section)
        self.assertIn("`cache.t4g.medium`", self.section)

    def test_distinctions_appear_in_expected_order(self):
        asg_idx = self.section.index("**ASG Segregation:**")
        db_idx = self.section.index("**Database Engine Redundancy:**")
        cache_idx = self.section.index("**Caching Multi-Node Clustering:**")
        self.assertLess(asg_idx, db_idx)
        self.assertLess(db_idx, cache_idx)

    def test_no_trailing_content_after_third_distinction(self):
        """Regression: this section should end cleanly after item 3, with
        no stray placeholder text left behind."""
        cache_idx = self.section.index("**Caching Multi-Node Clustering:**")
        trailing = self.section[cache_idx:].strip()
        # Only a single numbered bullet's worth of text should remain.
        self.assertEqual(trailing.count("\n\n"), 0)


class ArchitectureDocumentUnaffectedByThisChangeTestCase(unittest.TestCase):
    """Regression checks confirming the pre-existing architecture content
    was left untouched by this purely-additive change."""

    @classmethod
    def setUpClass(cls):
        cls.content = _read(ARCHITECTURE_PATH)

    def test_original_title_heading_unchanged(self):
        self.assertIn("# System Architecture", self.content)

    def test_original_front_matter_timestamp_unchanged(self):
        self.assertIn("timestamp: 2026-08-05T22:20:36+08:00", self.content)

    def test_pre_existing_network_isolation_section_still_present(self):
        self.assertIn("## Network Isolation Layers", self.content)

    def test_pre_existing_routing_configuration_section_still_present(self):
        self.assertIn("## Routing Configuration", self.content)


if __name__ == "__main__":
    unittest.main()