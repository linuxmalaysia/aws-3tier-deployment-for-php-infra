"""Unit test suite for validating the Enterprise Observability Proposal document."""

from pathlib import Path


def test_enterprise_observability_proposal_files_exist():
    """Verify that Markdown, SVG diagram, and PDF download files exist in expected paths."""
    md_file = Path("docs/executive/enterprise-observability-proposal.md")
    svg_file = Path("docs/assets/enterprise-observability-architecture.svg")
    pdf_file = Path("docs/assets/ENTERPRISE-OBSERVABILITY-PROPOSAL.pdf")

    assert md_file.exists(), "docs/executive/enterprise-observability-proposal.md must exist."
    assert svg_file.exists(), "docs/assets/enterprise-observability-architecture.svg must exist."
    assert pdf_file.exists(), "docs/assets/ENTERPRISE-OBSERVABILITY-PROPOSAL.pdf must exist."
    assert pdf_file.stat().st_size > 10000, "Generated PDF file size must be > 10KB."


def test_enterprise_observability_proposal_content():
    """Verify OKF frontmatter, Document Control, single image constraint, and DSOM footer."""
    md_file = Path("docs/executive/enterprise-observability-proposal.md")
    content = md_file.read_text(encoding="utf-8")

    # Frontmatter assertions
    assert content.startswith("---")
    assert 'okf_version: "0.1"' in content
    assert 'type: "Executive Proposal"' in content
    assert 'title: "Enterprise Observability Modernisation: CloudWatch RUM, APM & Infrastructure Telemetry"' in content

    # Metadata & PDF Download Link
    assert "EBOOK-PROP-OBS-2026-CW01" in content
    assert "📄 **[Download Full Proposal PDF (A4 Document)](../assets/ENTERPRISE-OBSERVABILITY-PROPOSAL.pdf)**" in content

    # Single Image Constraint check (Must only contain exactly 1 image markdown tag)
    image_tags = [line for line in content.splitlines() if line.strip().startswith("![")]
    assert len(image_tags) == 1, f"Document must contain exactly 1 image tag, found {len(image_tags)}: {image_tags}"
    assert "enterprise-observability-architecture.svg" in image_tags[0]

    # Required Technical Sections
    assert "Executive Value Drivers" in content
    assert "CloudWatch Real User Monitoring (RUM)" in content
    assert "CloudWatch APM & Application Signals" in content
    assert "Unified CloudWatch Agent" in content
    assert "Dynatrace" in content
    assert "ap-southeast-5" in content

    # DSOM Footer
    assert "Deep State of Mind (DSOM) For My AI Protocol" in content
    assert "Harisfazilled Jamel" in content or "Harisfazillah Jamel" in content


def test_enterprise_observability_proposal_index_registration():
    """Verify that the proposal is registered across indices."""
    docs_index = Path("docs/index.md").read_text(encoding="utf-8")
    assert "executive/enterprise-observability-proposal.html" in docs_index

    docs_summary = Path("docs/SUMMARY.md").read_text(encoding="utf-8")
    assert "executive/enterprise-observability-proposal.md" in docs_summary

    root_summary = Path("SUMMARY.md").read_text(encoding="utf-8")
    assert "docs/executive/enterprise-observability-proposal.md" in root_summary

    llms_txt = Path("llms.txt").read_text(encoding="utf-8")
    assert "docs/executive/enterprise-observability-proposal.md" in llms_txt
