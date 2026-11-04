# herdr terminal app to herdr-app migration

- Date: 2026-11-04
- Status: Blocked (2026-11-04)
- Sources read at: `herdrdev/herdr-app` 816d205, `herdrdev/herdr-core` 3965a46 (v0.1.18)
- Current setup: the `herdr` terminal app inside kitty (`home/dot_config/herdr/config.toml`)

## Goal

Switch to herdr-app (desktop GUI). Rebuilding config, keys, and plugins is acceptable. Only missing
capabilities block the switch.

## Findings

- herdr-app runs on `herdr-core` (`hc`), not on the `herdr` terminal app. The OpenCode V1/V2
  integration in `herdrdev/herdr` does not apply to herdr-app.
- Core gets agent status only from OSC 7501, an escape sequence the program prints to its own
  terminal. No screen detection, no per-agent integrations (`herdr-core/AGENTS.md:34`,
  `CONTRIBUTING.md:5`).
- herdr-app ships no agent integrations. OpenCode is a launcher entry only
  (`defaults/programs.json:9`).
- herdr-app takes no feature-request issues: build it as a mod. Issues are for bugs and things a mod
  cannot do yet (`CONTRIBUTING.md:3-11`).

## Blocker 1: OpenCode status

Without OSC 7501 from OpenCode, its panes show no working/blocked/done state and no alerts.

- Fix needs only an OpenCode plugin that prints OSC 7501; no app mod is required.
- No such plugin found. Existing OpenCode plugins (`no-phux/herdr-opencode`,
  `nathabonfim59/herdr-opencode2`, `anaypurohit0907/herdr-opencode-bridge`) target the terminal app
  via `HERDR_PANE_ID`, which herdr-app does not set.
- Reference OSC 7501 emitters for agents: `can1357/oh-my-pi`, `nicobailon/pi-subagents`.

## Blocker 2: OpenCode session resume after reboot

The terminal app resumes conversations (`resume_agents_on_restore = true`). herdr-app does not.

- On reboot, core replaces a kept terminal's program with a shell and overwrites its `argv`
  (`herdr-core` `kept.rs:95`). Labels survive.
- OSC 7501 has no session or resume field (`status.rs:13-29`).
- Mods get no core restarted or terminal replaced event and cannot run at app start (app #288).
- Workaround pattern: `thuanlm215/herdr-agent-resume` stores the session ID as a terminal label and
  types the resume command into restored shells on a key press. Claude Code and Codex only.

## Tracked issues

- herdr-app #406 (open): resume supported agent sessions after reboot.
- herdr-core #15 (open): carry a resume reference in OSC 7501.
- herdr-app #288 (open): mods cannot run when the app starts.
- herdr-app #429 (open): restore Pi sessions after reboot.
- herdr-app #358 (open): Hermes integration cannot report under herdr-app.

## Next check

1. Search for an OpenCode plugin that emits OSC 7501 (`gh search code ']7501;' opencode`).
2. Check whether herdr-app or herdr-core added agent integrations or a resume mechanism (CHANGELOG,
   `status.rs`, `kept.rs`).
3. Recheck the tracked issues for state changes.
