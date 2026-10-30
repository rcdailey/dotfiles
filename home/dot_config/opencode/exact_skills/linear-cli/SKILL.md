---
name: linear-cli
description: >-
  Use when operating on Linear via the `linear` CLI: issues, projects, milestones,
  project updates, documents, comments, relations, links, labels, teams, states.
  Triggers on Linear issue keys (`ENG-`, `OPS-`), "file a ticket",
  "create/update/search issues", "list milestones", "project update",
  "link a PR to the issue", or any task naming Linear. Do NOT use for GitHub Issues,
  Jira, or other trackers.
---

# Linear CLI

Python CLI wrapping the Linear GraphQL API. Before the first `linear` call, run `linear --help`
once: it prints every command with its arguments, options, defaults, and option notes. Do not run
per-command `-h`. This skill covers only workflow and semantics that help omits.

## Auth

`linear auth login` stores tokens in `~/.local/state/linear-cli/tokens.json`; OAuth requires
`LINEAR_CLIENT_ID`. `LINEAR_API_KEY` overrides stored credentials when set.

## Identifier resolution

The CLI resolves names to UUIDs internally. Pass display names or keys for teams, states, labels,
projects, and milestones; never look up UUIDs first.

- `--label` matches case-insensitively on `create` and `update`, but exactly on `list` and `search`.
- `--cycle` requires `--team`.

## Create in one shot

`linear issue create` accepts every field the issue needs at birth. Gather title, state, labels,
assignee, and description, then issue one `create` call. Do NOT create a bare issue and patch it
with `linear issue update` to set state or labels; that is the failure mode this skill exists to
prevent.

- Include any template prefix (`BE:`, `FE:`) in `--title`.
- Without `--state`, the issue lands in Triage.
- Set `--milestone` when the project has milestones.

Pass the description inline with a quoted heredoc:

```bash
linear issue create \
  --title "BE: Medscape OIDC processor and client config" \
  --team ENG \
  --state "Ready For Dev" \
  --label "Product" --label "Feature Work" --label "Back end" \
  --priority 2 --assignee me --estimate 3 \
  --project "Sprint 42" \
  --description "$(cat <<'EOF'
## Goal

Multi-line markdown body goes here.
EOF
)"
```

## Priority values

0 = No priority, 1 = Urgent, 2 = High, 3 = Medium, 4 = Low.

## Relations

`issue create` creates the issue and its relation atomically: if any relation fails, nothing is
created, so fix the reference and rerun the whole command.

Linear stores a relation once, on the source issue. `blocked-by` is that same row read from the
other side, so the CLI resolves it by swapping the two issues. `relation list` shows both
directions.

## Sub-issues

`linear issue view` shows the parent and sub-issues inline; no separate lookup is needed.

## Milestones

Drill down top-down: `project view` groups issues under each milestone (plus a "no milestone" group)
with an `open: N/M` count and the top open issues. When a group is cut, its `+N more:` line prints
the exact command for the rest; run that instead of guessing. Milestone IDs (UUIDs) are required for
`update` and `delete`; get them from `milestone list` output.

## Linking issues

Three distinct mechanisms; pick by intent:

- `linear relation add` for issue-to-issue semantics. Use for dependency graphs and duplicate
  merges.
- `linear issue update <ID> --parent <PARENT-ID>` for parent/child hierarchy (sub-issues).
- `linear link add` for issue-to-URL attachments (GitHub PRs, design docs, external refs).

## Comments and updates

`linear issue view` shows only a comment count; add `--comments` to read them in the same call.
Comment output shows each ID, nests replies under their thread root, and marks threads synced with
an external service (e.g. `synced: slack`). `comment add --parent <root ID>` replies in that thread
and its synced copy.

To change an existing title or description, edit the file named on the last line of
`linear issue view` output (`edit file: <path>`), then run
`linear issue update <ID> --from-file <path>`. Never resend the full description inline.

- The `# ` line is the title; everything below it is the description. Leave the frontmatter alone.
- `view` output already shows the file's title and description verbatim. MUST NOT read the file;
  edit it directly. Read it only after an edit fails because its old text did not match.
- Keep each paragraph and list item on one line; never hard-wrap the description.
- Other `update` flags combine with `--from-file`; `--title` and `--description` do not.
- If the update reports the issue changed since the view, view again and redo the edits on the new
  file.

Pass multiple issue IDs to assign one project or milestone in a batch. Multi-issue updates accept
only `--project` and `--milestone`; a bad ID is reported while the valid issues still update.

Never chain mutations with `&&`; an earlier mutation remains applied if a later one fails. Run
independent verification reads separately so one timeout does not skip the remaining checks.

## Project context

`project view` also shows external links (PRDs, designs), content, and the 3 most recent project
updates.

## Raw API access

Use `linear api` only when `linear --help` shows no command for the data. Pass `-` as the query to
read it from stdin. `issue view --json` writes no edit file.

## Discovery before mutation

When creating issues within a project, `linear project view <name>` returns teams and their workflow
states in one call; no separate `team list` or `state list` needed. Labels are workspace-scoped: run
`linear label groups`, then `label list --group <name>`.
