## Research CLI

Use `research` for external sources:

```txt
research web search "query"                           # sourced answer
research web search "query" --results                 # result snippets for source selection
research web fetch URL [--find "pattern"] [-C N] [--offset N]
research scout orient REPO [--brief]
research scout rg REPO PATTERN [--path P] [-g GLOB] [-C N] [-i] [-F]
research scout cat REPO PATH [--ref REF] [--offset N] [--limit N]
research pdf URL [--find "pattern"] [-C N] [--offset N]
```

Search queries MUST be one quoted argument. Do not pipe or chain commands. Run
`research <group> --help` only for unlisted operations or options.
