#!/usr/bin/env python3
"""
Python API, CLI, and automatic asset generator for llms.txt and llms-full.txt.
Provides functions to parse llms.txt, compile full documentation into llms-full.txt,
and create XML context files.
"""

import os
import re
import sys
import argparse

class AttrDict(dict):
    """A dictionary subclass that allows attribute-style access."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'AttrDict' object has no attribute '{name}'")
    def __setattr__(self, name, value):
        self[name] = value

def strip_front_matter(content):
    """Strip OKF/Jekyll front matter (starts with ---) from markdown content."""
    stripped = content.lstrip()
    if stripped.startswith('---'):
        parts = stripped.split('---', 2)
        if len(parts) >= 3:
            return parts[2].lstrip()
    return content

def parse_llms_file(txt):
    """
    Parse llms.txt file contents in `txt` and return an AttrDict
    with fields: title, summary, info, sections.
    """
    # Normalize line endings
    txt = txt.replace('\r\n', '\n')

    # Split text by H2 headers
    parts = re.split(r'^##\s*(.*?)$', txt, flags=re.MULTILINE)

    start_block = parts[0]
    rest = parts[1:]

    # Parse H1 title
    title_match = re.search(r'^#\s*(.*?)$', start_block, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else ""

    # Extract summary (blockquote >) and introduction info
    summary_lines = []
    info_lines = []

    for line in start_block.split('\n'):
        line_stripped = line.strip()
        if line_stripped.startswith('#'):
            continue
        elif line_stripped.startswith('>'):
            summary_lines.append(line_stripped.lstrip('>').strip())
        else:
            if line_stripped or info_lines:
                info_lines.append(line)

    summary = "\n".join(summary_lines).strip()
    info = "\n".join(info_lines).strip()

    # Parse H2 sections and their link lists
    sections = AttrDict()
    for i in range(0, len(rest), 2):
        if i + 1 >= len(rest):
            break
        header = rest[i].strip()
        links_block = rest[i+1].strip()

        links = []
        for line in links_block.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Match standard link pattern: - [title](url) : desc or - [title](url) : desc
            m = re.match(r'-\s*\[([^\]]+)\]\(([^)]+)\)(?:\s*:\s*(.*))?', line)
            if m:
                link_title = m.group(1).strip()
                link_url = m.group(2).strip()
                link_desc = m.group(3).strip() if m.group(3) else None
                links.append({
                    'title': link_title,
                    'url': link_url,
                    'desc': link_desc
                })
        sections[header] = links

    return AttrDict({
        'title': title,
        'summary': summary,
        'info': info,
        'sections': sections
    })

# Define alias for flexibility/compatibility
parse_llms_txt = parse_llms_file

def escape_xml_text(val):
    """Escape text for XML safely."""
    if val is None:
        return ""
    return (str(val)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))

def create_ctx(txt, optional=False, base_dir=None):
    """
    Create XML context output for LLMs from llms.txt content.
    If optional is False, the 'Optional' section (case-insensitive) is skipped.
    """
    parsed = parse_llms_file(txt)

    xml_parts = []
    title_esc = escape_xml_text(parsed.title)
    summary_esc = escape_xml_text(parsed.summary)

    xml_parts.append(f'<project title="{title_esc}" summary="{summary_esc}">')
    if parsed.info:
        xml_parts.append(escape_xml_text(parsed.info))
        xml_parts.append("")

    for sect_title, links in parsed.sections.items():
        if not optional and sect_title.lower() == 'optional':
            continue

        xml_parts.append(f'<section title="{escape_xml_text(sect_title)}">')
        for link in links:
            url = link['url']
            title = link['title']
            desc = link['desc']
            desc_attr = f' desc="{escape_xml_text(desc)}"' if desc else ''

            content = ""
            if not url.startswith('http://') and not url.startswith('https://'):
                file_path = os.path.join(base_dir, url) if base_dir else url
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            raw_md = f.read()
                        content = strip_front_matter(raw_md)
                    except Exception as e:
                        content = f"Error reading file {file_path}: {str(e)}"
                else:
                    content = f"File {file_path} not found."
            else:
                content = f"External document: {url}"

            xml_parts.append(f'<document title="{escape_xml_text(title)}" url="{escape_xml_text(url)}"{desc_attr}>')
            xml_parts.append(escape_xml_text(content.strip()))
            xml_parts.append('</document>')

        xml_parts.append('</section>')

    xml_parts.append('</project>')
    return "\n".join(xml_parts)

def compile_llms_full(txt, base_dir=None):
    """
    Compile all documentation contents listed in llms.txt into a single Markdown file.
    """
    parsed = parse_llms_file(txt)
    compiled_parts = []

    compiled_parts.append(f"# {parsed.title}")
    compiled_parts.append("")
    if parsed.summary:
        compiled_parts.append(f"> {parsed.summary}")
        compiled_parts.append("")
    if parsed.info:
        compiled_parts.append(parsed.info)
        compiled_parts.append("")

    compiled_parts.append("---")
    compiled_parts.append("")

    for sect_title, links in parsed.sections.items():
        compiled_parts.append(f"# Section: {sect_title}")
        compiled_parts.append("")
        for link in links:
            url = link['url']
            title = link['title']
            desc = link['desc']

            compiled_parts.append(f"## {title}")
            if desc:
                compiled_parts.append(f"*{desc}*")
                compiled_parts.append("")

            if not url.startswith('http://') and not url.startswith('https://'):
                file_path = os.path.join(base_dir, url) if base_dir else url
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            raw_md = f.read()
                        content = strip_front_matter(raw_md).strip()
                        compiled_parts.append(content)
                    except Exception as e:
                        compiled_parts.append(f"*Error reading file {file_path}: {str(e)}*")
                else:
                    compiled_parts.append(f"*File {file_path} not found.*")
            else:
                compiled_parts.append(f"External document: [{title}]({url})")

            compiled_parts.append("")
            compiled_parts.append("---")
            compiled_parts.append("")

    return "\n".join(compiled_parts)

def generate_all():
    """Automatic generator for this repository's llms-full.txt and llms-context.xml."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    docs_dir = os.path.join(repo_root, "docs")

    llms_txt_path = os.path.join(repo_root, "llms.txt")
    if not os.path.exists(llms_txt_path):
        print(f"Error: {llms_txt_path} not found.", file=sys.stderr)
        sys.exit(1)

    with open(llms_txt_path, "r", encoding="utf-8") as f:
        llms_content = f.read()

    print("Generating llms-full.txt...")
    full_content = compile_llms_full(llms_content, base_dir=repo_root)

    print("Generating llms-context.xml...")
    xml_context = create_ctx(llms_content, optional=True, base_dir=repo_root)

    # Write to repository root
    with open(os.path.join(repo_root, "llms-full.txt"), "w", encoding="utf-8") as f:
        f.write(full_content)
    with open(os.path.join(repo_root, "llms-context.xml"), "w", encoding="utf-8") as f:
        f.write(xml_context)

    # Write to docs/ directory
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, "llms-full.txt"), "w", encoding="utf-8") as f:
        f.write(full_content)
    with open(os.path.join(docs_dir, "llms-context.xml"), "w", encoding="utf-8") as f:
        f.write(xml_context)

    print("Assets successfully generated in repository root and docs/!")

if __name__ == '__main__':
    # If there are arguments (other than the script name itself), run as CLI
    if len(sys.argv) > 1 and sys.argv[1] not in ["--help", "-h"]:
        parser = argparse.ArgumentParser(description="Parse llms.txt and create XML context file.")
        parser.add_argument("input_file", help="Path to llms.txt file")
        parser.add_argument("--optional", type=str, default="False", help="Include 'optional' sections? (True/False)")
        args = parser.parse_args()

        opt_val = args.optional.lower() in ["true", "1", "yes", "t"]

        try:
            with open(args.input_file, "r", encoding="utf-8") as f:
                content = f.read()
            base_dir = os.path.dirname(args.input_file)
            xml_ctx = create_ctx(content, optional=opt_val, base_dir=base_dir)
            print(xml_ctx)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Help message if specifically requested
        if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
            print("Usage: python3 generate_llms_assets.py [input_file] [--optional True/False]")
            print("If run without arguments, generates llms-full.txt and llms-context.xml for this repo.")
            sys.exit(0)
        # Default behavior
        generate_all()
