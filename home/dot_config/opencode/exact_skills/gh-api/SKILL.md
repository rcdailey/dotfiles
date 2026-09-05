---
name: gh-api
description: >-
  Use when operating on the GitHub REST or GraphQL API via `gh api` for cases not covered by
  higher-level `gh` subcommands, including GitHub Discussions and other raw endpoints.
  Do NOT use for standard
  `gh pr`, `gh issue`, `gh release`, or `gh repo` workflows. Do NOT use for any PR review
  operations (reading comments, posting replies, managing reviews); use `gh-review` instead.
---

Use `gh pr create --draft` and `gh pr ready [--undo]` for draft status. Review comments belong to
`gh-pr-review`. Consult `gh api --help` for request flags; the global explicit-method rule applies to
REST and GraphQL alike.

## Output Filtering

Mutation responses (`POST`, `PATCH`, `PUT`, `DELETE`) return the full object by default, which
wastes context tokens. Always pipe through `--jq` to extract only the fields you need.

### General pattern

For any mutation, append `--jq` selecting the fields the caller actually needs. Typical minimal set:
`{id, body, html_url}`. Add `state`, `title`, or `number` when relevant.

## Discussions (GraphQL)

GraphQL queries use POST too; HTTP method alone does not classify GraphQL operation semantics.
Retrieve only needed fields and paginate when completeness matters:

```sh
gh api --method POST graphql -F owner=OWNER -F repo=REPO -f query='query(
  $owner: String!, $repo: String!
) {
  repository(owner: $owner, name: $repo) {
    discussions(first: 10) { nodes { number title url } }
  }
}'
```
