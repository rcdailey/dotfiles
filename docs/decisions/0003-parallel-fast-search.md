# ADR-0003: Parallel Fast Search for the Researcher

- Status: Accepted
- Date: 2026-11-22
- Supersedes: ADR-0002

The researcher's `research web search` uses Parallel's Search API in fast mode. Microsoft Learn
routing is unchanged. When local page fetching fails, `research web fetch` falls back to Parallel's
Extract API, so the researcher depends on one search vendor and no longer uses Tavily.

Researcher sessions from 2026-09-03 to 2026-11-22 made 1,412 searches. Of these, 1,014 were
replayable: unique queries that returned results, excluding failed or budget-blocked calls and
searches routed to Microsoft Learn. `research eval` replayed 120 of them, sampled with
domain-filtered and open queries in their real proportions, with their original domain and date
filters, against eleven provider configurations. Claude Haiku 5.5 graded each query's pooled top
five results from 0 to 2, given the caller's task and the fetched page, without knowing the
provider. On 200 results that Claude Sonnet 5.5 had also graded, Haiku agreed exactly 80% of the
time and was never more than one grade off.

| Configuration     | nDCG@5 | Difference from Tavily (95% CI) | p50 latency | Price per 1,000 |
| ----------------- | ------ | ------------------------------- | ----------- | --------------- |
| Parallel advanced | 0.757  | +0.079 (+0.042, +0.116)         | 2.2 s       | $5              |
| Parallel fast     | 0.753  | +0.075 (+0.033, +0.116)         | 1.8 s       | $1              |
| Parallel basic    | 0.748  | +0.070 (+0.033, +0.107)         | 2.8 s       | $5              |
| Exa auto          | 0.743  | +0.064 (+0.016, +0.115)         | 3.0 s       |                 |
| Keenable pro      | 0.723  | +0.045 (-0.001, +0.088)         | 1.6 s       |                 |
| Parallel turbo    | 0.714  | +0.035 (-0.002, +0.072)         | 0.6 s       | $1              |
| Perplexity        | 0.712  | +0.034 (-0.009, +0.073)         | 1.7 s       |                 |
| Brave             | 0.701  | +0.023 (-0.021, +0.064)         | 0.7 s       |                 |
| Tavily advanced   | 0.678  |                                 | 4.4 s       | $16             |
| Linkup standard   | 0.668  | -0.010 (-0.048, +0.029)         | 2.9 s       |                 |
| Firecrawl         | 0.601  | -0.077 (-0.122, -0.035)         | 4.9 s       |                 |

Fast, basic, and advanced are indistinguishable on quality, and fast costs a fifth as much. Tavily
led only on recall of the pages the original sessions fetched (69% in the top five, against 58% for
Parallel fast), and those pages came from Tavily's own results.

Every provider received the researcher's query unchanged. Parallel documents a separate
natural-language objective plus short keyword queries as its best input, so it may do better if the
tool ever asks the agent for an objective.

Uncapped fast-mode excerpts averaged about 25,000 characters per search, twice Tavily's. Requests
now cap excerpts at 1,200 characters per requested result, and every search route, including
Microsoft Learn, shares that budget. Search output also drops repeated pages (tracking-parameter
variants and mirrors) and markup noise. The 120-query evaluation ran uncapped; reruns go through the
production adapter and measure the capped configuration.

Parallel has no exact-phrase filter, so the search tool no longer offers `exact` (6 of the 1,412
searches used it). Parallel handles `OR` in a query, so the search tool no longer rejects it.

## Rerunning the comparison

Rerun before changing providers again. Queries come from private sessions, so data stays outside the
repository; this evaluation is archived read-only in `~/.local/share/research-eval/2026-11-22`, and
the table above is its `report --baseline tavily`. Use a new directory for each study, because
`collect` refuses to replace an existing query set:

```sh
dir=~/.local/state/research-eval/$(date +%F)
research eval --dir "$dir" collect       # free
research eval --dir "$dir" run           # paid: one call per query per provider
research eval --dir "$dir" judge         # paid: one NanoGPT LLM call per pooled result
research eval --dir "$dir" report        # free; --baseline picks the comparison column
```

Provider keys come from `<NAME>_API_KEY` or `rbw get <name>-api-key`; the judge reads
`NANO_GPT_API_KEY` or the rbw item `NanoGPT API Key`. `run` and `judge` resume after failures
without repeating finished calls.
