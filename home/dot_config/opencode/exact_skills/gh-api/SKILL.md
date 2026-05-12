---
name: gh-api
description: >-
  Use when operating on the GitHub REST or GraphQL API via `gh api` for cases not covered by
  higher-level `gh` subcommands: creating or managing draft pull requests, posting pull request
  review-body or issue comments programmatically, querying or mutating GitHub Discussions, or
  any GitHub API call requiring raw endpoints. Do NOT use for standard `gh pr`, `gh issue`,
  `gh release`, or `gh repo` workflows, or for PR review comments (use `gh-pr-review` instead).
---

## Output Filtering

Mutation responses (`POST`, `PATCH`, `PUT`, `DELETE`) return the full object by default, which
wastes context tokens. Always pipe through `--jq` to extract only the fields you need.

### Reply to a PR review comment (minimal output)

```sh
gh api --method POST \
  repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies \
  -f body="Comment text" \
  --jq '{id, body, html_url}'
```

### Create a conversation comment (minimal output)

```sh
gh api --method POST \
  repos/{owner}/{repo}/issues/{number}/comments \
  -f body="Comment text" \
  --jq '{id, body, html_url}'
```

### General pattern

For any mutation, append `--jq` selecting the fields the caller actually needs. Typical minimal set:
`{id, body, html_url}`. Add `state`, `title`, or `number` when relevant.

## Draft Pull Requests

### Create a draft PR

```sh
gh api --method POST repos/:owner/:repo/pulls \
  -f title="My new feature" -f body="Description of changes" \
  -f head="feature-branch" -f base="main" -F draft=true \
  --jq '{number, title, html_url, draft}'
```

For cross-repo PRs, use `head="username:branch"`.

### Get PR details

```sh
gh api repos/:owner/:repo/pulls/<number> --jq '{draft, state, title}'
```

### Convert draft to ready for review

```sh
gh api --method PATCH repos/:owner/:repo/pulls/<number> -F draft=false \
  --jq '{number, title, html_url, draft}'
```

Note: Cannot convert back to draft via API once marked ready.

### List open draft PRs

```sh
gh api repos/:owner/:repo/pulls --jq '.[] | select(.draft) | {number, title}'
```

### List my open PRs in a repo

```sh
gh api repos/:owner/:repo/pulls -f state=open --jq '.[] | select(.user.login=="USERNAME") | {number, title, draft}'
```

## PR Conversation Comments

Comments on the PR timeline (not on specific lines of code). For creating comments, see the Output
Filtering examples above.

### List conversation comments

```sh
gh api repos/:owner/:repo/issues/<number>/comments --jq '[.[] | {id, author: .user.login, body}]'
```

## Discussions (GraphQL)

List discussions:

```sh
gh api graphql -f query='query($owner:String!,$repo:String!) { repository(owner:$owner,name:$repo) { discussions(first:10) { nodes { number title url } } } }' -F owner=OWNER -F repo=REPO
```

View discussion:

```sh
gh api graphql -f query='query($owner:String!,$repo:String!,$number:Int!) { repository(owner:$owner,name:$repo) { discussion(number:$number) { title body comments(first:10) { nodes { body author { login } } } } } }' -F owner=OWNER -F repo=REPO -F number=NUM
```

Search discussions:

```sh
gh api graphql -f query='query($q:String!) { search(query:$q,type:DISCUSSION,first:10) { nodes { ...on Discussion { number title url } } } }' -f q="repo:OWNER/REPO QUERY"
```
