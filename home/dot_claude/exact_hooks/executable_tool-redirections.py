#!/usr/bin/env python3

"""
Consolidated tool redirection hook for Claude Code.
Catches common tool usage patterns and suggests better alternatives.
"""

import json
import re
import sys
from typing import NamedTuple


class RedirectionRule(NamedTuple):
    """A single redirection rule with pattern and message."""

    pattern: re.Pattern[str]
    message: str
    examples: list[str]


# Tool redirection rules
REDIRECTIONS = [
    RedirectionRule(
        pattern=re.compile(r"\bgrep\b"),
        message="Use 'rg' instead of 'grep' for better performance and features",
        examples=["grep pattern file.txt", "ps aux | grep process"],
    ),
    RedirectionRule(
        pattern=re.compile(r"\bfind\b.*-name"),
        message="Use 'rg --files -g pattern' instead of 'find -name'",
        examples=["find /path -name '*.txt'", "find . -name 'test*'"],
    ),
    RedirectionRule(
        pattern=re.compile(r"\|.*\bgrep\b"),
        message="Avoid chaining grep commands - use 'rg' with multiple patterns or combined regex",
        examples=["rg files | grep -v '/obj/'", "cat file | grep pattern"],
    ),
    RedirectionRule(
        pattern=re.compile(r"\bls\b.*\|.*\b(rg|grep)\b"),
        message="Use 'rg --files -g pattern' instead of 'ls | rg/grep' for file filtering",
        examples=["ls -la | rg pattern", "ls *.txt | grep file"],
    ),
    RedirectionRule(
        pattern=re.compile(r"\bfind\b.*\|.*\b(rg|grep)\b"),
        message="Use 'rg --files -g pattern' instead of 'find | rg/grep' combinations",
        examples=[
            "find . -type d | rg pattern",
            "find /path -name '*.txt' | grep filter",
        ],
    ),
    RedirectionRule(
        pattern=re.compile(r"sops\s+--set"),
        message="Use 'sops set' instead of 'sops --set'\nCorrect: sops set file.sops.yaml '[\"section\"][\"key\"]' '\"value\"'",
        examples=["sops --set file.yaml key value"],
    ),
]

# Tavily MCP restrictions
TAVILY_RESTRICTIONS = [
    RedirectionRule(
        pattern=re.compile(
            r"(?<!docs\.)(?<!gist\.)github\.com(?!/marketplace)", re.IGNORECASE
        ),
        message="BLOCKED: GitHub repository detected. MUST retry this request using GitHub CLI tools (gh) instead.",
        examples=[
            "github.com/user/repo",
            "github.com/org/project",
            "https://github.com/example",
            "repository analysis",
            "code search across repos",
        ],
    ),
]

# GitHub CLI enforcements (replacing GitHub MCP tools)
GITHUB_CLI_REDIRECTIONS = [
    RedirectionRule(
        pattern=re.compile(r"mcp__github__search_code"),
        message="Use 'mcp__octocode__githubSearchCode' instead for superior GitHub code search with bulk operations, filtering, and optimized token usage.",
        examples=[
            "searching code across repositories",
            "finding specific functions or patterns",
        ],
    ),
    RedirectionRule(
        pattern=re.compile(r"mcp__github__search_repositories"),
        message="Use 'mcp__octocode__githubSearchRepositories' instead for comprehensive repository discovery with quality filtering and bulk operations.",
        examples=["finding repositories by topic", "discovering similar projects"],
    ),
    RedirectionRule(
        pattern=re.compile(r"mcp__github__search_pull_requests"),
        message="Use 'gh search prs' for PR searching with better performance and native CLI integration.",
        examples=["analyzing pull request patterns", "finding PRs by criteria"],
    ),
    RedirectionRule(
        pattern=re.compile(r"mcp__github__search_issues"),
        message="Use 'gh search issues' for GitHub issue searching with better performance and native CLI integration.",
        examples=["finding issues by criteria", "searching issue content"],
    ),
    RedirectionRule(
        pattern=re.compile(r"mcp__github__list_pull_requests"),
        message="Use 'gh pr list' for listing pull requests with better performance and native CLI integration.",
        examples=["listing repository PRs", "filtering PRs by status"],
    ),
    RedirectionRule(
        pattern=re.compile(r"mcp__github__list_issues"),
        message="Use 'gh issue list' for listing issues with better performance and native CLI integration.",
        examples=["listing repository issues", "filtering issues by status"],
    ),
    RedirectionRule(
        pattern=re.compile(r"mcp__github__list_releases"),
        message="Use 'gh release list' for listing releases with better performance and native CLI integration.",
        examples=["listing repository releases", "checking latest versions"],
    ),
    RedirectionRule(
        pattern=re.compile(r"mcp__github__list_workflow_jobs"),
        message="Use 'gh run list' for workflow information with better performance and native CLI integration.",
        examples=["checking workflow job status", "monitoring CI/CD runs"],
    ),
    RedirectionRule(
        pattern=re.compile(r"mcp__github__list_workflow_runs"),
        message="Use 'gh run list' for workflow run information with better performance and native CLI integration.",
        examples=["listing workflow runs", "checking CI/CD history"],
    ),
    RedirectionRule(
        pattern=re.compile(r"mcp__github__list_discussions"),
        message="Use 'gh api' with GraphQL for discussion operations with better performance and native CLI integration.",
        examples=["retrieving discussions", "analyzing discussion content"],
    ),
    RedirectionRule(
        pattern=re.compile(r"mcp__github__get_"),
        message="Use appropriate 'gh' CLI commands for GitHub data retrieval: 'gh issue view', 'gh pr view', 'gh release view', 'gh run view', etc.",
        examples=[
            "getting single issues",
            "viewing PRs",
            "checking releases",
            "workflow details",
        ],
    ),
]


def dry_run() -> None:
    """Test all redirection patterns against sample commands."""
    print("Testing regex patterns against sample commands:\n")

    # Comprehensive test commands
    test_commands = [
        # Should match patterns
        "grep pattern file.txt",
        "ps aux | grep process",
        "grep -v unwanted file.txt",
        "find /path -name '*.txt'",
        "find . -name 'test*'",
        "find . -maxdepth 2 -type d | rg pattern",
        "find /usr -type f | grep config",
        "rg files | grep -v '/obj/'",
        "cat file | grep pattern",
        "ls | grep -E '^test'",
        "ls -la | rg blocky",
        "ls *.txt | grep file",
        "rg pattern | grep other",
        "rg --files | grep filter",
        "sops --set file.yaml key value",
        # Should NOT match any patterns (excluded commands)
        "git commit -m 'find the right solution'",
        "ssh user@host 'grep logs'",
        "kubectl exec -n media restore-config -- grep -E 'api_key|download_dir|complete_dir' /config/sabnzbd.ini",
        "kubectl exec -n media restore-config -- sh -c \"rg 'api_key|download_dir|complete_dir' /config/sabnzbd.ini || grep -E 'api_key|download_dir|complete_dir' /config/sabnzbd.ini\"",
        "docker exec container grep pattern file",
        "podman exec container find /path -name '*.txt'",
        "rg files | head -10",
        "sops set file.yaml key value",
        "find /usr/local -type f",
    ]

    for i, rule in enumerate(REDIRECTIONS, 1):
        print(f"=== Rule {i}: {rule.pattern.pattern} ===")
        print(f"Examples: {', '.join(rule.examples)}")

        matches = [cmd for cmd in test_commands if rule.pattern.search(cmd)]
        non_matches = [cmd for cmd in test_commands if not rule.pattern.search(cmd)]

        if matches:
            print("✓ MATCHES:")
            for cmd in matches:
                print(f"  {cmd}")

        if non_matches:
            print("  No matches:")
            for cmd in non_matches[:3]:  # Show first 3 to keep output manageable
                print(f"  {cmd}")
            if len(non_matches) > 3:
                print(f"  ... and {len(non_matches) - 3} more")

        print()

    # Test Tavily queries and URLs
    tavily_test_queries = [
        # Should match GitHub pattern (repositories)
        "search github.com repositories",
        "find issues on GitHub.com",
        "https://github.com/user/repo",
        "https://github.com/actions/checkout",
        # Should NOT match (docs.github.com, gist.github.com, and marketplace)
        "https://docs.github.com/en/actions/how-tos/sharing-automations/reusing-workflows",
        "https://docs.github.com/en/github/getting-started-with-github",
        "https://gist.github.com/user/12345",
        "https://gist.github.com/anonymous/abcdef123456",
        "gist.github.com/user/snippet",
        "https://github.com/marketplace/actions/workflow-run-debounce",
        "github.com/marketplace/category/deployment",
        "search for python tutorials",
        "find documentation online",
        "https://stackoverflow.com/questions",
    ]

    print("=== Tavily Restrictions ===")
    for i, rule in enumerate(TAVILY_RESTRICTIONS, 1):
        print(f"=== Tavily Rule {i}: {rule.pattern.pattern} ===")
        print(f"Examples: {', '.join(rule.examples)}")

        matches = [query for query in tavily_test_queries if rule.pattern.search(query)]
        non_matches = [
            query for query in tavily_test_queries if not rule.pattern.search(query)
        ]

        if matches:
            print("MATCHES:")
            for query in matches:
                print(f"  {query}")

        if non_matches:
            print("  No matches:")
            for query in non_matches:
                print(f"  {query}")

        print()

    # Test Tavily parameter validation
    print("=== Tavily Parameter Validation ===")
    tavily_test_inputs = [
        # Should be blocked - include_raw_content=true
        {
            "tool_name": "mcp__tavily__tavily-search",
            "tool_input": {"query": "test", "include_raw_content": True},
        },
        {
            "tool_name": "mcp__tavily__tavily-extract",
            "tool_input": {
                "urls": ["https://example.com"],
                "include_raw_content": True,
            },
        },
        # Should be allowed - default behavior
        {"tool_name": "mcp__tavily__tavily-search", "tool_input": {"query": "test"}},
        {
            "tool_name": "mcp__tavily__tavily-extract",
            "tool_input": {"urls": ["https://example.com"]},
        },
    ]

    for test_input in tavily_test_inputs:
        has_raw_content = test_input.get("tool_input", {}).get(
            "include_raw_content", False
        )
        tool_name = test_input["tool_name"]
        status = "BLOCKED" if has_raw_content else "ALLOWED"
        print(f"  {tool_name} with include_raw_content={has_raw_content}: {status}")

    print()

    # Test command exclusion logic
    print("=== Command Exclusion Testing ===")
    test_exclusion_commands = [
        "kubectl exec -n media restore-config -- grep -E 'api_key|download_dir|complete_dir' /config/sabnzbd.ini",
        "kubectl exec -n media restore-config -- sh -c \"rg 'api_key|download_dir|complete_dir' /config/sabnzbd.ini || grep -E 'api_key|download_dir|complete_dir' /config/sabnzbd.ini\"",
        "docker exec container grep pattern file",
        "podman exec container find /path -name '*.txt'",
        "ssh user@host 'grep logs'",
        "git commit -m 'find the right solution'",
        "grep pattern file.txt",  # Should be blocked
        "find /path -name '*.txt'",  # Should be blocked
    ]

    for cmd in test_exclusion_commands:
        is_excluded = bool(
            re.match(r"^\s*(git|ssh|kubectl\s+exec|docker\s+exec|podman\s+exec)\s", cmd)
        )
        would_match = any(rule.pattern.search(cmd) for rule in REDIRECTIONS)
        status = (
            "EXCLUDED" if is_excluded else ("BLOCKED" if would_match else "ALLOWED")
        )
        print(f"  {cmd[:50]}{'...' if len(cmd) > 50 else ''}: {status}")

    print()


def main() -> None:
    """Main hook logic."""
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        dry_run()
        return

    # Normal hook operation
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    command = input_data.get("tool_input", {}).get("command", "")

    # Block LS tool - require rg instead
    if tool_name == "LS":
        error_msg = "TOOL USAGE VIOLATION: Use 'rg --files' or 'rg --files -g pattern' instead of LS tool for file listing"
        print(error_msg, file=sys.stderr)
        sys.exit(2)

    # Block Search tool - require rg instead
    if tool_name == "Search":
        error_msg = 'TOOL USAGE VIOLATION: Use \'rg\' instead of Search tool for content searching\nExamples: rg "pattern", rg -i "pattern" (case insensitive), rg "pattern" --type js (file type), rg -A3 -B3 "pattern" (with context)'
        print(error_msg, file=sys.stderr)
        sys.exit(2)

    # Process Bash commands
    if tool_name == "Bash" and command:
        # Skip validation for remote execution and container commands to avoid false positives
        if re.match(
            r"^\s*(git|ssh|kubectl\s+exec|docker\s+exec|podman\s+exec)\s", command
        ):
            sys.exit(0)

        # Check each redirection pattern
        for rule in REDIRECTIONS:
            if rule.pattern.search(command):
                error_msg = f"TOOL USAGE VIOLATION: {rule.message}"
                print(error_msg, file=sys.stderr)
                sys.exit(2)

    # Process GitHub MCP tools (now redirected to gh CLI)
    elif tool_name.startswith("mcp__github__"):
        # Check each GitHub CLI redirection pattern
        for rule in GITHUB_CLI_REDIRECTIONS:
            if rule.pattern.search(tool_name):
                error_msg = f"GITHUB TOOL VIOLATION: {rule.message}"
                print(error_msg, file=sys.stderr)
                sys.exit(2)

    # Process Tavily MCP tools
    elif tool_name.startswith("mcp__tavily__"):
        tool_input = input_data.get("tool_input", {})
        query = tool_input.get("query", "")
        urls = tool_input.get("urls", [])

        # Check for raw content flag (token-expensive)
        if tool_input.get("include_raw_content", False):
            error_msg = "TAVILY USAGE VIOLATION: NEVER use 'include_raw_content=true' - causes excessive token usage. Use default content extraction instead."
            print(error_msg, file=sys.stderr)
            sys.exit(2)

        # Check query for GitHub references
        if query:
            for rule in TAVILY_RESTRICTIONS:
                if rule.pattern.search(query):
                    error_msg = f"TAVILY USAGE VIOLATION: {rule.message}"
                    print(error_msg, file=sys.stderr)
                    sys.exit(2)

        # Check URLs for GitHub references
        if urls:
            for url in urls:
                for rule in TAVILY_RESTRICTIONS:
                    if rule.pattern.search(url):
                        error_msg = f"TAVILY USAGE VIOLATION: {rule.message}"
                        print(error_msg, file=sys.stderr)
                        sys.exit(2)


if __name__ == "__main__":
    main()
