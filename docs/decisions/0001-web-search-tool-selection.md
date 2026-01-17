# ADR-0001: Web Search Tool Selection for OpenCode

- Status: Accepted
- Date: 2026-01-17

## Context

OpenCode requires a web search capability for AI-assisted research during coding sessions. The
search tool needs to integrate via MCP (Model Context Protocol) and balance several concerns:

- Token efficiency (search results consume context window)
- Result quality and source accuracy
- Reliability and rate limiting
- Cost (API pricing)

We evaluated three options: Tavily, Brave Search, and Exa.

## Options Considered

### Tavily

Remote MCP server with two search modes (basic/advanced).

Pros:

- Rich content snippets with code examples embedded
- Extracts YouTube transcripts
- Relevance scoring per result
- Can surface factual data (dates, prices, benchmarks) directly in snippets

Cons:

- Inconsistent basic mode behavior (sometimes returns verbose snippets regardless of setting)
- Advanced mode returns ~400 tokens per result (context pollution)
- Confused similar tool names in testing (returned OpenAI Codex docs for "opencode" query)
- LinkedIn/social media noise in results
- Extract tool has code block corruption issues

### Brave Search

Local MCP server via npx.

Pros:

- Consistently terse descriptions (1-2 sentences, ~40 tokens per result)
- Predictable token usage
- Better source accuracy (correctly identified official docs)
- Cleaner results (no social media aggregation noise)
- Multiple specialized search types available (news, video, image, local)

Cons:

- Requires page extraction via separate webfetch for full content
- Local npx process startup overhead

### Exa

Built-in OpenCode tool (experimental).

Pros:

- No additional MCP configuration needed
- Code-focused search option

Cons:

- Aggressive rate limiting (429 errors during testing)
- Experimental/unstable status

## Decision

Use **Brave Search** as the primary web search tool.

## Rationale

Our intended workflow is "lean search + targeted extraction":

1. Search returns minimal context (title, URL, brief description)
2. AI selects the most relevant URL(s)
3. Webfetch extracts full page content only when needed

This workflow minimizes context pollution when most search results won't be used. Brave's consistent
brevity (~40 tokens/result vs Tavily's ~400 tokens/result in advanced mode) makes it ideal for this
pattern.

Tavily's inconsistent basic mode and tendency to return verbose snippets regardless of settings made
it unreliable for the lean search strategy. While Tavily's rich snippets can be useful when the
snippet itself answers the question, this benefit doesn't outweigh the unpredictability.

## Consequences

### Positive

- Predictable token budget for search operations
- Two-step workflow (search + extract) gives finer control over context usage
- Cleaner source quality in results

### Negative

- Extra round-trip for extraction when full content is needed
- Brave API key required (free tier available)

### Neutral

- Tavily API key no longer needed (can be removed from secrets)
- Exa remains available but disabled; can be re-enabled if stability improves
