import re
import timeit

# Dummy Markdown text for testing
content = """# Title of the Document
Some introduction text here.
## Sub-heading
More text.
### Another Heading
Even more text.
"""

def test_pattern_string_api():
    # Uses the string API which incurs regex cache lookup overhead
    heading_match = re.search(r'^\s*#+\s+(.+)$', content, re.MULTILINE)
    if heading_match:
        _ = heading_match.group(1).strip()

# Compiled regex
HEADING_PATTERN = re.compile(r'^\s*#+\s+(.+)$', re.MULTILINE)

def test_compiled_pattern_api():
    # Uses the compiled pattern API directly, avoiding cache lookup overhead
    heading_match = HEADING_PATTERN.search(content)
    if heading_match:
        _ = heading_match.group(1).strip()

def main():
    print("Running benchmark (1,000,000 iterations)...")
    string_api_time = timeit.timeit(test_pattern_string_api, number=1000000)
    compiled_api_time = timeit.timeit(test_compiled_pattern_api, number=1000000)

    print(f"Pattern string API search time: {string_api_time:.6f} seconds")
    print(f"Compiled pattern API search time: {compiled_api_time:.6f} seconds")
    improvement = (string_api_time - compiled_api_time) / string_api_time * 100
    print(f"Improvement: {improvement:.2f}% faster")

if __name__ == "__main__":
    main()
