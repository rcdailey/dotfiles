---
description: Build a Perplexity search prompt for research or answers on a topic
---

# Research Prompt Builder

**Target Topic**: $ARGUMENTS (if provided) or inferred from recent discussion/problems

## Execution Protocol

**OUTPUT MODE**: Return ONLY the search prompt - no additional text, explanations, or boilerplate

**WORKFLOW PAUSE**: After generating the prompt, pause all current work and wait for user to provide
search results

## Task Flow

1. **Parse input**: Check if topic argument is provided
2. **Topic determination**:
   - If argument provided: Use it as the research topic
   - If no argument: Analyze recent conversation context, current problems, or code being worked on
     to infer what needs research
3. **Prompt construction**: Build an optimized Perplexity search prompt that:
   - Is specific and focused on the topic
   - Requests comprehensive, actionable information
   - Asks for current best practices, tools, or solutions
   - Includes relevant context keywords for better results
4. **Output**: Return only the search prompt text
5. **Pause**: Stop all current activities and wait for user to provide search results

## Prompt Construction Guidelines

**Structure**: Create prompts that are:

- Direct and specific to the topic
- Request comprehensive coverage of the subject
- Ask for current/recent information when relevant
- Include practical examples or implementations
- Request authoritative sources when applicable

**Format**: Plain text search query optimized for Perplexity's capabilities

## Rules

- Never include explanatory text around the prompt
- Never add "Here's your search prompt:" or similar prefixes
- Never add suggestions for how to use the prompt
- Output must be ready to copy/paste directly into Perplexity
- Pause all other work until search results are provided
- Focus on creating comprehensive, well-structured search queries
