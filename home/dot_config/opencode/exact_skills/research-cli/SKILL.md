---
name: research-cli
description: >
  Use when a permitted specialist performs external web, PDF, or GitHub research through the
  research_* tools. Covers evidence retrieval, source eligibility, budget handling, and recovery. Do
  not use for bounded Context7 lookups or local repository exploration.
---

# Research CLI

Use search to discover sources, then retrieve the relevant source before relying on it. Apply the
global citation rule; a search result or snippet is not evidence for its linked URL.

## Workflow

1. Identify the evidence tracks and source types required by the caller.
2. Search with `research_search`, using `results` for a ranked source list.
3. Retrieve relevant sources with `research_fetch`; it handles web pages, PDFs, and GitHub object
   URLs.
4. Retrieve a direct primary result matching the target before broad repository exploration.
5. For GitHub repositories, start with the narrowest applicable `research_github` command. Use
   `orient`, then `find`, before path-specific `rg` or `cat` calls when paths are unknown.
6. For changes absent upstream, run `forks` with `--grep` or `--path`, then inspect matches with
   `commit`.

Call `research_search` and `research_fetch` sequentially so each budget checkpoint can shape the
next call.

Before responding, call `research_ledger`. Cite only URLs listed under Sources, and include every
Errors entry in the Errors section.

## Evidence

- Prefer current primary sources for behavior, versions, defaults, and support status.
- Corroborate vendor comparisons with independent evidence when the distinction affects the answer.
- Treat a community theme as repeated only after retrieving independent discussions from at least
  two venues. Otherwise label it anecdotal or not established.
- To support an absence claim, search every source category named by the caller and report the
  attempted categories and missing evidence.
- Preserve source version, date, repository ref, and vendor affiliation when material.

## Budget and output bounds

Search and fetch calls are budgeted; GitHub calls and cached pagination are free. Each budgeted call
reports current usage. After a warning, synthesize unless one named evidence gap justifies a single
sequential `critical` call.

When the evidence target names a field, option, symbol, or phrase, start page retrieval with
`find`. Use `offset` to paginate cached content. Do not disable output bounds when a narrower
query or page can answer the question.

## Recovery

- After a missing GitHub path, run `find`; do not guess another path.
- If search results miss the required source type, narrow the next query to a named source or domain.
- A no-match fetch is failed evidence. Retry without `find` or with a corrected pattern.
- A partial aggregate warning means that command is incomplete evidence.
- A budget guard is a workflow limit, not evidence that the requested source does not exist.
