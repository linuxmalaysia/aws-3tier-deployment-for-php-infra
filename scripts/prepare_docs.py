#!/usr/bin/env python3
import os
import re
import subprocess
import datetime

# Pre-compile the regex pattern for finding the first heading
HEADING_PATTERN = re.compile(r'^\s*#+\s+(.+)$', re.MULTILINE)

# Map filenames or directories to specific OKF "type" values
def infer_okf_type(filepath):
    filename = os.path.basename(filepath).lower()
    rel_path = os.path.relpath(filepath, start=os.path.dirname(os.path.dirname(__file__))).lower()

    if filename == "changelog.md":
        return "Changelog"
    elif filename == "history.md":
        return "History"
    elif filename == "readme.md":
        return "Portal"
    elif filename == "agents.md":
        return "Agent Operating Instructions"
    elif filename == "skill.md":
        return "Agent Skill"
    elif "terraform/modules" in filepath.replace('\\', '/'):
        return "Module README"
    elif "docs/modules" in filepath.replace('\\', '/'):
        return "Module Technical Guide"
    elif "docs/" in filepath.replace('\\', '/'):
        if filename == "index.md":
            return "Documentation Index"
        return "Technical Reference Guide"
    return "Technical Documentation"

# Map filenames or directories to specific OKF "topics" lists
def infer_okf_topics(filepath, current_topics_or_tags=None):
    if current_topics_or_tags and isinstance(current_topics_or_tags, list) and len(current_topics_or_tags) > 0:
        return current_topics_or_tags

    filename = os.path.basename(filepath).lower()
    topics = ["aws", "3-tier"]

    if "vpc" in filename:
        topics.extend(["vpc", "networking"])
    elif "security_groups" in filename or "waf" in filename:
        topics.extend(["security", "firewall"])
    elif "rds" in filename or "postgresql" in filename:
        topics.extend(["database", "rds"])
    elif "elasticache" in filename or "valkey" in filename:
        topics.extend(["caching", "valkey"])
    elif "asg" in filename:
        topics.extend(["compute", "autoscaling"])
    elif "jumphost" in filename or "bastion" in filename:
        topics.extend(["security", "bastion"])
    elif "cost" in filename:
        topics.extend(["finops", "costing"])
    elif "cicd" in filename or "gitlab" in filename:
        topics.extend(["cicd", "automation"])
    elif "migration" in filename or "opentofu" in filename:
        topics.extend(["opentofu", "migration"])
    elif "agent" in filename or "skill" in filename:
        topics.extend(["ai-agents", "instructions"])
    elif "php" in filename or "codeigniter" in filename:
        topics.extend(["php", "codeigniter"])

    # Remove duplicates
    seen = set()
    return [x for x in topics if not (x in seen or seen.add(x))]

def get_git_timestamp(filepath):
    try:
        # Get the commit ISO timestamp for the file
        timestamp_str = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", filepath],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        if timestamp_str:
            return timestamp_str
    except Exception:
        pass

    # Fallback to current modified time in ISO format
    try:
        mtime = os.path.getmtime(filepath)
        return datetime.datetime.fromtimestamp(mtime).isoformat()
    except Exception:
        return datetime.datetime.now().isoformat()

def parse_yaml_front_matter(fm_text):
    """
    Very basic YAML parser that doesn't require PyYAML.
    Only supports top-level key-value pairs (strings, booleans, list of strings/scalars).
    Handles format like key: "value", key: value, key: [a, b, c], or key: - a \n - b
    """
    data = {}
    lines = fm_text.splitlines()
    current_key = None
    list_mode = False

    for line in lines:
        if not line.strip() or line.strip().startswith('#'):
            continue

        # Check for list items
        if line.strip().startswith('-') and current_key:
            val = line.strip().lstrip('-').strip().strip('"').strip("'")
            if current_key not in data or not isinstance(data[current_key], list):
                data[current_key] = []
            data[current_key].append(val)
            continue

        match = re.match(r'^([^:]+):\s*(.*)$', line)
        if match:
            current_key = match.group(1).strip()
            val = match.group(2).strip()

            # Reset list mode
            list_mode = False

            if not val:
                # Might be starting a list on next lines
                data[current_key] = []
            elif val.startswith('[') and val.endswith(']'):
                # Inline YAML array like [a, b]
                items = [x.strip().strip('"').strip("'") for x in val[1:-1].split(',')]
                data[current_key] = [x for x in items if x]
            else:
                # Scalar value
                # Strip quotes
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]

                # Try conversions
                if val.lower() == 'true':
                    val = True
                elif val.lower() == 'false':
                    val = False
                data[current_key] = val

    return data

def format_yaml_front_matter(data):
    lines = ["---"]
    # Ensure layout always comes first if it exists
    if "layout" in data:
        lines.append(f"layout: {data['layout']}")

    # Required OKF v0.1 fields
    lines.append(f"okf_version: \"{data.get('okf_version', '0.1')}\"")
    lines.append(f"type: {data.get('type', 'Technical Documentation')}")

    # Title format
    title = data.get('title', '')
    if '"' in title or "'" in title:
        lines.append(f"title: {title}")
    else:
        lines.append(f"title: \"{title}\"")

    lines.append(f"timestamp: {data.get('timestamp', '')}")

    topics = data.get('topics', [])
    if isinstance(topics, list):
        topics_str = ", ".join(topics)
        lines.append(f"topics: [{topics_str}]")
    else:
        lines.append(f"topics: {topics}")

    # Write other existing fields
    for k, v in sorted(data.items()):
        if k in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
            continue
        if isinstance(v, list):
            v_str = ", ".join(v)
            lines.append(f"{k}: [{v_str}]")
        elif isinstance(v, bool):
            lines.append(f"{k}: {str(v).lower()}")
        else:
            if isinstance(v, str) and ('"' in v or "'" in v):
                lines.append(f"{k}: {v}")
            elif isinstance(v, str):
                lines.append(f"{k}: \"{v}\"")
            else:
                lines.append(f"{k}: {v}")

    lines.append("---")
    return "\n".join(lines)

def process_markdown_file(filepath):
    print(f"Processing: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if the file already has front matter
    has_front_matter = False
    stripped_content = content.lstrip()
    if stripped_content.startswith('---'):
        has_front_matter = True

    # Extract or infer baseline front matter fields
    title = None
    heading_match = HEADING_PATTERN.search(content)
    if heading_match:
        title = heading_match.group(1).strip()
        # Clean markdown bold/italic tags from title if present
        title = title.replace('**', '').replace('*', '').replace('`', '')
    else:
        filename = os.path.basename(filepath)
        name_without_ext, _ = os.path.splitext(filename)
        title = name_without_ext.replace('_', ' ').replace('-', ' ').title()

    timestamp = get_git_timestamp(filepath)
    okf_type = infer_okf_type(filepath)
    okf_topics = infer_okf_topics(filepath)

    if not has_front_matter:
        # Build completely new front matter block
        fm_data = {
            "layout": "default",
            "okf_version": "0.1",
            "type": okf_type,
            "title": title,
            "timestamp": timestamp,
            "topics": okf_topics
        }

        # Exception for files outside of docs folder (like README.md, AGENTS.md, etc.) which might not need "layout"
        # However, it doesn't hurt, but if it's outside docs, we can keep layout: default or omit it. Let's keep layout for jekyll.
        # But for non-docs, maybe layout isn't strictly needed. Let's just keep it for consistency.

        new_fm_text = format_yaml_front_matter(fm_data)
        new_content = new_fm_text + "\n\n" + content

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  -> Added OKF front matter with title: '{title}'")
    else:
        # Parse and merge with existing front matter
        parts = stripped_content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body_text = parts[2]

            existing_data = parse_yaml_front_matter(fm_text)

            # Map existing tags/topics
            tags_or_topics = existing_data.get('topics') or existing_data.get('tags')
            final_topics = infer_okf_topics(filepath, tags_or_topics)

            fm_data = {
                "layout": existing_data.get("layout", "default"),
                "okf_version": existing_data.get("okf_version", "0.1"),
                "type": existing_data.get("type", okf_type),
                "title": existing_data.get("title", title),
                "timestamp": existing_data.get("timestamp", timestamp),
                "topics": final_topics
            }

            # Preserve all other keys
            for k, v in existing_data.items():
                if k not in fm_data and k != 'tags':
                    fm_data[k] = v

            new_fm_text = format_yaml_front_matter(fm_data)
            new_content = new_fm_text + body_text

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  -> Updated OKF front matter for: '{title}'")

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print(f"Scanning and processing all markdown files under: {repo_root}")

    for root, _, files in os.walk(repo_root):
        # Skip directories like .git
        if '.git' in root.split(os.sep):
            continue

        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                process_markdown_file(filepath)

if __name__ == '__main__':
    main()
