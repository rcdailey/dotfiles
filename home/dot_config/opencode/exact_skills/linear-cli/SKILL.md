---
name: linear-cli
description: >-
  Use when operating on the Linear issue tracker via the `linear` CLI: creating, viewing, querying,
  or updating issues, projects, milestones, labels, or documents; adding or editing issue comments;
  assigning, labeling, or transitioning issues; listing team members. Triggers on phrases like
  "create a Linear issue", "file a ticket", "update ENG-###", "move to Ready For Dev", "add a
  comment to the Linear issue", or any task naming Linear, a Linear issue key (`ENG-`, `OPS-`,
  etc.), a Linear project, or a Linear milestone. Do NOT use for GitHub Issues, Jira, or other
  trackers.
---

# Linear CLI

Use `linear` for Linear issue tracker operations. Lines below are usage signatures (not examples):
`<required>`, `[optional]`. Run `linear <group> <cmd> -h` for the full flag set.

- Groups: `issue`, `team`, `project`, `milestone`, `label`, `document`

```txt
linear team members [teamKey]
linear project list [--all-teams] [--team KEY] [--status NAME]
linear label list [--all | --team KEY | --workspace]
linear issue view [ID] [-w] [-a]
linear issue query [--search TERM] [-s STATE] [--project NAME] [--assignee USER] [--limit N]
linear issue create <-t title> <-d desc> [-s STATE] [--project NAME] [--milestone NAME]
                    [-l LABEL]... [--estimate N] [--assignee self|USER] [--no-interactive]
linear issue update <ID> [-t title] [-d desc] [-s state] [--priority 1-4] [-a assignee]
                    [-l LABEL]... [--parent ID]
linear issue comment add [ID] <-b body> [-p parent-comment-id]
linear issue comment update <commentId> <-b body>
linear issue comment list [ID]
linear issue relation add <ID> <blocked-by|blocks|related|duplicate> <relatedID>
linear issue relation delete <ID> <relationType> <relatedID>
linear issue relation list [ID]
linear issue link <urlOrID> [url] [-t TITLE]
```

## Linking issues

Three distinct mechanisms; pick by intent:

- `linear issue relation add` for issue-to-issue semantics (`blocked-by`, `blocks`, `related`,
  `duplicate`). Use for dependency graphs and duplicate merges.
- `linear issue update <ID> --parent <parentID>` for parent/child hierarchy (sub-issues).
- `linear issue link` for issue-to-URL attachments (GitHub PRs, design docs, external refs); `-t`
  sets a custom display title.

## Create in one shot

`linear issue create` accepts every field the issue needs at birth. Gather title, state, labels,
project, milestone, estimate, assignee, and description, then issue one `create` call. Do NOT create
a bare issue and patch it with follow-up `linear issue update` invocations to set state or labels;
that is the failure mode this skill exists to prevent.

Checklist before calling `create`:

- Title (including any template prefix such as `BE:`, `FE:`)
- `-s` state (e.g. `Ready For Dev`) if the issue should not land in Triage
- `-l` labels (repeat the flag per label) if the template requires them
- `--project` and `--milestone` when applicable
- `--estimate` and `--assignee` when known
- `--no-interactive` for scripted/agent use

Pass the description inline via `-d` with a quoted heredoc; this keeps creation to a single tool
turn and avoids a temp-file round trip. Quote the delimiter (`'EOF'`) so `$`, backticks, and
backslashes in the markdown pass through literally.

Place `-d` last so the flag block stays compact and the body trails:

```bash
linear issue create \
  -t "BE: Medscape OIDC processor and client config" \
  -s "Ready For Dev" \
  --project "Medscape" --milestone "SSO" \
  -l "Product" -l "Feature Work" -l "Back end" \
  --estimate 3 --assignee self --no-interactive \
  -d "$(cat <<'EOF'
## Goal

Multi-line markdown body goes here.
EOF
)"
```

Fall back to `--description-file PATH` only when the body contains a literal `EOF` line that would
terminate the heredoc, or when the description has already been written to disk for unrelated
reasons.

## Discovery before mutation

Run `linear <group> <cmd> -h` to confirm current flags before assuming a field must be set via a
follow-up command. Most "missing" capabilities on `create` and `update` are just flags that were not
checked first.

## Comments and updates

Use `linear issue comment add` for new threads and `-p <parent-comment-id>` to reply. Reach for
`linear issue update` only for fields that genuinely change after creation (state transitions
mid-work, reassignments, parent linkage), not to finish configuring a newly created issue.
