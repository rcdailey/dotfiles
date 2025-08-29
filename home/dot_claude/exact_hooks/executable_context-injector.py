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
• Use 'gh' CLI for: all GitHub operations (listing, viewing, searching)
• Use mcp__octocode__* for: advanced code/repo search (superior performance)
• NEVER use: grep, find -name, command chaining, include_raw_content=true, GitHub MCP tools""")

    except Exception:
        pass  # Silent failure to avoid disrupting workflow


if __name__ == "__main__":
    main()
