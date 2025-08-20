#!/usr/bin/env python3

"""
UserPromptSubmit hook for context injection.
Automatically adds tool usage reminders when prompts mention file operations.
"""

import json
import sys
import re


def main():
    """Main hook logic for context injection."""
    try:
        input_data = json.load(sys.stdin)
        prompt = input_data.get("prompt", "")

        # Check if prompt mentions file operations, searching, GitHub, or bash commands
        file_operation_patterns = [
            r"\bfind\b",
            r"\bgrep\b",
            r"\bls\b.*\|",
            r"\bbash\b",
            r"\bsearch\b",
            r"\bfile\b",
            r"\bdirectory\b",
            r"\bgithub\b",
        ]

        if any(
            re.search(pattern, prompt, re.IGNORECASE)
            for pattern in file_operation_patterns
        ):
            additional_context = """
CRITICAL TOOL USAGE REMINDER (from CLAUDE.md):
• NEVER use 'grep' - ALWAYS use 'rg' (ripgrep)
• NEVER use 'find -name' - ALWAYS use 'rg --files -g "pattern"'
• NEVER chain commands like 'rg | grep', 'ls | rg', 'find | rg'
• Use single 'rg' commands with combined patterns

Your hooks will block violations of these rules.
"""

            output = {"hookSpecificOutput": {"additionalContext": additional_context}}
            print(json.dumps(output))

    except Exception:
        pass  # Silent failure to avoid disrupting workflow


if __name__ == "__main__":
    main()
