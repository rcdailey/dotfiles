---
name: linear-cli
description: >
  Use when managing Linear issues, projects, comments, labels, or relations from the command line
  using the linear CLI
---

CLI for managing Linear issues, projects, and workflows. Installed via mise; call with Bash.

## Markdown Content

Use file-based flags for descriptions and comments containing markdown:

- `--description-file` for `issue create` and `issue update`
- `--body-file` for `comment add` and `comment update`

This avoids shell escaping issues and literal `\n` in output. Only use `--description` or `--body`
for simple, single-line content.

```bash
cat > /tmp/description.md <<'EOF'
## Summary
- First item
EOF

linear issue create --title "My Issue" \
  --description-file /tmp/description.md
```

## Commands

```txt
linear issue              Issues (CRUD, comments, relations, attachments)
linear project            Projects (list, view, create, update, delete)
linear project-update     Project status updates
linear team               Teams (list, create, members, autolinks)
linear label              Labels (list, create, delete)
linear cycle              Cycles (list, view)
linear milestone          Milestones (CRUD)
linear initiative         Initiatives (CRUD, add/remove projects)
linear initiative-update  Initiative status updates (timeline posts)
linear document           Documents (CRUD)
linear config             Generate .linear.toml configuration
linear schema             Print GraphQL schema to stdout
linear api                Raw GraphQL API requests
```

Run `--help` on any command for flags and subcommands:

```bash
linear issue create --help
linear project list --help
```

## Gotchas

- `issue list` requires `--sort` (`manual` or `priority`), or set `LINEAR_ISSUE_SORT` env var. Also
  requires `--team <key>` unless inferred from directory.
- `--no-pager` only works on `issue list`.
- GraphQL queries with non-null type markers (e.g. `String!`) must use heredoc stdin to avoid shell
  escaping issues.

## GraphQL API Fallback

Prefer CLI commands for all supported operations. Use `linear api` only for queries not covered by
the CLI.

```bash
# Check schema
linear schema -o "${TMPDIR:-/tmp}/linear-schema.graphql"
rg -i "cycle" "${TMPDIR:-/tmp}/linear-schema.graphql"

# Simple query
linear api '{ viewer { id name email } }'

# Variables via heredoc
linear api --variable teamId=abc123 <<'GRAPHQL'
query($teamId: String!) { team(id: $teamId) { name } }
GRAPHQL

# Pipe to jq
linear api '{ issues(first: 5) { nodes { identifier title } } }' \
  | jq '.data.issues.nodes[].title'
```
