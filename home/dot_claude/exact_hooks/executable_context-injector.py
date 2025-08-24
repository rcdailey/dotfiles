#!/usr/bin/env python3

"""
UserPromptSubmit hook for context injection.
Always adds tool usage requirements to ensure optimal tool selection.
"""


def main():
    """Main hook logic for context injection."""
    try:
        # Always inject tool usage guidance for optimal performance
        # For UserPromptSubmit hooks, stdout is directly added to context
        print("""
TOOL USAGE REQUIREMENTS (ENFORCED BY HOOKS):
• Use 'rg' for: text search, file discovery (rg --files -g "pattern")
• Use 'gh' CLI for: listing issues/PRs/workflows, searching issues
• Use mcp__octocode__* for: code/repo/PR search (superior to GitHub MCP)
• Use mcp__github__get_* for: single item retrieval only
• NEVER use: grep, find -name, command chaining, include_raw_content=true""")

    except Exception:
        pass  # Silent failure to avoid disrupting workflow


if __name__ == "__main__":
    main()
