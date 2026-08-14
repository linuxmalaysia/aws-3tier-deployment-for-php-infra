#!/usr/bin/env python3
import os
import re
import subprocess
import datetime

# Pre-compile the regex pattern for finding the first heading
HEADING_PATTERN = re.compile(r'^\s*#+\s+(.+)$', re.MULTILINE)

def infer_okf_type(filepath):
    """Infer the Open Knowledge Format (OKF) 'type' attribute based on file path.

    Args:
        filepath (str): Path of the file to classify.

    Returns:
        str: Classified OKF documentation type string.
    """
    filename = os.path.basename(filepath).lower()
    parts = filepath.replace('\\', '/').split('/')

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
    elif any(parts[i] == "docs" and parts[i+1] == "modules" for i in range(len(parts) - 1)) or any(parts[i] == "docs" and parts[i+1] == "engineering" and parts[i+2] == "modules" for i in range(len(parts) - 2)):
        return "Module Technical Guide"
    elif "docs/" in filepath.replace('\\', '/'):
        if filename == "index.md":
            return "Documentation Index"
        return "Technical Reference Guide"
    return "Technical Documentation"


def infer_okf_topics(filepath, current_topics_or_tags=None):
    """Infer appropriate OKF topics based on folder hierarchy and filename keywords.

    If a non-empty `current_topics_or_tags` list is provided, it is returned unchanged,
    without inferring additional topics or removing duplicates. Otherwise, topics are
    inferred from the directory structure and filename keywords.

    Args:
        filepath (str): Path of the markdown document.
        current_topics_or_tags (list[str], optional): Pre-existing topics to
            preserve. Defaults to None.

    Returns:
        list[str]: The unchanged pre-existing list if non-empty; otherwise, a merged
            list of unique inferred topic string keywords.
    """
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
    """Retrieve the latest Git committer timestamp when available.

    If Git is not initialized or the file has not been committed, this function
    falls back to the repository's latest commit timestamp, then the filesystem
    modification time (mtime), and finally the current system time if all else fails.

    Args:
        filepath (str): Absolute or relative path to the file.

    Returns:
        str: ISO-8601 formatted timestamp string.
    """
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

    # Fallback to latest commit ISO timestamp of the repository
    try:
        timestamp_str = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI"],
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


def escape_yaml_double_quoted_scalar(val):
    """Escape backslashes, double quotes, and specific control characters.

    If the input is not a string, returns unquoted `str(val)`. Otherwise, escaping
    is applied to backslashes, double quotes, and specific control characters (\\n,
    \\t, \\r, \\b, \\f), wrapping the escaped string in double quotes.

    Args:
        val (any): The input value to escape.

    Returns:
        str: The unquoted string representation for non-string inputs; otherwise,
            a double-quoted string with specific character escaping applied.
    """
    if not isinstance(val, str):
        return str(val)
    # Double-quoted YAML scalars escape backslashes, quotes, and control characters
    escaped = val.replace('\\', '\\\\')
    escaped = escaped.replace('"', '\\"')
    escaped = escaped.replace('\n', '\\n')
    escaped = escaped.replace('\t', '\\t')
    escaped = escaped.replace('\r', '\\r')
    escaped = escaped.replace('\b', '\\b')
    escaped = escaped.replace('\f', '\\f')
    return f'"{escaped}"'


def format_string_value(val):
    """Format an arbitrary scalar value as a safe, unquoted or quoted YAML string.

    Args:
        val (any): A primitive value to format.

    Returns:
        str: Correctly formatted YAML scalar string representation.
    """
    # Handle None/null first before generic string conversion
    if val is None:
        return "null"
    # Handle actual bool and int/float values before string processing
    if isinstance(val, bool):
        return str(val).lower()
    if isinstance(val, (int, float)):
        return str(val)

    if not isinstance(val, str):
        return str(val)

    # Note: val is treated as already decoded.
    # Quote string values that resemble YAML implicit scalar forms (bool, integer, float, etc.)
    needs_quotes = False
    if val == "":
        needs_quotes = True
    elif val.lower() in ['true', 'false', 'null', 'yes', 'no', 'on', 'off']:
        needs_quotes = True
    elif re.match(r'^-?\d+$', val):
        needs_quotes = True
    elif re.match(r'^-?\d+\.\d+$', val):
        needs_quotes = True
    else:
        # Standard quoting checks
        special_chars = ':[]{}()&!@#$%^*+=~`<>,?/;:\\|.'
        if any(ord(c) > 127 for c in val):
            needs_quotes = True
        elif any(c in val for c in special_chars):
            needs_quotes = True
        elif '"' in val or "'" in val:
            needs_quotes = True
        elif ' ' in val:
            needs_quotes = True

    if needs_quotes:
        return escape_yaml_double_quoted_scalar(val)
    else:
        return val


def tokenize_flow_sequence(val):
    """
    Parses a string representing a flow sequence (e.g. "item1, \"item2, vpc\", item3")
    and returns a list of raw string tokens, preserving commas inside quoted items and
    correctly handling quotes and backslashes.
    Note: input val should be the contents inside [ and ].
    """
    tokens = []
    current = []
    in_double_quote = False
    in_single_quote = False
    escaped = False

    i = 0
    while i < len(val):
        c = val[i]

        if escaped:
            current.append(c)
            escaped = False
            i += 1
            continue

        if in_double_quote:
            if c == '\\':
                current.append(c)
                escaped = True
            elif c == '"':
                current.append(c)
                in_double_quote = False
            else:
                current.append(c)
        elif in_single_quote:
            if c == "'" and i + 1 < len(val) and val[i+1] == "'":
                current.append("''")
                i += 1
            elif c == "'":
                current.append(c)
                in_single_quote = False
            else:
                current.append(c)
        else:
            if c == '"':
                in_double_quote = True
                current.append(c)
            elif c == "'":
                in_single_quote = True
                current.append(c)
            elif c == ',':
                tokens.append("".join(current).strip())
                current = []
            else:
                current.append(c)
        i += 1

    tokens.append("".join(current).strip())

    result = []
    for t in tokens:
        stripped = t.strip()
        if not stripped:
            continue
        result.append(stripped)
    return result


def parse_and_decode_yaml_value(val):
    if not isinstance(val, str):
        return val
    val = val.strip()
    if not val:
        return ""

    # Check if it starts/ends with double quotes or single quotes (quoted token)
    if val.startswith('"') and val.endswith('"') and len(val) >= 2:
        inner = val[1:-1]
        # Decode standard YAML escape sequences, Unicode, tabs, and newlines
        def replacer(match):
            esc = match.group(0)
            char = esc[1]
            if char == 'n':
                return '\n'
            elif char == 't':
                return '\t'
            elif char == 'r':
                return '\r'
            elif char == 'b':
                return '\b'
            elif char == 'f':
                return '\f'
            elif char == '"':
                return '"'
            elif char == '\\':
                return '\\'
            elif char == 'u':
                return chr(int(esc[2:6], 16))
            elif char == 'x':
                return chr(int(esc[2:4], 16))
            return esc
        pattern = re.compile(r'\\(?:[ntrbf"\\]|u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2})')
        return pattern.sub(replacer, inner)
    if val.startswith("'") and val.endswith("'") and len(val) >= 2:
        inner = val[1:-1]
        return inner.replace("''", "'")

    # Unquoted tokens: convert to native types if boolean, null, or numeric
    if val.lower() == 'true':
        return True
    if val.lower() == 'false':
        return False
    if val.lower() == 'null':
        return None
    if re.match(r'^-?\d+$', val):
        return int(val)
    if re.match(r'^-?\d+\.\d+$', val):
        return float(val)

    return val


def parse_yaml_front_matter(fm_text):
    """
    Very basic YAML parser that doesn't require PyYAML.
    Only supports top-level key-value pairs (strings, booleans, list of strings/scalars).
    Handles format like key: "value", key: value, key: [a, b, c], or key: - a \n - b
    Also supports a nested single-level 'metadata:' block.
    """
    data = {}
    lines = fm_text.splitlines()
    current_key = None
    in_metadata = False

    for line in lines:
        if line.strip() == '---':
            continue
        if not line.strip() or line.strip().startswith('#'):
            continue

        if line.strip() == 'metadata:':
            in_metadata = True
            data['metadata'] = {}
            continue

        # Check for list items
        if line.strip().startswith('-') and current_key:
            val = line.strip().lstrip('-').strip()
            decoded_val = parse_and_decode_yaml_value(val)
            if in_metadata and current_key:
                meta = data['metadata']
                if current_key not in meta or not isinstance(meta[current_key], list):
                    meta[current_key] = []
                meta[current_key].append(decoded_val)
            elif current_key:
                if current_key not in data or not isinstance(data[current_key], list):
                    data[current_key] = []
                data[current_key].append(decoded_val)
            continue

        match = re.match(r'^([^:]+):\s*(.*)$', line)
        if match:
            key_raw = match.group(1)
            val = match.group(2).strip()

            # Check indentation to determine if inside metadata block
            is_indented = key_raw.startswith(' ') or key_raw.startswith('\t')
            key = key_raw.strip()

            if in_metadata and is_indented:
                current_key = key
                if not val:
                    data['metadata'][key] = []
                elif val.startswith('[') and val.endswith(']'):
                    items = tokenize_flow_sequence(val[1:-1])
                    data['metadata'][key] = [parse_and_decode_yaml_value(x) for x in items]
                else:
                    data['metadata'][key] = parse_and_decode_yaml_value(val)
            else:
                if not is_indented:
                    in_metadata = False
                current_key = key
                if not val:
                    data[current_key] = []
                elif val.startswith('[') and val.endswith(']'):
                    items = tokenize_flow_sequence(val[1:-1])
                    data[current_key] = [parse_and_decode_yaml_value(x) for x in items]
                else:
                    data[current_key] = parse_and_decode_yaml_value(val)

    return data

def serialize_timestamp(val):
    """Serialize and consistently double-quote a timestamp value for YAML frontmatter.

    Args:
        val (any): The timestamp value to serialize.

    Returns:
        str: Double-quoted serialized timestamp string.
    """
    if not val:
        return '""'
    val_str = str(val).strip()
    if not val_str:
        return '""'
    # If already wrapped in double quotes, preserve it
    if val_str.startswith('"') and val_str.endswith('"'):
        return val_str
    # If wrapped in single quotes, change to double quotes
    if val_str.startswith("'") and val_str.endswith("'"):
        return f'"{val_str[1:-1]}"'
    # Consistently double-quote ISO timestamp strings when emitted
    return f'"{val_str}"'


def format_yaml_front_matter(data):
    """Format structured dictionary metadata into an OKF-compliant YAML block.

    Args:
        data (dict): The front matter metadata.

    Returns:
        str: Serialized YAML frontmatter block starting and ending with ---.
    """
    lines = ["---"]

    # Check if this is an Agent Skill frontmatter
    is_skill = "name" in data or data.get("type") == "Agent Skill" or (isinstance(data.get("metadata"), dict) and data["metadata"].get("type") == "Agent Skill")

    if is_skill:
        # Format schema-supported top-level fields first (name, description)
        name_val = data.get("name")
        desc_val = data.get("description")

        # If they are inside metadata map, extract them
        if not name_val and isinstance(data.get("metadata"), dict):
            name_val = data["metadata"].get("name")
        if not desc_val and isinstance(data.get("metadata"), dict):
            desc_val = data["metadata"].get("description")

        if name_val:
            lines.append(f"name: {format_string_value(name_val)}")
        if desc_val:
            lines.append(f"description: {escape_yaml_double_quoted_scalar(desc_val)}")

        # Format the metadata block containing the OKF v0.1 fields
        lines.append("metadata:")
        okf_keys = ["layout", "okf_version", "type", "title", "timestamp", "topics"]

        # Get metadata dictionary if exists, else construct it
        metadata_dict = data.get("metadata", {})
        if not isinstance(metadata_dict, dict):
            metadata_dict = {}

        for k in okf_keys:
            val = metadata_dict.get(k, data.get(k))
            if val is not None:
                if k == "title":
                    lines.append(f"  title: {escape_yaml_double_quoted_scalar(val)}")
                elif k == "timestamp":
                    lines.append(f"  timestamp: {serialize_timestamp(val)}")
                elif k == "topics" and isinstance(val, list):
                    topics_str = ", ".join(escape_yaml_double_quoted_scalar(x) for x in val)
                    lines.append(f"  topics: [{topics_str}]")
                else:
                    lines.append(f"  {k}: {format_string_value(val)}")

        # Any other metadata
        for k, v in sorted(metadata_dict.items()):
            if k in okf_keys or k in ["name", "description"]:
                continue
            lines.append(f"  {k}: {format_string_value(v)}")

        # Any other top-level keys that are NOT metadata and NOT name/description/okf_keys
        for k, v in sorted(data.items()):
            if k in ["name", "description", "metadata"] or k in okf_keys:
                continue
            lines.append(f"{k}: {format_string_value(v)}")
    else:
        # Standard OKF formatting for general markdown files
        if "layout" in data:
            lines.append(f"layout: {format_string_value(data['layout'])}")

        lines.append(f"okf_version: {format_string_value(data.get('okf_version', '0.1'))}")
        lines.append(f"type: {format_string_value(data.get('type', 'Technical Documentation'))}")

        title = data.get('title', '')
        lines.append(f"title: {escape_yaml_double_quoted_scalar(title)}")

        lines.append(f"timestamp: {serialize_timestamp(data.get('timestamp', ''))}")

        topics = data.get('topics', [])
        if isinstance(topics, list):
            topics_str = ", ".join(escape_yaml_double_quoted_scalar(x) for x in topics)
            lines.append(f"topics: [{topics_str}]")
        else:
            lines.append(f"topics: {format_string_value(topics)}")

        # Write other existing fields
        for k, v in sorted(data.items()):
            if k in ["layout", "okf_version", "type", "title", "timestamp", "topics"]:
                continue
            if isinstance(v, list):
                v_str = ", ".join(escape_yaml_double_quoted_scalar(x) for x in v)
                lines.append(f"{k}: [{v_str}]")
            elif isinstance(v, bool):
                lines.append(f"{k}: {str(v).lower()}")
            else:
                lines.append(f"{k}: {format_string_value(v)}")

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
                items = tokenize_flow_sequence(val[1:-1])
                parsed_val = [parse_and_decode_yaml_value(x) for x in items]
            else:
                parsed_val = parse_and_decode_yaml_value(val)

            key_line_map[current_key] = {
                'start_line': i,
                'end_line': i,
                'value': parsed_val,
                'raw_val': val
            }
        elif current_key is not None:
            key_line_map[current_key]['end_line'] = i
            if line.strip().startswith('-'):
                item_val = line.strip().lstrip('-').strip()
                decoded_item = parse_and_decode_yaml_value(item_val)
                if not isinstance(key_line_map[current_key]['value'], list):
                    key_line_map[current_key]['value'] = []
                key_line_map[current_key]['value'].append(decoded_item)

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
    final_lines.append(f"layout: {format_string_value(layout_val)}")
    final_lines.append(f"okf_version: {format_string_value(okf_version_val)}")
    final_lines.append(f"type: {format_string_value(type_val)}")

    # Title format (always double-quoted to be standard and stable)
    final_lines.append(f"title: {escape_yaml_double_quoted_scalar(title_val)}")

    # Keep timestamps intact (Requirement 3)
    final_lines.append(f"timestamp: {serialize_timestamp(timestamp_val)}")

    # Use array format with double quotes (Requirement 3 example)
    topics_str = ", ".join(escape_yaml_double_quoted_scalar(x) for x in topics_val)
    final_lines.append(f"topics: [{topics_str}]")

    for line in preserved_lines:
        if line.strip():
            # If the line is a single-line key-value pair, ensure its value is formatted correctly
            match = re.match(r'^([a-zA-Z0-9_-]+):\s*(.*)$', line)
            if match:
                k = match.group(1)
                v = match.group(2).strip()
                if v and not (v.startswith('[') or v.startswith('{') or v.startswith('-') or v.startswith('|') or v.startswith('>')):
                    decoded_v = parse_and_decode_yaml_value(v)
                    final_lines.append(f"{k}: {format_string_value(decoded_v)}")
                elif v and v.startswith('[') and v.endswith(']'):
                    items = tokenize_flow_sequence(v[1:-1])
                    decoded_items = [parse_and_decode_yaml_value(x) for x in items]
                    formatted_items = ", ".join(escape_yaml_double_quoted_scalar(x) for x in decoded_items)
                    final_lines.append(f"{k}: [{formatted_items}]")
                else:
                    final_lines.append(line)
            else:
                final_lines.append(line)

    return "---\n" + "\n".join(final_lines) + "\n---"

def process_markdown_file(filepath):
    """Process a single Markdown file, adding or updating OKF frontmatter.

    Extracts existing metadata or infers baseline OKF fields, serializes the block,
    validates the structural integrity, and overwrites the target file.

    Args:
        filepath (str): The absolute path to the Markdown file.
    """
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

    is_skill = os.path.basename(filepath).lower() == "skill.md"

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
        if is_skill:
            meta = validated_fm.get("metadata", {})
            for key in ["name", "description"]:
                if key not in validated_fm:
                    raise ValueError(f"Validation failed: {key} missing in serialized front matter of {filepath}")
            for key in ["okf_version", "type", "title", "timestamp", "topics"]:
                if key not in meta:
                    raise ValueError(f"Validation failed: {key} missing in serialized front matter metadata of {filepath}")
        else:
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

            if is_skill:
                fm_data = parse_yaml_front_matter(fm_text)
                # Enforce structure
                new_fm_text = format_yaml_front_matter(fm_data)
            else:
                new_fm_text = process_front_matter_structure_preserving(
                    fm_text, filepath, title, timestamp, okf_type, okf_topics
                )

            # Validate serialized front matter before writing
            validated_fm = parse_yaml_front_matter(new_fm_text.strip("-\n"))
            if is_skill:
                meta = validated_fm.get("metadata", {})
                for key in ["name", "description"]:
                    if key not in validated_fm:
                        raise ValueError(f"Validation failed: {key} missing in serialized front matter of {filepath}")
                for key in ["okf_version", "type", "title", "timestamp", "topics"]:
                    if key not in meta:
                        raise ValueError(f"Validation failed: {key} missing in serialized front matter metadata of {filepath}")
            else:
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

def main(repo_root=None):
    """Traverse and standardize all Markdown files under the repository root.

    Args:
        repo_root (str, optional): The base folder path. Defaults to None.
    """
    if repo_root is None:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    repo_root = os.path.realpath(repo_root)
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
                    if os.path.commonpath((repo_root, resolved_path)) != repo_root:
                        continue
                except ValueError:
                    continue

                process_markdown_file(resolved_path)

if __name__ == '__main__':
    main()
