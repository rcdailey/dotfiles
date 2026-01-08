---
description: Add conventional commit rules to AGENTS.md
---

Add path-based conventional commit classification rules to AGENTS.md for consistent commit messages.

## Process

### 1. Check Prerequisites

Verify AGENTS.md exists in repo root. If missing, report and exit.

### 2. Analyze Repository

Run in parallel:

- `rg --files | rg "^\.github/workflows"` (CI)
- `rg --files | rg "\.(props|csproj|slnx)$|^Directory\."` (build config)
- `rg --files | rg "^\.(renovate|editorconfig|gitignore)"` (tooling)
- `rg --files | rg "test|spec" -i` (tests)
- `rg --files | rg "\.(md|txt)$|^docs/"` (docs)
- `git log --oneline -30 | rg "^[a-f0-9]+ (feat|fix|chore|ci)"` (commit patterns)

Identify: primary language, build paths, source structure, test patterns, tooling configs.

### 3. Check Existing Rules

Read AGENTS.md and look for conventional commit sections:

- **Sufficient**: Has path mappings for ci/build/chore/test/docs AND source rules AND breaking
  change criteria - report "already complete" and exit
- **Scattered**: Rules exist but spread across sections - consolidate
- **Partial/Missing**: Generate comprehensive rules

### 4. Generate Rules

Adapt this template to discovered patterns:

```markdown
**Conventional Commit Rules** (path-based):

- `ci:` → `.github/workflows/**`, `ci/*`, `.gitlab-ci.yml`
- `build:` → `*.csproj`, `package.json`, `go.mod`, `Cargo.toml`, `Makefile`
- `chore:` → `.renovate/*`, `.editorconfig`, `.gitignore`, linting configs
- `test:` → `tests/**`, `*_test.*`, `*Test.*`
- `docs:` → `*.md`, `docs/**`, `LICENSE`, `README`

For source files (inspect diff):
- `feat:` → New public APIs, user-visible capabilities
- `fix:` → Bug fixes, error handling corrections
- `refactor:` → Internal restructuring, no behavior change
- `perf:` → Performance improvements

Breaking changes (!): API removals, incompatible changes, migration required
```

### 5. Insert Rules

Place after project description or in development standards section. Merge with any existing
partial rules, preserving project-specific customizations.

## Output

Report action taken:

- "Already has comprehensive rules. No changes needed."
- "Consolidated scattered rules into unified section at line X."
- "Added conventional commit rules at line X. Covers: [patterns]"
