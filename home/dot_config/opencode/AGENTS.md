# Global Directives

## Core Rules

- Resolve minor ambiguity using available context and tools. Ask before proceeding when missing
  information could materially change the outcome; do not guess.
- Deliver what was asked, at the scope intended. MUST NOT expand into adjacent work, add unrequested
  features, or reframe the task.
- MUST NOT substitute a different approach when the requested one turns out to be hard, blocked, or
  unworkable. Full stop, report what blocked you and the options you see, and wait for direction. A
  change of direction requires explicit approval. Subagents report `blocked` to their caller instead
  of asking.
- Match user-facing written artifact length to substance. MUST NOT pad with filler sections,
  redundant summaries, or boilerplate. This rule does not govern prompts sent to subagents.
- Don't provide time estimates.

## Skills

MUST check the available skills list before any task. MUST load a matching skill BEFORE acting on
the governed task; skills loaded in parallel with that action arrive too late. MUST load skills
alone (never in parallel with other tool calls).

## Shell Search

MUST use `rg` (ripgrep) over `grep`. MUST use `rg --files -g` over `find -name`. Both are enforced
by tool guards that reject the blocked commands.

ripgrep is recursive by default; no flag enables it. `-r` is `--replace=REPLACEMENT`: it takes an
argument, so `rg -r "pattern" path/` consumes `pattern` as replacement text and searches for `path/`
instead. MUST NOT use `-r` or `-rl` for recursion. Common patterns:

```sh
rg "pattern" path/              # recursive content search (default)
rg -n "pattern" path/           # with line numbers
rg -l "pattern" path/           # files containing matches
rg -c "pattern" path/           # match count per file
rg -i / -w / -F "pattern"       # case-insensitive / whole-word / literal
rg -A3 -B3 "pattern"            # context lines after/before
rg --files -g "*.yaml" path/    # find files by glob (replaces find -name)
rg -g "*.py" "pattern" path/    # restrict search to a glob
rg --hidden -g "!**/.git/**"    # include dot-directories
```

## Agents

- Subagents MUST use their designated tools for repo exploration; MUST NOT clone repos or use local
  file tools on external repositories.
- Citations MUST be literal URLs fetched in the current session (via webfetch or a subagent's
  designated fetch tool). No bracket indices, no placeholder references, no carry-forward from prior
  turns or prior searches. If a URL was not fetched this session, the citation does not exist and
  MUST be omitted. Search results and snippets are discovery only; they do not make linked URLs
  citable. A missing citation beats an unverified one.
