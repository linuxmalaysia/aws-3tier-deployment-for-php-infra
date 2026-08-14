#!/usr/bin/env python3
"""Sitemap, Robots.txt, and RFC 9116 security.txt Generator.

This utility automates crawling the docs/ directory and root Markdown files
and compiling XML/TXT sitemaps, robots.txt, and .well-known/security.txt
consistently.
"""

import os
import re
import subprocess
import datetime
import xml.etree.ElementTree as ET

EXISTING_LASTMODS = {}


def load_existing_lastmods():
    """Load existing lastmod dates from the already-committed sitemap.xml.

    This preserves historical dates in CI environments where author dates might
    differ on shallow merges or fresh checkouts.
    """
    global EXISTING_LASTMODS
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sitemap_xml_path = os.path.join(repo_root, "sitemap.xml")
    if os.path.exists(sitemap_xml_path):
        try:
            tree = ET.parse(sitemap_xml_path)
            root = tree.getroot()
            ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
            for url_node in root.findall(f"{ns}url"):
                loc_node = url_node.find(f"{ns}loc")
                lastmod_node = url_node.find(f"{ns}lastmod")
                if loc_node is not None and lastmod_node is not None:
                    loc = loc_node.text.strip()
                    lastmod = lastmod_node.text.strip()
                    EXISTING_LASTMODS[loc] = lastmod
        except Exception:
            pass


def get_git_timestamp(filepath):
    """Retrieve the latest Git committer timestamp when available.

    If Git is not initialized or the file has not been committed, this function
    falls back to using the repository's latest commit date, then the filesystem
    modification time (mtime), or today's date if all else fails.

    Args:
        filepath (str): The absolute or relative path to the file.

    Returns:
        str: A date string formatted as YYYY-MM-DD.
    """
    try:
        timestamp_str = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", filepath],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        if timestamp_str:
            # We can extract just the date part (YYYY-MM-DD) for sitemap.xml
            return timestamp_str.split("T")[0]
    except Exception:
        pass

    # Fallback to the latest commit date of the repository
    try:
        timestamp_str = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        if timestamp_str:
            return timestamp_str.split("T")[0]
    except Exception:
        pass

    # Fallback to mtime
    try:
        mtime = os.path.getmtime(filepath)
        return datetime.date.fromtimestamp(mtime).isoformat()
    except Exception:
        return datetime.date.today().isoformat()


def get_dir_priority(d: str) -> tuple[int, str]:
    """Retrieve sorting priority for traversed directories.

    Prioritizes 'executive' directory first, 'engineering' directory second, and
    all other directories afterward, ensuring deterministic and stable sitemap
    generation.

    Args:
        d (str): The directory name.

    Returns:
        tuple[int, str]: A tuple of priority level (lower is higher priority) and
            the directory name itself.
    """
    if d == "executive":
        return (0, d)
    if d == "engineering":
        return (1, d)
    return (2, d)


def discover_markdown_files(docs_dir):
    """Crawl the docs directory to find all relative paths to Markdown files.

    Args:
        docs_dir (str): The docs/ directory path.

    Returns:
        list[str]: Discovered relative Markdown file paths.
    """
    discovered_rel_paths = []
    for root, dirs, files in os.walk(docs_dir):
        # Ignore system/jekyll specific folders
        dirs[:] = [d for d in dirs if d not in ["_layouts", "assets", ".well-known"]]

        # Sort dirs so that 'executive' is traversed first, 'engineering' second
        dirs.sort(key=get_dir_priority)

        # Sort files alphabetically
        files.sort()

        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, docs_dir).replace('\\', '/')
                if rel_path.lower() != "index.md":
                    discovered_rel_paths.append(rel_path)
    return discovered_rel_paths


def sort_relative_paths(discovered_rel_paths):
    """Sort relative documentation paths according to standard sequence indexes.

    Args:
        discovered_rel_paths (list[str]): Unsorted relative Markdown paths.

    Returns:
        list[str]: Standardized sorted relative documentation paths.
    """
    original_order = [
        "aws-vs-self-hosted-review.md",
        "legal-notice.md",
        "executive/hybrid-onprem.md",
        "executive/costing.md",
        "executive/production-costing.md",
        "executive/aws-adoption-roadmap.md",
        "executive/dr-options.md",
        "executive/dr-options-evaluation.md",
        "executive/dr-option-two-malaysia.md",
        "engineering/aws-vs-onprem-comparison.md",
        "engineering/developer-design-mapping.md",
        "engineering/cicd.md",
        "engineering/postgresql-comparison.md",
        "engineering/SOP-KNOWLEDGE-FIRST-DISCOVERY.md",
        "engineering/aws-cli-guide.md",
        "engineering/asimp-output.md",
        "engineering/root-files.md",
        "engineering/route53.md",
        "engineering/openscap-output.md",
        "engineering/lynis-output.md",
        "engineering/codeigniter-php-fpm.md",
        "engineering/opentofu-migration.md",
        "engineering/asimp-for-ai-agents.md",
        "engineering/jumphost.md",
        "engineering/security-posture-assessment.md",
        "engineering/scripts.md",
        "engineering/performance-testing.md",
        "engineering/ami-design.md",
        "engineering/asg-separation-of-concern.md",
        "engineering/performance-analysis.md",
        "engineering/architecture.md",
        "engineering/github-detach-fork.md",
        "engineering/ragflow-langfuse.md",
        "engineering/gitlab-efs-cicd.md",
        "engineering/modules/standalone_ec2.md",
        "engineering/modules/alb.md",
        "engineering/modules/asg.md",
        "engineering/modules/rds.md",
        "engineering/modules/vpc.md",
        "engineering/modules/jumphost.md",
        "engineering/modules/elasticache.md",
        "engineering/modules/waf.md",
        "engineering/modules/security_groups.md",
        "engineering/modules/fusio.md"
    ]
    original_order_map = {path: idx for idx, path in enumerate(original_order)}

    def get_path_sort_key(p):
        p_norm = p.replace('\\', '/')
        if p_norm in original_order_map:
            return (0, original_order_map[p_norm], p_norm)
        else:
            # Group new folders after existing ones
            parts = p_norm.split('/')
            dir_name = parts[0] if len(parts) > 1 else ""
            if len(parts) > 2 and parts[0] == "engineering" and parts[1] == "modules":
                dir_name = "engineering/modules"

            dir_order = ["", "executive", "engineering", "engineering/modules", "explanation", "how-to", "reference", "tutorials"]
            try:
                dir_idx = dir_order.index(dir_name)
            except ValueError:
                dir_idx = len(dir_order)
            return (1, dir_idx, p_norm)

    return sorted(discovered_rel_paths, key=get_path_sort_key)


def generate_sitemap_urls(discovered_rel_paths, gh_base, gb_base, docs_dir, repo_root):
    """Generate the structured GitHub Pages and GitBook URL arrays.

    Args:
        discovered_rel_paths (list[str]): Sorted relative paths.
        gh_base (str): Base URL of GitHub Pages.
        gb_base (str): Base URL of GitBook.
        docs_dir (str): Docs directory.
        repo_root (str): Repository root directory.

    Returns:
        tuple[list[dict], list[str]]: GitHub Pages URL objects, and GitBook URL list.
    """
    gh_urls = []
    gb_urls = []

    # Homepage mapping to docs/index.md
    index_path = os.path.join(docs_dir, "index.md")
    index_date = get_git_timestamp(index_path)

    gh_urls.append({
        "url": f"{gh_base}/",
        "lastmod": index_date,
        "priority": "1.0",
        "changefreq": "weekly"
    })
    gb_urls.append(f"{gb_base}/")

    # Relative paths
    for rel_path in discovered_rel_paths:
        filepath = os.path.join(docs_dir, rel_path)

        url_path = rel_path[:-3] + ".html"
        gh_url = f"{gh_base}/{url_path}"
        gb_url = f"{gb_base}/docs/{rel_path[:-3]}"

        lastmod = get_git_timestamp(filepath)

        priority = "0.8" if "/" not in rel_path else "0.6"

        gh_urls.append({
            "url": gh_url,
            "lastmod": lastmod,
            "priority": priority,
            "changefreq": "weekly"
        })
        gb_urls.append(gb_url)

    # Generated PDF assets if present
    pdf_path = os.path.join(docs_dir, "assets", "output.pdf")
    if os.path.exists(pdf_path):
        pdf_date = get_git_timestamp(pdf_path)
        pdf_url = f"{gh_base}/assets/output.pdf"

        gh_urls.append({
            "url": pdf_url,
            "lastmod": pdf_date,
            "priority": "0.5",
            "changefreq": "monthly"
        })

    # Root Markdown files for GitBook
    root_mds = ["README.md", "AGENTS.md", "CHANGELOG.md", "HISTORY.md"]
    for f in root_mds:
        p = os.path.join(repo_root, f)
        if os.path.exists(p):
            name = os.path.splitext(f)[0].lower()
            if name == "readme":
                continue
            gb_urls.append(f"{gb_base}/{name}")

    return gh_urls, gb_urls


def write_sitemap_files(repo_root, docs_dir, gh_urls, gb_urls, gh_base):
    """Write sitemap.txt, sitemap.xml, robots.txt, and security.well-known.

    Args:
        repo_root (str): The repository root path.
        docs_dir (str): The docs/ path.
        gh_urls (list[dict]): GitHub Pages URL objects.
        gb_urls (list[str]): GitBook URL list.
        gh_base (str): Base URL of GitHub Pages.
    """
    # Remove any duplicates while preserving order
    unique_gb_urls = []
    for u in gb_urls:
        if u not in unique_gb_urls:
            unique_gb_urls.append(u)

    # Combine lists for sitemap.txt
    all_txt_urls = [u["url"] for u in gh_urls] + unique_gb_urls

    # Write sitemap.txt
    sitemap_txt_content = "\n".join(all_txt_urls) + "\n"

    with open(os.path.join(repo_root, "sitemap.txt"), "w", encoding="utf-8") as f:
        f.write(sitemap_txt_content)
    with open(os.path.join(docs_dir, "sitemap.txt"), "w", encoding="utf-8") as f:
        f.write(sitemap_txt_content)

    print(f"Generated sitemap.txt with {len(all_txt_urls)} URLs.")

    # Write sitemap.xml
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for item in gh_urls:
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{item['url']}</loc>")
        xml_lines.append(f"    <lastmod>{item['lastmod']}</lastmod>")
        xml_lines.append(f"    <changefreq>{item['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{item['priority']}</priority>")
        xml_lines.append("  </url>")
    xml_lines.append("</urlset>")

    sitemap_xml_content = "\n".join(xml_lines) + "\n"

    with open(os.path.join(repo_root, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_xml_content)
    with open(os.path.join(docs_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap_xml_content)

    print(f"Generated sitemap.xml with {len(gh_urls)} URLs.")

    # Generate robots.txt
    robots_content = f"""User-agent: *
Allow: /

Sitemap: {gh_base}/sitemap.xml
"""
    with open(os.path.join(repo_root, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots_content)
    with open(os.path.join(docs_dir, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots_content)

    print("Generated robots.txt.")

    # Generate .well-known/security.txt
    os.makedirs(os.path.join(repo_root, ".well-known"), exist_ok=True)
    os.makedirs(os.path.join(docs_dir, ".well-known"), exist_ok=True)

    security_content = f"""# RFC 9116 - Security Contact Information
Contact: mailto:contact@linuxmalaysia.com
Preferred-Languages: en, ms
Canonical: {gh_base}/.well-known/security.txt
"""
    with open(os.path.join(repo_root, ".well-known", "security.txt"), "w", encoding="utf-8") as f:
        f.write(security_content)
    with open(os.path.join(docs_dir, ".well-known", "security.txt"), "w", encoding="utf-8") as f:
        f.write(security_content)

    print("Generated .well-known/security.txt.")


def main():
    """Main function coordinating sitemap generation."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    docs_dir = os.path.join(repo_root, "docs")

    gh_base = "https://linuxmalaysia.github.io/aws-3tier-deployment-for-php-infra"
    gb_base = "https://linuxmalaysia.gitbook.io/aws-3tier-deployment-for-php-infra"

    # Step 1: Discover relative paths
    discovered_rel_paths = discover_markdown_files(docs_dir)

    # Step 2: Sort relative paths
    sorted_rel_paths = sort_relative_paths(discovered_rel_paths)

    # Step 3: Generate URL objects
    gh_urls, gb_urls = generate_sitemap_urls(sorted_rel_paths, gh_base, gb_base, docs_dir, repo_root)

    # Step 4: Write all output sitemaps and security files
    write_sitemap_files(repo_root, docs_dir, gh_urls, gb_urls, gh_base)


if __name__ == "__main__":
    main()
