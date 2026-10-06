---
name: discord-chat
description: >-
  Use when the user provides a discord.com/channels/<server>/<channel> link or a Discord message
  link and asks to inspect, fetch, search, summarize, or use the linked conversation. Do NOT use
  for Discord application, bot, webhook, or server administration.
---

# Discord chat retrieval

Export the week preceding the referenced point to a local plain-text file. Search and read that file
instead of repeatedly calling Discord or loading the entire conversation into context.

## Input

Accept these URL shapes:

- Channel: `https://discord.com/channels/<server-id>/<channel-id>`
- Message: `https://discord.com/channels/<server-id>/<channel-id>/<message-id>`

mise supplies `DISCORD_TOKEN` to the exporter from `~/.config/mise/config.local.toml`. Never print,
read, or pass it on the command line.

## Export

Run once, substituting the URL verbatim:

```sh
~/.config/opencode/skills/discord-chat/export.py '<discord-url>'
```

When the rolling window is insufficient, bound a channel export with ISO-8601 timestamps:

```sh
~/.config/opencode/skills/discord-chat/export.py '<discord-channel-url>' \
  --after '2026-08-17T16:06:00Z' --before '2026-08-24T16:06:00Z'
```

The command invokes `DiscordChatExporter.Cli` through mise and writes plain text without media under
`/tmp/opencode`:

- Channel link: seven days ending when the command starts
- Message link: seven days preceding the linked message, including that message
- Explicit channel range: `--after` through `--before`
- Filename: `discord-<channel-id>-latest.txt` or `discord-<channel-id>-<message-id>.txt`

## Use the export

The command prints the output path after a successful export. Reuse that file for subsequent
searches and reads. Locate relevant names, dates, errors, or topics, then read only the necessary
ranges. Rerun only when the user requests newer messages or the available context is insufficient.

Timestamps are UTC. A message-link export ends one second after the target timestamp, so start near
the end of the file when the linked message is the focus.

## Failure behavior

- Missing token: stop and ask the user to set `DISCORD_TOKEN` under `[env]` in
  `~/.config/mise/config.local.toml`.
- Invalid URL: report the accepted URL shapes.
- Discord permission or authentication error: report it without exposing the token.
- Empty export: verify channel access; do not broaden the range unless the task requires it.
