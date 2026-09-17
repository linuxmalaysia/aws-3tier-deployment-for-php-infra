"""Unit test suite for validating the IT Management Proposal document."""

from pathlib import Path
import re


def test_it_management_proposal_file_exists():
    """Verify that IT-MANAGEMENT-PROPOSAL.md exists in docs/."""
    file_path = Path("docs/IT-MANAGEMENT-PROPOSAL.md")
    assert file_path.exists(), "docs/IT-MANAGEMENT-PROPOSAL.md must exist."


def test_it_management_proposal_frontmatter_and_content():
    """Verify frontmatter, title, PDF link, and required sections in IT-MANAGEMENT-PROPOSAL.md."""
    file_path = Path("docs/IT-MANAGEMENT-PROPOSAL.md")
    content = file_path.read_text(encoding="utf-8")

    # Frontmatter assertions
    assert content.startswith("---")
    assert 'okf_version: "0.1"' in content
    assert 'type: "Executive Proposal"' in content
    assert 'title: "IT Management Proposal: Enterprise Data & Infrastructure Modernisation (Historical to AI-Ready)"' in content

    # PDF download link
    assert "📄 **[Download Full Proposal PDF (A4 Document)](assets/IT-MANAGEMENT-PROPOSAL.pdf)**" in content

    # Scope
    assert "`aws-3tier-deployment-for-php-infra`" in content

    # Essential native project technologies present
    assert "CodeIgniter 4" in content
    assert "Fusio" in content
    assert "Amazon RDS" in content
    assert "Valkey" in content
    assert "OpenTofu" in content
    assert "Podman" in content

    # DSOM Protocol footer
    assert "Deep State of Mind (DSOM) For My AI Protocol" in content
    assert "Harisfazillah Jamel" in content


def test_it_management_proposal_no_foreign_software():
    """Ensure non-project external software technologies are not present in IT-MANAGEMENT-PROPOSAL.md."""
    file_path = Path("docs/IT-MANAGEMENT-PROPOSAL.md")
    content = file_path.read_text(encoding="utf-8")

    foreign_terms = ["NiFi", "Patroni", "Superset", "Metabase", "Laravel"]
    for term in foreign_terms:
        matches = re.findall(rf"\b{term}\b", content, re.IGNORECASE)
        assert len(matches) == 0, f"Foreign software reference '{term}' found in docs/IT-MANAGEMENT-PROPOSAL.md: {matches}"


def test_it_management_proposal_index_registration():
    """Verify that IT-MANAGEMENT-PROPOSAL.md is registered across indices."""
    docs_index = Path("docs/index.md").read_text(encoding="utf-8")
    assert "IT-MANAGEMENT-PROPOSAL.html" in docs_index

    docs_summary = Path("docs/SUMMARY.md").read_text(encoding="utf-8")
    assert "IT-MANAGEMENT-PROPOSAL.md" in docs_summary

    root_summary = Path("SUMMARY.md").read_text(encoding="utf-8")
    assert "docs/IT-MANAGEMENT-PROPOSAL.md" in root_summary

    llms_txt = Path("llms.txt").read_text(encoding="utf-8")
    assert "docs/IT-MANAGEMENT-PROPOSAL.md" in llms_txt
