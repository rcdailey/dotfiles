---
name: gh-api
description: GitHub API calls for discussions and PR comments (non-standard gh CLI patterns)
---

## PR Comments

Get inline code review comments:

```sh
gh api repos/:owner/:repo/pulls/<number>/comments
```

Get PR conversation thread comments:

```sh
gh api repos/:owner/:repo/issues/<number>/comments
```

## Discussions (GraphQL)

List discussions:

```sh
gh api graphql -f query='query($owner:String!,$repo:String!) {repository(owner:$owner,name:$repo){discussions(first:10) {nodes{number title url}}}}' -F owner=OWNER -F repo=REPO
```

View discussion:

```sh
gh api graphql -f query='query($owner:String!,$repo:String!,$number:Int!) {repository(owner:$owner,name:$repo){discussion(number:$number) {title body comments(first:10){nodes{body author{login}}}}}}' -F owner=OWNER -F repo=REPO -F number=NUM
```

Search discussions:

```sh
gh api graphql -f query='query($q:String!){search(query:$q,type:DISCUSSION, first:10){nodes{...on Discussion{number title url}}}}' -f q="repo:OWNER/REPO QUERY"
```
