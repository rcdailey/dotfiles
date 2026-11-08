# ADR-0002: Tavily Advanced Search for the Researcher

- Status: Accepted
- Date: 2026-11-08
- Supersedes: ADR-0001

The researcher's `research web search` uses Tavily with advanced depth on every query, with no
per-query depth choice. Replaying the queries of a researcher session against both depths, advanced
returned 48 distinct on-topic pages against basic's 28, and fewer off-topic results (51 of 150
against 83 of 144). A depth option would leave the model to pick the cheaper, weaker mode.

Advanced costs 2 credits per query instead of 1. At the observed ~800 searches a month this exceeds
the free 1,000 credits by an estimated 600 to 1,100 credits, about $5 to $9 a month at pay-as-you-go
rates; this cost was accepted.

Results below a relevance score of 0.3 are hidden. In the same replay this kept 72 of 79 on-topic
results and dropped 39 of 51 off-topic ones. Queries containing `OR` are rejected before spending
credits: Tavily treats it as a plain word and returns unrelated results.

Tavily does not index Hacker News, Mastodon, or X posts usefully; covering those needs
platform-specific search, not a Tavily setting.
