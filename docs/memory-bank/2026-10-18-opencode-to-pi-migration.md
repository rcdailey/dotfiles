# OpenCode → pi Migration (Memory Bank)

Session date: 2026-10-18. pi version at time of research: **1.3.0** (installed via mise). Chunks
1-3 are implemented (see §2); this file captures research, decisions, and the chunked plan so future
sessions can resume without redoing the investigation.

Status legend used below: **[verified]** = read in source/docs/code this session; **[inferred]** =
reasoned from docs, not tested; **[open]** = unresolved.

---

## 1. Goals and user decisions (authoritative)

- chezmoi is the **source of truth** for pi config.
- **Complete copies, clear separation** from OpenCode. Do not reuse `opencode-*` templates, do not
  point pi at `~/.config/opencode/...` paths, do not read `opencodeModels` data. pi gets its own
  files (and its own `.chezmoidata` block if one is ever needed).
- Source location: `home/private_dot_pi/private_agent/` (target `~/.pi/agent`). `~/.pi` and
  `~/.pi/agent` are already mode 700; `private_` keeps that. **Never `exact_` the agent dir**
  (it holds `auth.json`, `sessions/`, `npm/`, `bin/`, caches).
- Willing to change mental model to "the pi way" rather than replicate OpenCode 1:1.
- **Question OpenCode assumptions.** Before porting any piece, check pi built-ins, installed
  packages, and community extensions for a more idiomatic solution; port as-is only when none fits.
- **Edit this file only for facts or decisions that change future work.** Never just to mark
  progress; git log records what is done.
- Work in **small chunks, foundational basics first**. Minimal-friction pilot.
- **No temporary test directories** (e.g. `PI_CODING_AGENT_DIR=/tmp/...`) for experiments.
- **Do not force `ask` → `deny`** via hacks.
- Subagent `ask` may forward to the user and pause (the earlier never-pause requirement was
  dropped). Keep `ask` rules few: only irreversible or other-people-visible actions.
- **Adopt pi default keybindings for now** (no `keybindings.json` yet).
- Undo: wants undo to change **session context only, never files on disk**. Hates that OpenCode
  undo reverts code. Use pi's native `/tree` (double-Escape). **Keep** the branch-summary prompt
  (do NOT set `branchSummary.skipPrompt`).
- Package versions: pin to **major only**, e.g. `npm:@gotgenes/pi-anthropic-auth@3`.
- Keep pi's **default built-in tools** (`read`, `bash`, `edit`, `write`).
- Git mutations still require explicit user approval (repo AGENTS.md rule). Commit scope for this
  work: `pi` (per repo commit conventions; confirm with user).

---

## 2. Plan (chunks)

### Chunk 1 — foundational base (agreed in principle, not yet written)

```text
home/private_dot_pi/private_agent/
  modify_settings.json     # merge managed keys into live settings.json
  AGENTS.md                # global directives, standalone pi-adapted copy
  extensions/tool-guards.ts  # pending final scope decision (see §9)
```

Plus a short pi section in repo-root `AGENTS.md` documenting layout and the `modify_` ownership
rule.

Managed settings keys:

| Key | Value | Reason |
|---|---|---|
| `$schema` | `https://pi.dev/schemas/settings.schema.json` | editor validation |
| `defaultProvider` | `anthropic` | |
| `defaultModel` | `claude-opus-5-5` | matches OpenCode build agent; live file currently has stale `claude-opus-4-8` |
| `defaultThinkingLevel` | `medium` | OpenCode build variant |
| `packages` | `["npm:@gotgenes/pi-anthropic-auth@3"]` | already in use; major-pinned |
| `hideThinkingBlock` | `true` | mirrors OpenCode `cli.json` `session.thinking: hide` |
| `enableInstallTelemetry` | `false` | mirrors OpenCode `share: manual` / `update: disable` stance (assumed; user didn't object) |

Explicitly decided against: `branchSummary.skipPrompt`, `httpIdleTimeoutMs` (leave default
300000 unless stalls appear), `keybindings.json`, extra `defaultTools`.

Model values are hardcoded (single provider for now). A `piModels` block in a pi-owned
`.chezmoidata.yaml` is the fallback if switching becomes needed.

`AGENTS.md` content: copy of current global directives (`home/dot_config/opencode/AGENTS.md`:
Core Rules, Shell Search, GitHub API, Agents/citations) with OpenCode wording removed. **Exclude
coding/testing directives for now** (they get sorted in chunk 3).

### Later chunks (proposed order)

1. Chunk 1 (above). **Done** (fe2dc58 and follow-ups).
2. Skills. **Done** (ab9c353, 895c173, fd6cd04). The four OpenCode authoring skills became one
   `instruction-authoring` skill; `commit` skill added; `discord-chat`, `gh-api`, `gh-pr-review`,
   `humanizer`, `hunk-staging`, `linear-cli`, `python-scripting` copied (discord paths moved to
   `~/.pi/agent/skills` and `/tmp/pi`; gh-pr-review dropped the reviewer-subagent hand-off);
   mattpocock skills via pi-owned `exact_skills/.chezmoiexternal.toml.tmpl`. Humanizer sync for pi:
   `.pi/prompts/sync-humanizer.md`.
3. Directive sorting. **Done** (this session). Principle: pi-subagents children do not load global
   `AGENTS.md` (`inheritGlobalContext: false`), so global `AGENTS.md` is main-session only and
   subagent rules belong in agent files. Review of OpenCode's global `AGENTS.md` found almost
   nothing that benefits subagents beyond what guards, permissions, and agent protocols already
   enforce. Placement:
   - pi `AGENTS.md`: Implementation Discipline, Architecture, General, Development, Code
     Documentation, Git (no initial tracking branch; never create worktrees), Repository Locations
     (`/tmp/pi/`), Tools (rewritten for fff + pi-lens; OpenCode V2 LSP and Glob notes dropped),
     Output (`file:line`), CLI Prose Arguments, and a one-line pointer to the `testing` skill.
   - New skills: `testing` (testing directives), `git-conflicts` (UD/DU handling),
     `worktree-branches`.
   - Removed from pi `AGENTS.md` (subagents never read it): "Subagents report `blocked`" clause
     and "Subagents MUST NOT clone". Citations rule kept (renamed section `Citations`).
   - Deferred: Agents + Delegating read-only discovery -> chunk 6; Change boundaries -> chunk 7.
4. Shell guards / file-tool guard extension (if not folded into chunk 1).
5. Permissions (`@gotgenes/pi-permission-system`).
6. Subagents (agent files for reviewer, researcher, acceptance, upgrade-analyst, scout/explore),
   model mapping. Carry into agent files: report `blocked` instead of asking; no cloning
   (reviewer may use task-owned worktrees); the `rg -r` is-replace warning for agents that run
   `rg`; `skills: [testing]` for agents that judge tests (e.g. acceptance). Port OpenCode
   primary-shared Agents/Delegating-discovery sections into the main-session side then.
7. Plannotator (`@plannotator/pi-extension`) + `/plan` prompt/skill workflow. Port OpenCode
   primary-shared Change boundaries here.
8. Remaining custom plugins (acceptance, research, chat-brevity, formatter, session naming,
   herdr state, notifications), footer.
9. Optional non-coding profile for `~/OpenCloud/Documents`.

---

## 3. pi facts (environment and config surface)

### Installation [verified]

- Binary: `~/.local/share/mise/installs/pi/1.3.0/pi/pi` (compiled Bun executable, ~107 MB).
- **Bundled docs**: `~/.local/share/mise/installs/pi/1.3.0/pi/docs/*.md` (settings, extensions,
  packages, keybindings, models, virtual-models, sessions, cli, configuration, security, ...).
  Examples: `.../pi/examples/extensions/*.ts` (permission-gate, protected-paths, plan-mode,
  subagent, git-checkpoint, notify, prompt-customizer, ...), `.../pi/examples/sdk/`.
- The binary embeds readable JS; `rg -a` on it works for answering behavior questions the docs
  don't cover (that is how package version semantics were verified).
- Env vars pi sets for the running agent: `PI_CODING_AGENT=true`, `PI_PROVIDER`, `PI_MODEL`,
  `PI_REASONING_LEVEL`, `PI_SESSION_FILE`, `PI_SESSION_ID`. (`claude-opus-5-5` is a valid id —
  it is the model running this session.)

### Current live `~/.pi/agent` (before any chezmoi management)

```text
auth.json (600)  bin/fd  models-store.json  npm/  sessions/  settings.json
```

`settings.json`:

```json
{
  "lastChangelogVersion": "1.3.0",
  "defaultProvider": "anthropic",
  "defaultModel": "claude-opus-4-8",
  "packages": ["npm:@gotgenes/pi-anthropic-auth"]
}
```

`npm/package.json` records `"@gotgenes/pi-anthropic-auth": "^3.4.3"`. pi put `fd` into
`bin/` for its `find` tool.

### Config surface [verified, docs/configuration.md]

| Path (agent dir) | Purpose | Who writes |
|---|---|---|
| `settings.json` | settings, packages, resource paths | **pi AND chezmoi** → `modify_` |
| `keybindings.json` | keybindings | chezmoi only |
| `mcp.json` | MCP servers | chezmoi only |
| `models.json` | custom endpoints/model overrides | chezmoi only |
| `auth.json` | credentials | pi only (never chezmoi) |
| `AGENTS.md` (or `AGENTS.override.md`, `CLAUDE.md`) | global context | chezmoi only |
| `SYSTEM.md` | **replaces** pi default system prompt | chezmoi only |
| `APPEND_SYSTEM.md` | appends to system prompt | chezmoi only |
| `extensions/`, `skills/`, `prompts/`, `themes/` | resources | chezmoi only |
| `sessions/`, `npm/`, `bin/`, `models-store.json` | runtime state/caches | pi only |

- Project config lives in `<cwd>/.pi/` (settings, mcp, SYSTEM.md, APPEND_SYSTEM.md, extensions,
  skills, prompts, themes) and loads only after **project trust** is granted.
- Context files (`AGENTS.md`/`CLAUDE.md`) load from agent dir + cwd + every parent dir, **no trust
  required**. `AGENTS.override.md` replaces only files in the same directory.
- `pi -nc` / `--no-context-files` disables all AGENTS.md/CLAUDE.md discovery. No settings key
  equivalent.
- `PI_CODING_AGENT_DIR` overrides the whole agent dir.
- `/reload` re-reads settings, keybindings, instructions, resources.
- Settings schema: `https://pi.dev/schemas/settings.schema.json`.

### Why `modify_settings.json` [verified]

pi writes `settings.json` itself: `lastChangelogVersion` (every update), `pi install`/`pi remove`,
Ctrl+S in `/model` or `/thinking`, `/settings`, `/scoped-models`, theme selection, and some
packages (e.g. pi-powerline-footer `powerline` key, pi-subagents profile commands). A plain
chezmoi-owned file would fight pi forever. A `modify_` script receives the current file on stdin
and emits it with managed keys overwritten, preserving pi-owned keys.

Semantics to accept: chezmoi wins on managed keys (a Ctrl+S model change reverts on next apply);
unmanaged keys are left alone.

Precedents:

- In-repo: `home/dot_config/modify_private_kwinrc` (Python, stdlib only). Follow this style.
- External: [joelazar/dotfiles `dot_pi/private_agent/modify_settings.json`](https://github.com/joelazar/dotfiles/blob/main/dot_pi/private_agent/modify_settings.json)
  (bash + `jq -s` merge). Same `dot_pi/private_agent/` layout as planned here.

### Package version semantics [verified from pi 1.3.0 embedded source]

- `parseSource("npm:<spec>")` → `{ range: semver.validRange(version), pinned: semver.valid(version) !== null }`.
- Exact version (`@3.4.3`) = **pinned** (never updated).
- Range (`@3`, `@^3.4`) = not pinned; startup checks installed version satisfies the range;
  `pi update --extensions` installs `maxSatisfying` within the range. So `@3` = latest 3.x, never
  4.0.
- No version = latest; npm records `^x.y.z`.
- Git sources: tag/commit refs are pinned.
- Local path sources are allowed in `packages` (resolved relative to the settings file).

### Built-in tools [verified, docs/settings.md]

Default on: `read`, `bash`, `edit`, `write`. Available but off: `grep`, `find`, `ls`,
`powershell`; built-in extensions register `codemode` and `tool_search` inactive. Enable via
`"defaultTools": ["+grep", ...]` (`+`/`-` lists modify the inherited selection). Decision: keep
defaults; directives require `rg` / `rg --files` via bash anyway.

### Built-in extensions

`builtin:mcp`, `builtin:llama.cpp`, `builtin:codemode`, `builtin:tool-search` load by default;
disable with `"extensions": ["-builtin:mcp"]`.

### Undo / branching [verified, docs/sessions.md + keybindings.md]

- Double-Escape on empty editor → `/tree` (`doubleEscapeAction`, default `tree`).
- Selecting an earlier user message puts its text back in the editor; resubmitting creates a new
  branch. Old branch stays in the session file. **No file changes are reverted.**
- Leaving a branch prompts for an optional branch summary (user wants to keep this prompt).
- `/fork` (new session from earlier user message), `/clone` (copy branch to new session).
- Packages to **avoid** (they revert files): `pi-workspace-history`, `pi-rewind-hook`,
  `@davideasden/pi-undo`, pi's `examples/extensions/git-checkpoint.ts`.
- `@henryqw/pi-undo` claims context-only rewind to latest user prompt (unread code) — optional.

### Keybindings (defaults adopted) [verified, docs/keybindings.md]

Notable defaults: `shift+tab` cycle thinking level; `ctrl+p` / `shift+ctrl+p` cycle models;
`ctrl+l` model selector; `ctrl+t` toggle thinking blocks; `ctrl+o` expand tool output; `ctrl+x`
copy message; `ctrl+g` external editor; `alt+enter` queue follow-up; `alt+up` dequeue;
`ctrl+-` editor undo; `ctrl+shift+up/down` jump between prompts; `ctrl+shift+f` transcript
search; `app.session.new/tree/fork/resume` unbound by default. `tab` = autocomplete (no agent
cycling). `/hotkeys` lists active bindings.

If keybindings are customized later, the OpenCode → pi mapping from
`home/dot_config/opencode/private_cli.json` was worked out:

| OpenCode | Key | pi action | Conflict |
|---|---|---|---|
| session.undo | alt+u | app.session.tree | — |
| session.timeline | alt+z | app.session.tree | duplicate of undo |
| session.fork | alt+f | app.session.fork | alt+f = editor word-right; remove there |
| session.list | alt+l | app.session.resume | — |
| session.new | alt+n | app.session.new | — |
| model.list | alt+m | app.model.select | replaces ctrl+l |
| messages.copy | alt+c | app.message.copy | replaces ctrl+x |
| session.toggle.thinking | alt+t | app.thinking.toggle | replaces ctrl+t |
| session.first/last | ctrl+g / ctrl+alt+g | tui.altScreen.top/bottom | ctrl+g = external editor in pi |
| agent.cycle | tab/shift+tab | — | shift+tab already cycles thinking (closest analog to plan/build) |
| variant.list | ctrl+t | — | use `/thinking` |
| prompt.skills | alt+s | — | `/skill:` autocomplete |
| session.parent/child.* | alt+arrows | depends on subagent pkg | alt+up dequeue, alt+left/right word nav |

Other `cli.json` prefs: `attention.sound` → needs a notify extension (pi `examples/extensions/notify.ts`);
herdr plugin → herdr-agent-state extension (see §7).

---

## 4. Models and providers

- **No single "provider toggle"** in pi [verified]. Pieces:
  - `defaultProvider`/`defaultModel`/`defaultThinkingLevel` = startup only.
  - `--provider` CLI flag only disambiguates `--model`.
  - `enabledModels` + Ctrl+P: list one model per provider → Ctrl+P flips provider live.
  - `modelThinkingLevels` keyed by `provider/modelId` — docs call it *startup* thinking; unknown
    whether it applies on Ctrl+P switch [open].
  - **Virtual models** (`pi.registerVirtualModel`, docs/virtual-models.md): an extension can expose
    e.g. `me/build` that routes per request to a physical model chosen by a flag/env. Closest to a
    real toggle; custom code.
- `enabledModels` only scopes cycling; `/model` still lists every authenticated provider. No
  equivalent of OpenCode's `provider.use` deny policy found.
- OpenCode's `opencodeProvider` switch also chose providers blocks/plugins; in pi, providers with
  credentials coexist.
- Possible provider-id gotcha: ChatGPT subscription may appear as `openai-codex`, not `openai`
  [open — check `/model`].
- OpenCode model matrix (for reference, from `home/dot_config/opencode/.chezmoidata.yaml`):
  anthropic — plan/build/acceptance/reviewer opus-5-5 (high/medium/high/high), researcher
  sonnet-5-5 medium, upgradeAnalyst sonnet-5-5 high, explore/title/compaction haiku-5-5 low;
  openai — gpt-6-astra/sol/luna equivalents.
- Subagent model per provider: nicobailon `pi-subagents` has
  `subagents.agentOverridesByProvider.<provider>.<agent>` keyed on the **parent session's current
  provider** (native replacement for the chezmoi provider hack). Precedence: per-run →
  provider-scoped role override → `agentOverrides.<name>` → frontmatter `model` →
  `subagents.defaultModel` → parent model. Its `/subagents-load-profile` writes settings.json
  (would fight chezmoi — avoid). `@gotgenes/pi-subagents` model options were not researched in
  equivalent depth [open].

---

## 5. Instructions architecture: primary vs subagent vs on-demand

### Core pi behavior [verified]

- pi has **no built-in subagents or plan mode** by design ("Pi ships with powerful defaults but
  skips features like sub-agents and plan mode").
- Global `~/.pi/agent/AGENTS.md` loads for every session.

### Subagent inheritance differs by package [verified via docs]

- **`@gotgenes/pi-subagents`** ([configuration.md](https://raw.githubusercontent.com/gotgenes/pi-packages/main/packages/pi-subagents/docs/configuration.md)):
  children inherit the parent's "stable identity" = preamble + **AGENTS.md/CLAUDE.md** (+
  SYSTEM.md/APPEND_SYSTEM.md per "portable" strategy wording). Both `prompt_mode: append`
  (default) and `replace` keep the inherited prompt as base. **No opt-out for AGENTS.md.**
  Extension-appended blocks (`before_agent_start`) are NOT inherited, but children load the
  parent's extensions and re-run the handler. `excludedExtensionPackages` in
  `~/.pi/agent/subagents.json` keeps listed **package** extensions out of children (exact match to
  `packages` entry strings; loose `extensions/` files can't be excluded). Whether local-path
  package entries match is **[open]**.
  - Idiomatic primary-only instructions with this package: local package (e.g.
    `packages/primary-instructions/`) whose extension appends `PRIMARY.md` in
    `before_agent_start`, listed in both `packages` and `excludedExtensionPackages`. Must emit
    byte-identical text each turn (cache). Alternative gating on `ctx.hasUI` is fragile
    (also drops in `pi -p`/RPC).
- **nicobailon `pi-subagents`** (most popular, ~583k/mo;
  [docs/agents.md](https://github.com/nicobailon/pi-subagents/blob/main/docs/agents.md)):
  per-agent `inheritProjectContext` (builtins default true), **`inheritGlobalContext` (default
  false → `~/.pi/agent/AGENTS.md` excluded from children)**, `inheritSkills`,
  `systemPromptMode` (default `replace`). Forked children (`context: fork`) get the full parent
  prompt regardless. User agents: `~/.pi/agent/agents/**/*.md`. Builtins: `scout`, `worker`,
  `reviewer`, `delegate`, `oracle`, external CLI adapters, etc.

### GitHub survey of real pi setups (18 repos sampled) [verified]

- Global `AGENTS.md`: 7/18; `APPEND_SYSTEM.md` only: 2; neither: ~9 (nicknisi, Mic92, sapegin,
  jackfranklin, joelazar, dkarter, fredrikaverpil, mikker, basnijholt).
- Heavy customization lives in **extensions** (15–34 files in some repos) and **skills**, not big
  prompts.
- Mic92 uses an extension to append `~/.claude/CLAUDE.md` to the system prompt.
- [HazAT/pi-config](https://github.com/HazAT/pi-config): workflows are **prompt templates + skills**
  (`/plan` loads `plan` skill, `/execute` dispatches workers told to read `skills/worker/SKILL.md`).
  Notably keeps general coding principles ("Keep It Simple", reuse codebase, stdlib first)
  **inline in global AGENTS.md** — counterexample to "everything in skills".
- Few use subagents; those who do use nicobailon `pi-subagents`, `@tintinweb/pi-subagents`, or
  self-written ones.
- Some scope rules in prose ("This section does not apply to the advisor minion itself").

### Directives-as-skills evidence [verified]

- [ilude/claude-code-config `testing-workflow`](https://github.com/ilude/claude-code-config/blob/main/skills/testing-workflow/SKILL.md):
  451-line RFC-2119 testing skill with condition trigger ("Activate when working with tests, test
  files, ..."). Closest analog to the user's testing directives.
- barnabasJ/dotfiles `testing` skill: weak trigger ("Software testing").
- [kunchenguid/firstmate coding-guidelines](https://github.com/kunchenguid/firstmate/blob/main/.agents/skills/firstmate-coding-guidelines/SKILL.md):
  best articulation of the pattern — knowledge-placement decision tree (every-turn → AGENTS.md;
  nameable situation → skill), **inline-stub pattern** (leave only the load trigger + any
  safety-critical fact in AGENTS.md, no partial restatement), size discipline, trigger hygiene
  (description = always-loaded trigger index; phrase as a condition).
- Many generic catalog skills exist (yagni, solid, kiss, tdd, coding-guidelines) — not personal
  directive sets.
- Conclusion: skills suit **situational** guidance; rules that must hold every turn stay
  always-on. Earlier blanket advice "move coding directives to skills" was retracted.
- Current directive sizes: `opencode-coding-directives.md` 103 lines,
  `opencode-testing-directives.md` 32 lines, `opencode-primary-shared.md` 160 lines.
  Coding directives contain OpenCode-specific lines to rewrite: `/tmp/opencode/` clone location,
  "until OpenCode V2 restores its LSP runtime", Glob tool dot-dir note, webfetch references.

### Primary-agent "mode" packages (OpenCode-style Tab agents) [verified READMEs]

None matches OpenCode exactly (no md-per-agent, no Tab — Tab is autocomplete; ctrl+tab usually
eaten by terminals; `alt+m` is the de facto cycle key).

- `@arhen/pi-add-mode` (~1.8k/mo, new Oct 2026, [repo](https://github.com/arhen/pi-extensions)):
  modes in `~/.pi/agent/modes.json` (instructions string, tools preset, model, thinking,
  subagentModel/Thinking, color); `alt+m`, `/mode`, `--start-mode`; injects via
  `systemPromptOptions.sections.mode` (cache friendly). chezmoi could render JSON from per-mode
  md via `{{ include ... | toJson }}`. Subagent leakage and subagent-tool compatibility untested.
- `pi-agent-modes` (~700/mo, stale, tested on pi 0.83), `pi-oc-style-agent-switcher` (model only),
  `pi-profile-switch` (needs separate `pi-profile` launcher), `rolebox` (heavy, multi-harness).
- pi-way alternative adopted in plan: plan/build become `/plan` prompt + skill + Plannotator;
  thinking level via `shift+tab`.

### Non-coding directories (e.g. `~/OpenCloud/Documents`)

- A: separate profile via `PI_CODING_AGENT_DIR` set by a `mise.toml` `[env]` in that tree
  (needs `mise trust`; separate auth.json → `/login` once; don't symlink auth.json — pi may
  rewrite/replace it on OAuth refresh [inferred]; separate sessions).
- B: `<dir>/.pi/SYSTEM.md` replaces pi's coding-oriented base prompt (needs project trust); global
  AGENTS.md still loads unless `pi -nc`.
- C: extension filtering context files per cwd (possible via SDK/prompt sections, unverified).
- With lean always-on AGENTS.md + coding stuff in skills, B alone may suffice. User hasn't chosen.

---

## 6. Permissions × subagents (deep dive)

### `@gotgenes/pi-permission-system` [verified]

- Config: `~/.pi/agent/extensions/pi-permission-system/config.json` (global), project
  `<cwd>/.pi/extensions/pi-permission-system/config.json` (trusted only). Static file → chezmoi
  can own it.
- Surfaces: `*`, tools, `bash` patterns (last match wins), `mcp`, `skill`, `path`,
  `external_directory`, directional read/write surfaces, `commandEffects`, `shellTools`.
  Fails closed on unparseable bash or wrappers (`bash -c`, `eval`, `sudo`, `env`, `xargs`,
  `find -exec`) → `ask`.
- Per-agent override: `permission:` frontmatter in `~/.pi/agent/agents/<agent>.md` (minimal YAML:
  scalars + nested maps only). Agent resolved from `<active_agent>` tag in child system prompt.
- Subagent adapter convention ([subagent-integration.md](https://github.com/gotgenes/pi-packages/blob/main/packages/pi-permission-system/docs/subagent-integration.md)):
  in-process implementations emit `subagents:child:session-created` / `subagents:child:disposed`
  on `pi.events`; out-of-process set `PI_SUBAGENT_PARENT_SESSION`. Conformance table there is
  **stale** regarding nicobailon (see below).
- Ask resolution ([authorizer.ts](https://github.com/gotgenes/pi-packages/blob/main/packages/pi-permission-system/src/authority/authorizer.ts)):
  has UI → local dialog (or relay if a live parent target); no UI + detected subagent → forward
  to parent (waits up to `forwardingTimeoutMs`, default 600000; ~2 s fast-fail if parent not
  serving); no UI + not subagent → `DenyingAuthorizer` = **immediate deny**.
- `promptTimeoutMs` (parent) denies unanswered prompts; `yoloMode` exists.
- OpenCode permission list in `home/dot_config/opencode/opencode.jsonc.tmpl` maps almost
  directly (git push/reset --hard/clean/branch -D/stash drop|clear ask; git commit deny; rm -r ask
  except /tmp; sudo/kill/pkill/shutdown/reboot ask; herdr pane/tab deny + server/session/
  workspace/worktree ask; many gh mutations ask; `gh api*` ask with `--method GET` allow;
  gh-review reply/delete ask; `* --help *` allow last; read `*.pdf` deny; websearch deny).

### nicobailon `pi-subagents` + permissions [verified from code]

- Children run **in-process** (foreground) or in a **detached runner process** (background), not
  separate `pi` binaries.
- Own native permission layer ([permissions.ts](https://github.com/nicobailon/pi-subagents/blob/main/src/runs/shared/permissions.ts)):
  tool-level allow/ask/deny in `~/.pi/agent/extensions/subagent/config.json` and agent
  `permission:`/`permissions:` frontmatter. **`bash` rules throw** ("left to pi-guard"); bash
  always passes this layer. `ask` goes to a watchdog-model arbiter (not the user).
- Injects `@gotgenes/pi-permission-system` into a child **only when the agent has native
  permission rules** ([child-tool-plan.ts](https://github.com/nicobailon/pi-subagents/blob/main/src/runs/shared/child-tool-plan.ts)).
  Docs suggest foreground children don't do ambient extension discovery → **bash may run
  ungoverned** in foreground children without native rules [inferred].
- Injects `<active_agent name="..."/>` tag (compatible with gotgenes per-agent resolution).
- **Frontmatter collision**: both packages read `permission:` from the same agent files; gotgenes
  bash rules there make nicobailon reject the agent → per-agent bash policy impossible.
- Background runners get `PI_SUBAGENT_PARENT_SESSION` → `ask` **forwards to user and pauses**.
  Foreground children: no parent env → deny.
- Verdict: cannot meet "allow/deny only, never pause" without custom glue.

### `@gotgenes/pi-subagents` + permissions

- Conformant; permission system active in every child; per-agent `permission:` with bash patterns
  works without collision.
- Trade-off: global AGENTS.md always inherited (needs the excluded primary-instructions package
  pattern).

### Decision

**Chosen: `@gotgenes/pi-subagents` + `@gotgenes/pi-permission-system`** (replaced nicobailon).
Consequences for chunk 6 [verified, gotgenes docs/configuration.md]:

- Children inherit the parent's `<project_context>`, so **global `AGENTS.md` reaches every
  child**. Main-session-only rules go in `~/.pi/agent/PRIMARY.md` (system-prompt section added by
  `primary-instructions.ts`, skipped in children); deferred Agents/delegation (chunk 6) and Change
  boundaries (chunk 7) belong there. Child detection: `exact_extensions/lib/subagent-children.ts`.
- Children inherit all parent skills and extensions; no `skills:`, `inheritSkills`, or
  `inheritGlobalContext` keys. Opt-outs: `excludedExtensionPackages` setting.
- Agent models: `extensions/model-roles.ts` registers virtual models `role/<name>`; settings.json
  `modelRoles` (managed whole in `modify_settings.json`) maps provider x role to model + thinking (per-role, not tiers: variants
  differ per provider). Provider = root session's selected model, snapshotted per child at spawn.
  Agent files set `model: role/<name>` and no `thinking`. Add a role row with each new agent.
- nicobailon re-checked at `95683a4` (2026-10-17): foreground children still load no ambient
  extensions and reject frontmatter bash rules, so the gotgenes choice stands.
- Agent files: `~/.pi/agent/agents/<name>.md`, frontmatter `description`, `tools`, `model`,
  `thinking`, `max_turns`, `prompt_mode` (`append`|`replace`), `inherit_context`,
  `run_in_background`, `enabled`, `locked`, plus permission-system `permission:`.

---

## 7. Community package catalog (researched; nothing installed yet)

Download counts are npm monthly as of 2026-10-18; ecosystem churns weekly (pin majors).

| Need | Package | Notes |
|---|---|---|
| Anthropic auth | `@gotgenes/pi-anthropic-auth` | already installed (^3.4.3) |
| Permissions | `@gotgenes/pi-permission-system` (~66k) | v41.x; see §6 |
| Subagents | nicobailon `pi-subagents` (~583k), `@gotgenes/pi-subagents` (v25), `pi-subagents-lite`, `pi-subagent-manager`, `@tintinweb/pi-subagents` | don't run two at once |
| Plan review | `@plannotator/pi-extension` (~124k) | official port of OpenCode plugin in use |
| Footer | `pi-powerline-footer` (~97k, [repo](https://github.com/nicobailon/pi-powerline-footer)) | writes `powerline` key into settings.json; adds alt+s stash, /cd, bash mode |
| Footer | `pi-cc-extensions` (~70k, Chinese README), `pi-footer` (own config file), `@narumitw/pi-statusline`, `@narumitw/pi-starship` | own-file config is chezmoi-friendlier |
| Context view | `pi-context-view` (~9k) | |
| Session naming | `pi-rename`, `@fyeeme/pi-session-name`, `pi-session-name` | replaces `session-rename.ts` |
| Herdr | `pi-herdr-tab-name`; joelazar & dkarter keep a `herdr-agent-state.ts` extension in dotfiles | OpenCode uses `herdr integration install opencode` (see `.chezmoiignore`); check whether herdr has a pi integration [open] |
| Formatter | `@ian-pascoe/pi-formatter` (post-edit commands; could run `md-format`), `pi-lens` (heavy) | |
| Web | `pi-web-access` (~755k), `pi-web-search` | OpenCode setup denies websearch deliberately; likely skip |
| Guards | `@yaosu/pi-path-guard`, `@lystran/pi-guard`, `pi-dcg` | none replicate rg/gh-api guards |

Discovery: npm search `keywords:pi-package` (registry API
`https://registry.npmjs.org/-/v1/search?text=keywords:pi-package+<q>`), gallery at
https://pi.dev/packages.

---

## 8. OpenCode inventory → pi mapping

Source: `home/dot_config/opencode/`.

| OpenCode piece | pi approach | Status |
|---|---|---|
| `AGENTS.md` global directives | `~/.pi/agent/AGENTS.md` copy | chunk 1 |
| `coding-directives.md.tmpl` (+ shared partials) | sort into AGENTS.md / skills / agent files | done (chunk 3; agent/plan parts deferred to 6/7) |
| `exact_skills/` + external mattpocock skills | copies in pi `skills/` | done (chunk 2) |
| `exact_commands/` (`$ARGUMENTS` compatible) | pi `prompts/` copies; `review`, `upgrade-prs` depend on subagents | later |
| `exact_agents/` plan/build (primary) | `/plan` prompt + skill + Plannotator; build = default session | later |
| `exact_agents/` acceptance/researcher/reviewer/upgrade-analyst | subagent agent files | chunk 6 |
| `opencode.jsonc` permissions | pi-permission-system config | chunk 5 |
| `opencode.jsonc` formatter (md-format for .md/.mdx/.md.tmpl, shfmt off) | formatter extension | later |
| Anthropic timeout false / chunkTimeout 60000 | `httpIdleTimeoutMs` (default 300000; leave) | decided: leave |
| `tool-guards.ts` (grep→rg, find -name→rg --files, sops --set) | pi `tool_call` hook extension | chunk 1 or 4 |
| `ripgrep-recursive-flag.ts` (rg -r misuse) | port | chunk 4 |
| `gh-api-guard.ts` (require --method) | port | chunk 4 |
| `formatter-true-guard.ts` | read before porting | later |
| `file-tools/` (Anthropic reminder: use file tools not sed/cat/heredocs) | fold into guard extension as blocks | pending (§9) |
| `chat-brevity/`, `acceptance/`, `research/` (with tests), `lib/` reminders | rebuild on pi extension API | later; not read in detail |
| `session-rename.ts` | session-name package | later |
| `private_cli.json` keybinds/attention/herdr plugin | defaults; notify + herdr extensions | later |

Repo conventions to carry over (repo AGENTS.md): OpenCode plugin hooks must keep earlier
conversation bytes identical (prompt cache); same applies to pi `before_agent_start`/`context`
hooks. Test conventions for pi extensions are not yet defined [open] — mirror OpenCode rules
(single-file: no durable tests; directory: colocated `*.test.ts`) unless user decides otherwise.

---

## 9. File-tool guard design (in progress)

Observed problem: Opus drifts to shell reads/edits. Evidence in this very session: despite a
system prompt saying "Use read to examine files instead of cat or sed", the agent ran
`cat ~/.pi/agent/settings.json`, `head -30 .../build.md.tmpl`, `sed -n '1,80p' virtual-models.md`,
`sed -n '1381,1421p' /tmp/permcfg.md`. Prompt-only guidance is insufficient.

Planned: single extension (`extensions/tool-guards.ts`) with a `tool_call` hook on `bash`
returning `{ block: true, reason }`. Reuse the command parser from
`home/dot_config/opencode/exact_plugins/tool-guards.ts` (`commandWords`, `localInvocation`
with sudo/env/command wrapper handling; skips heredocs/`$()`/backticks).

Proposed narrow v1 rules:

- Port as-is: block `grep`, `find ... -name`, `sops --set`.
- Block `cat` / `head` / `tail` / `sed -n '<range>p'` only when ALL hold:
  1. invoked directly (not via `sudo`, not remote — first word must be the command);
  2. operand is an existing regular file (stat relative to session cwd);
  3. output is **not piped or redirected** (needs parser change to track pipe position);
  4. no follow/byte/visibility flags (`-f`, `-F`, `-c`, `cat -A`/`-v`).
  Message: "use `read` (offset/limit for ranges)".
- Block `sed -i` / `perl -i` → "use `edit`". **[open]**: user hasn't confirmed whether to allow
  `sed -i` for bulk mechanical edits.
- Never block `awk` (computation), `sed` transforms to stdout, pipelines (`cmd | head`),
  concatenation (`cat a b > c`), `tail -f`, `ssh/kubectl/docker exec ... cat`.

Known false-positive/evasion concerns: parser doesn't special-case `<`, `>`, `<(...)` redirections;
blocking can push the model to `less`/`nl`/`bat`/`python -c open()`; heredoc writes
(`cat > f <<EOF`) and nested scripts bypass; multi-file `head a b c` becomes several `read` calls
(parallel is fine). Best-effort guard, not a security boundary.

Open decision: include in chunk 1 (recommended) vs only port existing grep/find guards first.

---

## 10. Gotchas (non-obvious)

- `settings.json` is shared-ownership → `modify_` only; never a plain chezmoi file.
- Don't `exact_` `private_agent/`; would delete sessions/auth/npm.
- `@3` range is honored (not pinned) — verified in source, not docs.
- `excludedExtensionPackages` matches exact `packages` strings; loose extension files can't be
  excluded; local-path entries unverified.
- `APPEND_SYSTEM.md`/`SYSTEM.md` are inherited by gotgenes subagents → not a primary-only channel.
- Forked nicobailon children (`context: fork`) receive the full parent prompt incl. global context.
- pi Tab = autocomplete; no agent cycling. `ctrl+tab` rarely reaches pi through terminals.
- `ctrl+g` in pi = external editor (OpenCode used it for scroll-to-top).
- `pi -nc` is the only way to drop global AGENTS.md; no setting.
- `enabledModels` doesn't hide providers from `/model`.
- Packages that "help" (powerline footer presets, subagent profiles, `/settings`, Ctrl+S saves)
  write settings.json → chezmoi reverts managed keys on next apply.
- pi's default system prompt itself is coding-oriented; `SYSTEM.md` replaces it.
- Undo packages vary wildly: several revert files (avoid).
- Ecosystem velocity is high (permission-system major 41, weekly releases); re-verify package
  behavior before each chunk.
- Repo markdownlint ignores `docs/memory-bank/**`; this file is exempt.

---

## 11. Open questions to resume with

1. Chunk 1: include file-tool blocks? allow `sed -i` for bulk edits?
2. Confirm commit scope `pi` for this work.
3. Subagent permission design satisfying allow/deny-only without ask→deny forcing (§6).
4. Subagent package final choice (gotgenes vs nicobailon) — tied to (3) and instruction
   separation.
5. Does `excludedExtensionPackages` accept local-path package entries?
6. `modelThinkingLevels` effect on Ctrl+P switches.
7. OpenAI provider id in pi (`openai` vs `openai-codex`).
8. Non-coding profile for `~/OpenCloud/Documents`: option A vs B.
9. Test conventions for pi extensions in this repo.
10. herdr pi integration availability.
