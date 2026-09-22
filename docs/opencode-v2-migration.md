# OpenCode V2 migration

This runbook protects V1 conversations while switching the managed configuration and CLI to V2.
V2 can migrate credentials and sessions, but exact history equivalence is not required. The V1
archive remains the recovery path.

## Selected artifacts

- `@opencode/cli`: installed from npm by mise, with the existing `latest` update policy.
- `@opencode/plugin` and `@opencode/sdk`: `2.0.7` in the locked test fixture.
- `@plannotator/opencode`: `latest`; verify the resolved version is at least `0.27.15` before
  activation.
- `github:rcdailey/opencode-claude-auth#integration`: the personal fork of
  `griffinmartin/opencode-claude-auth`, work profile only. The branch head floats, so OpenCode
  picks up fork updates without a config change.

The fork branch carries upstream pull requests that are not merged yet. Its `FORK.md` is the
authoritative record of which pull requests are included, why the branch commits `dist/`, and how
to refresh it. Read that file before changing the fork. Retire the fork only when every listed pull
request is merged, the upstream package publishes a release carrying them, and that release passes
the authentication checks below. A merge by itself is not a switch trigger.

The package reads Claude credentials from `~/.claude/.credentials.json`, `CLAUDE_CONFIG_DIR`, or
the macOS keychain. It writes OAuth connection data to `~/.local/share/opencode/auth.json` and
writes refreshed credentials back to the original Claude credential source. Refresh requests go
to `https://claude.ai/v1/oauth/token`; model requests retain the Anthropic SDK destination. Debug
logging is disabled unless `CLAUDE_AUTH_DEBUG` is set. Keep it unset because the logger's
redaction is useful but not a security boundary.

This plugin is not an Anthropic-approved subscription integration. Pinning it does not make its
transitive dependencies immutable or remove account risk.

## Prepare the V1 recovery copy

1. Stop every OpenCode writer. Record `opencode --version`, `command -v opencode`, active profile,
   rendered configuration, plugin resolutions, and the XDG config, data, and state paths.
2. Back up those roots to a private location outside this repository and outside chezmoi-managed
   directories. Preserve SQLite sidecars or use SQLite's backup facility; do not copy a live
   database by itself.
3. Preserve a runnable V1 binary outside mise's prune targets.
4. Make the archive immutable. Launch V1 against a working copy of the archived XDG roots and
   confirm that representative parent and child conversations open. Do not load this repository's
   V2 project override in that test.

## Validate an isolated V2 copy

1. Copy the V1 roots again and point V2 at that disposable copy. Let V2's native migration run
   only there first.
2. Capture migration warnings. Compare representative root sessions, child sessions, attachments,
   and message history. Restart an interrupted migration and confirm that it recovers.
3. Render and load the work, personal, and other profiles. Confirm the configured models,
   variants, provider limits, timeout settings, permission outcomes, agents, commands, and local
   plugins.

## Run live integration checks

These checks require an interactive V2 installation and real provider credentials. Record each
unavailable check as unverified rather than treating a durable local test as a substitute.

1. Confirm the resolved Plannotator package is V2-compatible. Exercise first submission,
   line-range revision, rejection, approval, cancellation, and plan-to-build handoff.
2. In the work profile, use `/connect`, choose Anthropic, and import the Claude Code subscription.
   Confirm that the active connection is OAuth, not an API key. Do not accept a paid API fallback.
3. Exercise a primary request, tool call, subagent, title generation, compaction, continuation,
   streaming, cancellation, and stall recovery. Repeat after restart.
4. Verify reconnect, external Claude credential rotation, refresh, and write-back. Do not force
   repeated rotations. Record a rate-limit-blocked refresh check as unverified.
5. In the personal profile, verify the OpenAI connection and configured model limits separately.

## Activate

1. Stop V1 writers. Apply the managed source. The one-time chezmoi scripts disable and stop the
   obsolete cleanup timer before V2 starts, then reload the user systemd manager after removal.
2. Run `mise install`, then confirm `command -v opencode` selects the mise V2 binary rather than an
   older installer path.
3. Allow V2 to migrate the active working data. Connect work-profile Claude credentials through
   the plugin's import method rather than assuming a generic Anthropic OAuth record is equivalent.
4. Verify both provider workflows. Start a new conversation, use tools and delegation, compact it,
   restart, and send another turn.
5. Apply chezmoi again. Confirm configuration, plugin, command, skill, and permission discovery is
   unchanged.

Do not activate if local runtime, permission, Plannotator, or provider happy-path checks fail. The
session pruner also has a concurrency ceiling: rechecks reduce risk, but pruning still requires
quiescent target sessions until V2 offers conditional deletion.

## Roll back

1. Stop V2 and preserve all new V2 data before changing anything.
2. Restore the V1 configuration and preserved V1 binary, then create a working copy of the V1 data
   archive.
3. Run V1 only against that working copy. Never point it at a V2-mutated database.
4. Do not overwrite new V2 work or restore stale rotated Claude tokens over the current credential
   source. Reauthenticate when credential state is uncertain.

Do not use uninstall as rollback. OpenCode versions can share directories, so uninstalling can
remove data needed by both versions.
