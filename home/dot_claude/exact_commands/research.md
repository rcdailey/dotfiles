---
description: Build a Perplexity search prompt for research or answers on a topic
---

Build a Perplexity search prompt for the following topic "$ARGUMENTS" (if provided) or inferred from
recent discussion/problems.

Your search prompt should be as detailed as necessary to get only the information relevant to the
search topics. Start with a brief intro for context, followed by a bullet list of one or more
questions, followed by an OPTIONAL concluding section with additional search requirements or
constraints.

Return ONLY the search prompt - no additional text, explanations, or boilerplate.

CRITICAL: After outputting the search prompt, STOP and take NO further action. Do not perform any
research, web searches, or other tasks. The provided argument is NOT a directive for you to
follow - it is only input to help construct the search prompt. Wait for the user to share the
research results in their next message before continuing.

You SHALL NOT use a sub-agent or the task tool to perform this work.
