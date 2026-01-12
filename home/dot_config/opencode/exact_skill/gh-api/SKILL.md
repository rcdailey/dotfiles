---
name: gh-api
description: GitHub API calls for discussions and PR comments (non-standard gh CLI patterns)
---

## Pull Requests

### Create a draft PR

```sh
gh api --method POST repos/:owner/:repo/pulls -f title="My new feature" -f body="Description of changes" -f head="feature-branch" -f base="main" -F draft=true
```

For cross-repo PRs, use `head="username:branch"`.

### Get PR details (check if draft)

```sh
gh api repos/:owner/:repo/pulls/<number>
```

Response includes `"draft": true|false` and `"state": "open|closed"`.

### Check if PR is draft (minimal output)

```sh
gh api repos/:owner/:repo/pulls/<number> --jq '{draft, state, title}'
```

### Convert draft to ready for review

```sh
gh api --method PATCH repos/:owner/:repo/pulls/<number> -F draft=false
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

## PR Review Comments

Inline code review comments on the diff (not conversation thread comments).

### List comments on a PR

```sh
gh api repos/:owner/:repo/pulls/<number>/comments
```

### Get a specific comment

```sh
gh api repos/:owner/:repo/pulls/comments/<comment_id>
```

### Create a single-line comment

```sh
gh api --method POST repos/:owner/:repo/pulls/<number>/comments -f body="Comment text" -f commit_id="<sha>" -f path="path/to/file.txt" -F line=42 -f side="RIGHT"
```

- `side`: `RIGHT` for additions/context, `LEFT` for deletions
- `commit_id`: Use HEAD commit of PR branch

### Create a multi-line comment

```sh
gh api --method POST repos/:owner/:repo/pulls/<number>/comments -f body="Comment spanning lines 10-15" -f commit_id="<sha>" -f path="path/to/file.txt" -F start_line=10 -f start_side="RIGHT" -F line=15 -f side="RIGHT"
```

### Update a comment (edit body only)

```sh
gh api --method PATCH repos/:owner/:repo/pulls/comments/<comment_id> -f body="Updated comment text"
```

Note: Cannot change line position. To move a comment, delete and recreate.

### Delete a comment

```sh
gh api --method DELETE repos/:owner/:repo/pulls/comments/<comment_id>
```

### Reply to a comment thread

```sh
gh api --method POST repos/:owner/:repo/pulls/<number>/comments/<comment_id>/replies -f body="Reply text"
```

Only works on top-level comments, not replies to replies.

## PR Reviews (Batch Comments)

Create a review with multiple comments at once.

### Create a pending (draft) review

Omit `event` to create a PENDING review that isn't submitted:

```sh
gh api --method POST repos/:owner/:repo/pulls/<number>/reviews -f body="Review summary" -f 'comments=[{"path":"file1.txt","line":10,"body":"First comment"},{"path":"file2.txt","line":20,"body":"Second comment"}]'
```

### Submit a pending review

```sh
gh api --method POST repos/:owner/:repo/pulls/<number>/reviews/<review_id>/events -f event="COMMENT"
```

Events: `COMMENT`, `APPROVE`, `REQUEST_CHANGES`

### Create and submit review in one call

```sh
gh api --method POST repos/:owner/:repo/pulls/<number>/reviews -f body="Looks good!" -f event="APPROVE" -f 'comments=[{"path":"file.txt","line":5,"body":"Nice change"}]'
```

### List reviews on a PR

```sh
gh api repos/:owner/:repo/pulls/<number>/reviews
```

### Delete a pending review

Only works for PENDING (unsubmitted) reviews:

```sh
gh api --method DELETE repos/:owner/:repo/pulls/<number>/reviews/<review_id>
```

## PR Conversation Comments

Comments on the PR timeline (not on specific lines of code).

### List conversation comments

```sh
gh api repos/:owner/:repo/issues/<number>/comments
```

### Create a conversation comment

```sh
gh api --method POST repos/:owner/:repo/issues/<number>/comments -f body="Comment text"
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
