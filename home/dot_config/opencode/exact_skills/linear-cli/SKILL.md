---
name: linear-cli
description: >-
  Use when operating on Linear via the `linear` CLI: issues, projects, milestones,
  documents, comments, relations, links, labels, teams, states. Triggers on Linear
  issue keys (`ENG-`, `OPS-`), "file a ticket", "create/update/search issues",
  "list milestones", "link a PR to the issue", or any task naming Linear. Do NOT
  use for GitHub Issues, Jira, or other trackers.
---

# Linear CLI

Python CLI wrapping the Linear GraphQL API. Authenticates via stored OAuth token
(`linear auth login`) or `LINEAR_API_KEY` env var. Run `linear <group> <cmd> -h`
for the full flag set.

```txt
linear me
linear auth login [--oauth | --api-key] [--port N]
linear auth logout
linear auth status
linear teams list
linear teams members <TEAM_KEY>
linear states list [--team KEY]
linear labels groups
linear labels list [--group NAME]...
linear issues list [--team KEY] [--state TYPE] [--assignee USER] [--label NAME]
                   [--cycle CYCLE] [--estimate EST] [--limit N]
linear issues search <QUERY> [--team KEY] [--state TYPE] [--assignee USER]
                     [--label NAME] [--cycle CYCLE] [--estimate EST] [--limit N]
linear issues view <ID>
linear issues create --title TEXT --team KEY [--description TEXT] [--state NAME]
                     [--priority 0-4] [--assignee USER] [--label NAME]...
                     [--parent ID] [--estimate N] [--project NAME]
                     [--milestone NAME]
linear issues update <ID> [--title TEXT] [--state NAME] [--priority 0-4]
                     [--assignee USER] [--add-label NAME]...
                     [--remove-label NAME]... [--estimate N] [--parent ID]
                     [--project NAME] [--milestone NAME]
linear comments list <ISSUE_ID>
linear comments add <ISSUE_ID> --body TEXT [--parent COMMENT_ID]
linear comments edit <COMMENT_ID> --body TEXT
linear relations list <ISSUE_ID>
linear relations add <ISSUE_ID> <TYPE> <RELATED_ID>
linear relations remove <ISSUE_ID> <TYPE> <RELATED_ID>
linear links list <ISSUE_ID>
linear links add <ISSUE_ID> <URL> [--title TEXT]
linear links remove <LINK_ID>
linear projects list [--team KEY]
linear projects view <ID_OR_NAME>
linear milestones list --project <NAME_OR_UUID>
linear milestones create --project <NAME_OR_UUID> --name TEXT [--description TEXT]
                         [--target-date YYYY-MM-DD]
linear milestones update <ID> [--name TEXT] [--description TEXT]
                         [--target-date YYYY-MM-DD]
linear milestones delete <ID>
linear documents list [--project NAME]
linear documents view <ID>
linear api <QUERY> [--var key=value]...
```

## Auth

`linear auth login` opens the browser for OAuth (when `LINEAR_CLIENT_ID` is set)
or prompts for an API key. Tokens are stored at
`~/.local/state/linear-cli/tokens.json`. `LINEAR_API_KEY` env var overrides
stored credentials when set.

## Identifier resolution

The CLI resolves human-readable names to UUIDs internally. Never pass UUIDs for
teams, states, or labels; use display names or keys instead.

- `--team` takes a team key (e.g. `ENG`), not a UUID
- `--state` on `issues list` takes a state type (`triage`, `backlog`, `unstarted`,
  `started`, `completed`, `canceled`)
- `--state` on `issues create` and `issues update` takes a display name
  (e.g. `"Ready For Dev"`, `"In Progress"`)
- `--assignee` accepts `me` (resolves via viewer query) or a user UUID
- `--label` takes a label display name, case-insensitive
- `--project` takes a project display name
- `--milestone` takes a milestone display name, resolved within the project
- `--cycle` takes `active`, `previous`, or an integer cycle number; requires `--team`
- `--estimate` takes `none` (unestimated) or a numeric value

## Create in one shot

`linear issues create` accepts every field the issue needs at birth. Gather title,
state, labels, assignee, and description, then issue one `create` call. Do NOT
create a bare issue and patch it with `linear issues update` to set state or labels;
that is the failure mode this skill exists to prevent.

Checklist before calling `create`:

- `--title` (including any template prefix such as `BE:`, `FE:`)
- `--state` display name if the issue should not land in Triage
- `--label` (repeat per label) if the template requires them
- `--priority`, `--assignee`, `--estimate` when known
- `--project` when applicable
- `--milestone` when the project has milestones (requires `--project`)
- `--description` for the issue body (markdown)

Pass the description inline with a quoted heredoc:

```bash
linear issues create \
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

Relation types for `linear relations add/remove`: `blocks`, `blocked-by`,
`related`, `duplicate`.

## Sub-issues

`linear issues view` shows parent and sub-issues inline. Parent appears as a
field; children appear as a summary list with state, priority, assignee, labels,
and estimate. Use `--parent` on `create` or `update` to set the hierarchy.

## Milestones

Milestones are scoped to a project. `--project` accepts a display name or UUID.
`projects view` includes milestones inline. Milestone IDs (UUIDs) are required for
`update` and `delete`; get them from `milestones list` output or `linear api`.

## Linking issues

Three distinct mechanisms; pick by intent:

- `linear relations add` for issue-to-issue semantics (`blocked-by`, `blocks`,
  `related`, `duplicate`). Use for dependency graphs and duplicate merges.
- `linear issues update <ID> --parent <parentID>` for parent/child hierarchy
  (sub-issues).
- `linear links add` for issue-to-URL attachments (GitHub PRs, design docs,
  external refs).

## Comments and updates

Use `linear comments add` for new threads and `--parent` to reply to an existing
comment. `linear comments edit` updates an existing comment's body. Use
`linear issues update` only for fields that change after creation (state
transitions, reassignments, label changes, parent linkage).

## Raw API access

`linear api` executes arbitrary GraphQL queries and mutations. Output is JSON.
Pass variables with `--var key=value`. Read query from stdin with `-`.

## Searching vs listing

`linear issues search` does full-text relevance-ranked search across titles,
descriptions, and comments via Linear's `issueSearch` API. Use it to find issues
by keyword. `linear issues list` filters by structured fields (team, state,
assignee, label) without text matching. Combine search with filters:

```bash
linear issues search "multiple images" --team ENG --state started
```

## Discovery before mutation

Run `linear teams list`, `linear states list --team KEY`, or `linear labels groups`
to discover available values before creating or updating issues. Labels are
workspace-scoped (no `--team` filter). Use `linear labels list --group "Ticket Type"`
to see choices within a specific label group.
