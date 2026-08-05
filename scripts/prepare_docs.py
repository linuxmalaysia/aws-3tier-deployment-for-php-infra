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

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    rel_path = os.path.relpath(filepath, repo_root).replace('\\', '/').lower()

    topics = ["aws", "3-tier"]

    # Deriving matching keywords from the relative path or parent directory
    if "vpc" in rel_path:
        topics.extend(["vpc", "networking"])
    elif "security_groups" in rel_path or "waf" in rel_path:
        topics.extend(["security", "firewall"])
    elif "rds" in rel_path or "postgresql" in rel_path:
        topics.extend(["database", "rds"])
    elif "elasticache" in rel_path or "valkey" in rel_path:
        topics.extend(["caching", "valkey"])
    elif "asg" in rel_path:
        topics.extend(["compute", "autoscaling"])
    elif "jumphost" in rel_path or "bastion" in rel_path:
        topics.extend(["security", "bastion"])
    elif "cost" in rel_path:
        topics.extend(["finops", "costing"])
    elif "cicd" in rel_path or "gitlab" in rel_path:
        topics.extend(["cicd", "automation"])
    elif "migration" in rel_path or "opentofu" in rel_path:
        topics.extend(["opentofu", "migration"])
    elif "agent" in rel_path or "skill" in rel_path:
        topics.extend(["ai-agents", "instructions"])
    elif "php" in rel_path or "codeigniter" in rel_path:
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

def process_front_matter_structure_preserving(fm_text, filepath, title_fallback, timestamp_fallback, okf_type_fallback, okf_topics_fallback):
    lines = fm_text.splitlines()
    key_line_map = {}
    current_key = None

    for i, line in enumerate(lines):
        match = re.match(r'^([a-zA-Z0-9_-]+):\s*(.*)$', line)
        if match:
            if current_key is not None:
                key_line_map[current_key]['end_line'] = i - 1
            current_key = match.group(1)
            val = match.group(2).strip()

            if val.startswith('[') and val.endswith(']'):
                parsed_val = [x.strip().strip('"').strip("'") for x in val[1:-1].split(',')]
                parsed_val = [x for x in parsed_val if x]
            else:
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    parsed_val = val[1:-1]
                else:
                    parsed_val = val

            key_line_map[current_key] = {
                'start_line': i,
                'end_line': i,
                'value': parsed_val,
                'raw_val': val
            }
        elif current_key is not None:
            key_line_map[current_key]['end_line'] = i
            if line.strip().startswith('-'):
                item_val = line.strip().lstrip('-').strip().strip('"').strip("'")
                if not isinstance(key_line_map[current_key]['value'], list):
                    key_line_map[current_key]['value'] = []
                key_line_map[current_key]['value'].append(item_val)

    if current_key is not None:
        key_line_map[current_key]['end_line'] = len(lines) - 1

    # Extract layout
    layout_val = "default"
    if "layout" in key_line_map:
        layout_val = key_line_map["layout"]["value"]

    # Required OKF v0.1 fields
    okf_version_val = "0.1"
    if "okf_version" in key_line_map:
        okf_version_val = key_line_map["okf_version"]["value"]

    type_val = okf_type_fallback
    if "type" in key_line_map:
        type_val = key_line_map["type"]["value"]

    title_val = title_fallback
    if "title" in key_line_map:
        title_val = key_line_map["title"]["value"]

    timestamp_val = timestamp_fallback
    if "timestamp" in key_line_map:
        timestamp_val = key_line_map["timestamp"]["value"]

    topics_val = okf_topics_fallback
    existing_topics = None
    if "topics" in key_line_map:
        existing_topics = key_line_map["topics"]["value"]
        if isinstance(existing_topics, str):
            existing_topics = [existing_topics]
    elif "tags" in key_line_map:
        existing_topics = key_line_map["tags"]["value"]
        if isinstance(existing_topics, str):
            existing_topics = [existing_topics]

    if existing_topics:
        topics_val = infer_okf_topics(filepath, existing_topics)

    # Reconstruct preserving spacing/nested entries
    skip_lines = set()
    for k in ["layout", "okf_version", "type", "title", "timestamp", "topics", "tags"]:
        if k in key_line_map:
            for idx in range(key_line_map[k]['start_line'], key_line_map[k]['end_line'] + 1):
                skip_lines.add(idx)

    preserved_lines = []
    for idx, line in enumerate(lines):
        if idx not in skip_lines:
            preserved_lines.append(line)

    final_lines = []
    final_lines.append(f"layout: {layout_val}")
    final_lines.append(f"okf_version: \"{okf_version_val}\"")
    final_lines.append(f"type: {type_val}")

    if '"' in title_val or "'" in title_val:
        final_lines.append(f"title: {title_val}")
    else:
        final_lines.append(f"title: \"{title_val}\"")

    final_lines.append(f"timestamp: {timestamp_val}")

    topics_str = ", ".join(topics_val)
    final_lines.append(f"topics: [{topics_str}]")

    for line in preserved_lines:
        if line.strip():
            final_lines.append(line)

    return "---\n" + "\n".join(final_lines) + "\n---"

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

        new_fm_text = format_yaml_front_matter(fm_data)

        # Validate serialized front matter before writing
        validated_fm = parse_yaml_front_matter(new_fm_text.strip("-\n"))
        for key in ["okf_version", "type", "title", "timestamp", "topics"]:
            if key not in validated_fm:
                raise ValueError(f"Validation failed: {key} missing in serialized front matter of {filepath}")

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

            new_fm_text = process_front_matter_structure_preserving(
                fm_text, filepath, title, timestamp, okf_type, okf_topics
            )

            # Validate serialized front matter before writing
            validated_fm = parse_yaml_front_matter(new_fm_text.strip("-\n"))
            for key in ["okf_version", "type", "title", "timestamp", "topics"]:
                if key not in validated_fm:
                    raise ValueError(f"Validation failed: {key} missing in serialized front matter of {filepath}")

            new_content = new_fm_text + body_text

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  -> Updated OKF front matter for: '{title}'")

    # Verify with a read-only check
    with open(filepath, 'r', encoding='utf-8') as verify_f:
        verified_content = verify_f.read()
    if not verified_content.startswith('---'):
        raise ValueError(f"Read-only check failed: {filepath} does not start with front matter marker")

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print(f"Scanning and processing all markdown files under: {repo_root}")

    for root, dirs, files in os.walk(repo_root):
        # Prune generated and cache directory names in-place
        dirs[:] = [d for d in dirs if d not in ['.git', '.terraform', 'dist', 'build', '_site']]

        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                # Skip symlinked files
                if os.path.islink(filepath):
                    continue
                # Resolve candidate path
                resolved_path = os.path.realpath(filepath)

                # Double-check that we are not in any of the excluded directories
                path_parts = [p.lower() for p in resolved_path.replace('\\', '/').split('/')]
                if any(d in path_parts for d in ['.git', '.terraform', 'dist', 'build', '_site']):
                    continue

                # Verify resolved path remains within repo_root
                try:
                    rel = os.path.relpath(resolved_path, repo_root)
                    if (rel.startswith('..') or os.path.isabs(rel)) and not resolved_path.startswith('/repo'):
                        continue
                except ValueError:
                    continue

                process_markdown_file(resolved_path)

if __name__ == '__main__':
    main()
