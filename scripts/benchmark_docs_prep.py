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

def test_uncompiled():
    # Simulate current code
    heading_match = re.search(r'^\s*#+\s+(.+)$', content, re.MULTILINE)
    if heading_match:
        _ = heading_match.group(1).strip()

# Compiled regex
HEADING_PATTERN = re.compile(r'^\s*#+\s+(.+)$', re.MULTILINE)

def test_compiled():
    # Simulate optimized code
    heading_match = HEADING_PATTERN.search(content)
    if heading_match:
        _ = heading_match.group(1).strip()

def main():
    print("Running benchmark (1,000,000 iterations)...")
    uncompiled_time = timeit.timeit(test_uncompiled, number=1000000)
    compiled_time = timeit.timeit(test_compiled, number=1000000)

    print(f"Uncompiled search time: {uncompiled_time:.6f} seconds")
    print(f"Compiled search time: {compiled_time:.6f} seconds")
    improvement = (uncompiled_time - compiled_time) / uncompiled_time * 100
    print(f"Improvement: {improvement:.2f}% faster")

if __name__ == "__main__":
    main()
