#!/usr/bin/env python3
"""
Context7 Documentation Preference Hook

Analyzes Context7 library search results and provides guidance to Claude
to prioritize documentation-focused sources over code repositories.
"""

import json
import re
import sys


def is_documentation_result(library_id: str, name: str, description: str) -> bool:
    """
    Determine if a result appears to be documentation-focused.

    Args:
        library_id: Context7-compatible library ID (e.g., /org/project)
        name: Library name
        description: Library description

    Returns:
        True if the result appears to be documentation-focused
    """
    # Documentation indicators in library ID
    doc_id_patterns = [
        r"/docs$",
        r"/documentation$",
        r"-docs$",
        r"[_-]documentation$",
        r"^/websites/",
    ]

    # Documentation indicators in name
    doc_name_patterns = [
        r"\bdocs?\b",
        r"\bdocumentation\b",
        r"\bguide\b",
        r"\btutorial\b",
        r"\breference\b",
        r"\bmanual\b",
    ]

    # Documentation indicators in description
    doc_desc_patterns = [
        r"\bofficial\s+documentation\b",
        r"\bdocumentation\s+(site|website)\b",
        r"\bdocs?\s+(site|website)\b",
        r"\bguide\b",
        r"\btutorial\b",
        r"\breference\s+documentation\b",
        r"\bAPI\s+documentation\b",
    ]

    # Check library ID
    for pattern in doc_id_patterns:
        if re.search(pattern, library_id, re.IGNORECASE):
            return True

    # Check name
    for pattern in doc_name_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return True

    # Check description
    for pattern in doc_desc_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            return True

    return False


def is_website_result(library_id: str) -> bool:
    """Check if result is a website (typically documentation)."""
    return library_id.startswith("/websites/")


def analyze_context7_results(tool_response: str) -> None:
    """
    Analyze Context7 search results and provide guidance.

    Args:
        tool_response: Raw response text from resolve-library-id tool
    """
    # Parse the response to extract library information
    # The response format includes library entries with ID, name, description

    doc_results = []
    code_results = []

    # Split by result separators
    entries = tool_response.split("----------")

    for entry in entries:
        if not entry.strip():
            continue

        # Extract library ID
        library_id_match = re.search(
            r"Context7-compatible library ID:\s*(.+?)(?:\n|$)", entry
        )
        if not library_id_match:
            continue
        library_id = library_id_match.group(1).strip()

        # Extract title/name
        title_match = re.search(r"Title:\s*(.+?)(?:\n|$)", entry)
        name = title_match.group(1).strip() if title_match else ""

        # Extract description
        desc_match = re.search(r"Description:\s*(.+?)(?:\n|$)", entry)
        description = desc_match.group(1).strip() if desc_match else ""

        # Categorize the result
        result_info = {
            "id": library_id,
            "name": name,
            "description": description,
        }

        if is_documentation_result(library_id, name, description) or is_website_result(
            library_id
        ):
            doc_results.append(result_info)
        else:
            code_results.append(result_info)

    # Provide guidance if documentation results exist
    if doc_results:
        print("\n" + "=" * 80)
        print("IMPORTANT: CONTEXT7 DOCUMENTATION GUIDANCE")
        print("=" * 80)
        print("\nFOR YOUR NEXT get-library-docs CALL:")
        print(f"  USE THIS: {doc_results[0]['id']}")
        print("\nWHY: This is the official documentation site.")
        print("     Code repositories contain implementation, not usage guides.")

        if len(doc_results) > 1:
            print("\nAlternative documentation sources:")
            for result in doc_results[1:3]:
                print(f"  - {result['id']}")

        if code_results:
            print("\nCode repositories (for implementation details only):")
            for result in code_results[:2]:
                print(f"  - {result['id']}")

        print("\n" + "=" * 80 + "\n")


def main():
    """Main hook execution."""
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        tool_name = input_data.get("tool_name", "")

        # Only process Context7 resolve-library-id tool
        if tool_name != "mcp__context7__resolve-library-id":
            sys.exit(0)

        # Get the tool response - it's a list with a single dict containing text
        tool_response_raw = input_data.get("tool_response", [])

        if not tool_response_raw:
            sys.exit(0)

        # Extract the text content from the response structure
        # tool_response is a list: [{"type": "text", "text": "..."}]
        response_text = ""
        if isinstance(tool_response_raw, list) and len(tool_response_raw) > 0:
            first_item = tool_response_raw[0]
            if isinstance(first_item, dict):
                response_text = first_item.get("text", "")

        if not response_text:
            sys.exit(0)

        # Analyze and provide guidance
        analyze_context7_results(response_text)

        # Exit successfully (non-blocking)
        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error in context7-doc-preference hook: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
