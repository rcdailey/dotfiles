---
name: research-cli
description: >
  Use when a permitted specialist performs external web, PDF, or GitHub research through the
  research CLI. Covers evidence retrieval, source eligibility, budget handling, and recovery. Do
  not use for bounded Context7 lookups or local repository exploration.
---

# Research CLI

Use search to discover sources, then retrieve the relevant source before relying on it. Apply the
global citation rule; a search result or snippet is not evidence for its linked URL.

## Workflow

1. Identify the evidence tracks and source types required by the caller.
2. Search with `research web search "query" --results --max-results 5`.
3. Fetch relevant pages with `research web fetch URL`; use `research pdf URL` for PDFs.
4. For GitHub repositories, start with the narrowest applicable Scout command. Use `orient`, then
   `find`, before path-specific `rg` or `cat` calls when paths are unknown.
5. Before reporting, run `research report`. Cite only eligible sources and disclose retrieval
   failures or incomplete aggregate output.

Run `research <group> --help` for syntax beyond these common forms. Each shell command must contain
one `research` invocation; do not chain, pipe, background, or suppress errors.

## Evidence

- Prefer current primary sources for behavior, versions, defaults, and support status.
- Corroborate vendor comparisons with independent evidence when the distinction affects the answer.
- Treat a community theme as repeated only after retrieving independent discussions from at least
  two venues. Otherwise label it anecdotal or not established.
- To support an absence claim, search every source category named by the caller and report the
  attempted categories and missing evidence.
- Preserve source version, date, repository ref, and vendor affiliation when material.

## Budget and output bounds

Web and PDF calls are budgeted; Scout calls and cached pagination are free. Use `research status`
before a batch that could cross a checkpoint or warning. After a warning, synthesize unless one
named evidence gap justifies a single sequential `--critical` call.

When the evidence target names a field, option, symbol, or phrase, start page retrieval with
`--find`. Use `--offset` to paginate cached content. Do not disable output bounds when a narrower
query or page can answer the question.

## Recovery

- After a missing Scout path, run `scout find`; do not guess another path.
- After two failed searches for one track, change source type or report the gap.
- A partial aggregate warning means that command is incomplete evidence.
- A budget guard is a workflow limit, not evidence that the requested source does not exist.
