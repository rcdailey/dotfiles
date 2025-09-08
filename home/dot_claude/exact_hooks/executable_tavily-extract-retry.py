#!/usr/bin/env python3

"""
Tavily Extract Auto-Retry Hook for Claude Code.

Detects when mcp__tavily__tavily-extract returns empty results without the advanced flag,
then automatically blocks Claude and instructs it to retry with extract_depth: "advanced".

This addresses the known issue where Tavily extract silently fails for certain URLs
when using the default extraction depth but works correctly with advanced extraction.

See: https://github.com/tavily-ai/tavily-mcp/issues/58
"""

import json
import sys
import os
from datetime import datetime
from typing import Any, Dict


def is_empty_content(content: Any) -> bool:
    """Check if content is effectively empty."""
    if not content:
        return True

    if isinstance(content, str):
        return len(content.strip()) == 0

    if isinstance(content, list):
        return len(content) == 0 or all(is_empty_content(item) for item in content)

    if isinstance(content, dict):
        return len(content) == 0 or all(
            is_empty_content(value) for value in content.values()
        )

    return False


def has_meaningful_content(tool_response: Any) -> bool:
    """
    Check if the tool response contains meaningful content.

    Returns False if the response indicates empty extraction (but tool succeeded).
    Returns True if tool failed (different issue, don't interfere).
    """
    # Handle case where tool_response is directly a list (actual format)
    if isinstance(tool_response, list):
        content_items = tool_response
    elif isinstance(tool_response, dict):
        # If tool explicitly failed, don't interfere (different issue)
        if tool_response.get("success") is False:
            return True

        # Check for nested content structure: { content: [{ type: "text", text: "..." }] }
        content_items = tool_response.get("content", [])
        if not isinstance(content_items, list):
            return False
    else:
        return False

    # Analyze content items
    if isinstance(content_items, list):
        for item in content_items:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text", "")
                if isinstance(text, str):
                    # Check for meaningful content indicators
                    text_stripped = text.strip()
                    if len(text_stripped) > 50:
                        return True
                    # Check for truncation indicators that suggest hidden content
                    if "… +" in text or "lines (ctrl+r to expand)" in text:
                        return True
                    # Check for common content patterns that indicate successful extraction
                    if any(
                        pattern in text_stripped.lower()
                        for pattern in [
                            "<title>",
                            "<h1>",
                            "<h2>",
                            "<p>",
                            "<!doctype",
                            "# ",
                            "## ",
                            "### ",  # Markdown headers
                            "content-type:",
                            "charset=",  # Meta content
                        ]
                    ):
                        return True

    return False


def dry_run() -> None:
    """Test the hook logic with sample inputs."""
    print("Testing Tavily Extract Auto-Retry Hook:\n")

    test_cases = [
        # Should trigger retry - empty content without advanced flag (list format)
        {
            "name": "Empty content (list format), no advanced flag",
            "tool_input": {"urls": ["https://example.com"]},
            "tool_response": [{"type": "text", "text": ""}],
            "should_block": True,
        },
        # Should trigger retry - empty list without advanced flag
        {
            "name": "Empty list, no advanced flag",
            "tool_input": {"urls": ["https://example.com"]},
            "tool_response": [],
            "should_block": True,
        },
        # Should NOT trigger retry - has content (actual format from real tool)
        {
            "name": "Has meaningful content (actual format)",
            "tool_input": {"urls": ["https://example.com"]},
            "tool_response": [
                {
                    "type": "text",
                    "text": "Detailed Results:\n\nTitle: Example\nURL: https://example.com\nContent: This is meaningful content from the webpage that is longer than 50 characters and contains useful information.",
                }
            ],
            "should_block": False,
        },
        # Should NOT trigger retry - legacy nested format still supported
        {
            "name": "Has meaningful content (legacy nested format)",
            "tool_input": {"urls": ["https://example.com"]},
            "tool_response": {
                "success": True,
                "content": [
                    {
                        "type": "text",
                        "text": "This is meaningful content from the webpage that is longer than 50 characters.",
                    }
                ],
            },
            "should_block": False,
        },
        # Should NOT trigger retry - truncated content indicator
        {
            "name": "Truncated content with expansion indicator",
            "tool_input": {"urls": ["https://example.com"]},
            "tool_response": {
                "success": True,
                "content": [
                    {
                        "type": "text",
                        "text": "Title: JetBrains ReSharper\n… +584 lines (ctrl+r to expand)",
                    }
                ],
            },
            "should_block": False,
        },
        # Should NOT trigger retry - already using advanced
        {
            "name": "Empty content but advanced flag set",
            "tool_input": {
                "urls": ["https://example.com"],
                "extract_depth": "advanced",
            },
            "tool_response": {"success": True, "content": ""},
            "should_block": False,
        },
        # Should NOT trigger retry - tool failed (different issue)
        {
            "name": "Tool failed",
            "tool_input": {"urls": ["https://example.com"]},
            "tool_response": {"success": False, "error": "Network error"},
            "should_block": False,
        },
    ]

    for test_case in test_cases:
        print(f"=== {test_case['name']} ===")

        tool_input = test_case["tool_input"]
        tool_response = test_case["tool_response"]
        expected_block = test_case["should_block"]

        # Test the logic
        extract_depth = tool_input.get("extract_depth", "basic")
        using_advanced = extract_depth == "advanced"
        has_content = has_meaningful_content(tool_response)

        should_block = not using_advanced and not has_content

        status = "BLOCK" if should_block else "ALLOW"
        expected_status = "BLOCK" if expected_block else "ALLOW"
        result = "✓ PASS" if should_block == expected_block else "✗ FAIL"

        print(f"  Extract depth: {extract_depth}")
        print(f"  Has content: {has_content}")
        print(f"  Expected: {expected_status}")
        print(f"  Actual: {status}")
        print(f"  Result: {result}")
        print()


def log_tool_data(tool_input: Dict[str, Any], tool_response: Dict[str, Any]) -> None:
    """Log raw tool input/output data to debug file."""
    log_dir = os.path.expanduser("~/.local/share/claude-hooks-debug")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_file = os.path.join(log_dir, f"tavily-extract-{timestamp}.json")

    debug_data = {
        "timestamp": datetime.now().isoformat(),
        "tool_input": tool_input,
        "tool_response": tool_response,
    }

    with open(log_file, "w") as f:
        json.dump(debug_data, f, indent=2)


def main() -> None:
    """Main hook logic."""
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        dry_run()
        return

    # Parse hook input
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})

    # Only process tavily-extract tool
    if tool_name != "mcp__tavily__tavily-extract":
        sys.exit(0)

    # Log the raw data for debugging
    log_tool_data(tool_input, tool_response)

    # Check if already using advanced extraction
    extract_depth = tool_input.get("extract_depth", "basic")
    if extract_depth == "advanced":
        # Already using advanced, don't interfere
        sys.exit(0)

    # Check if extraction returned meaningful content
    if has_meaningful_content(tool_response):
        # Extraction succeeded, allow it to proceed
        sys.exit(0)

    # Empty results without advanced flag - block and instruct retry
    error_msg = (
        "TAVILY EXTRACT FAILURE: Empty results detected. "
        "Retry this exact request with 'extract_depth: \"advanced\"' parameter."
    )
    print(error_msg, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
