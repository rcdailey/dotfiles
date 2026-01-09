---
allowed-tools: Read, Edit, Bash(git log:*), Bash(rg:*), Bash(find:*)
description: Add file path-based conventional commit rules to CLAUDE.md
---

# Setup Conventional Commits Command

Add path-based conventional commit classification rules to a project's CLAUDE.md file for consistent
commit message generation without requiring deep file inspection.

## Execution Steps

### 1. Verify CLAUDE.md Exists

Check if `CLAUDE.md` exists in repository root:

```bash
[ -f CLAUDE.md ] && echo "exists" || echo "missing"
```

If missing, inform user and exit.

### 2. Analyze Repository Structure

Execute these commands in parallel to understand project patterns:

```bash
# Find workflow files
rg --files | rg "^\.github/workflows"

# Find build configuration files
rg --files | rg "\.(props|csproj|slnx)$|^Directory\."

# Find CI/build scripts
rg --files | rg "^(ci|scripts)/"

# Find tooling config
rg --files | rg "^\.(renovate|editorconfig|gitignore|yamllint|pre-commit|markdownlint|vscode|dockerignore)"

# Find test files
rg --files | rg "test|spec" -i

# Find documentation
rg --files | rg "\.(md|txt)$|^(docs|LICENSE|SECURITY|CODEOWNERS)"

# Find source directories
find . -type d -name "src" -o -name "lib" -o -name "app" | head -5

# Recent commits for pattern analysis
git log --oneline --no-decorate -30 | rg "^[a-f0-9]+ (feat|fix|chore|ci|build|refactor|test|docs|perf)"
```

### 3. Identify Project-Specific Patterns

Based on analysis, determine:

- **Primary language/framework**: Look for package managers (package.json, requirements.txt, go.mod,
  Cargo.toml, pom.xml, build.gradle, etc.)
- **Build system paths**: CI workflow locations, build script directories
- **Source structure**: Main source directories and their subdirectories
- **Test patterns**: Test file naming conventions (*Test.*, *_test.*, test_*.*)
- **Tooling configs**: Linting, formatting, dependency management configs

### 4. Analyze Existing CLAUDE.md Content

Read entire CLAUDE.md and assess existing conventional commit guidance:

**Search for existing rules:**

- Look for "CONVENTIONAL COMMIT" sections (case insensitive)
- Search for file path mappings like `ci:`, `build:`, `feat:`, `fix:`
- Identify scattered commit-related guidance across multiple sections
- Check for partial rules or incomplete coverage

**Evaluate completeness:**

- **Sufficient**: Has file path mappings for ci/build/chore/test/docs AND source file rules
  (feat/fix/refactor) AND breaking change criteria
- **Partial**: Has some commit guidance but missing key categories or path mappings
- **Scattered**: Rules exist but spread across multiple sections without consolidation
- **Missing**: No conventional commit rules present

### 5. Determine Action Based on Analysis

**If sufficient + consolidated:**

- Report: "CLAUDE.md already has comprehensive conventional commit rules. No changes needed."
- Exit without modifications

**If sufficient but scattered:**

- Consolidate all commit-related guidance into single "CONVENTIONAL COMMIT RULES" section
- Preserve all existing content, reorganize for clarity
- Remove duplicate information
- Update cross-references to point to consolidated section

**If partial or missing:**

- Proceed to generate comprehensive rules (next step)
- If partial rules exist, merge existing content with generated rules
- Preserve any project-specific customizations found in existing rules

### 6. Locate Insertion/Consolidation Point

Determine where to place rules:

1. If "conventional commits" mention exists: Insert/consolidate there
2. Development standards or code standards section: Use that location
3. If neither exists: Insert after project description/overview

Identify exact line number and context.

### 7. Generate Token-Optimized Rules

Create rules section based on repository analysis. Use this template structure adapted to findings:

```markdown
**CONVENTIONAL COMMIT RULES** (file path-based classification):

**Direct path mapping:**

- `ci:` → `.github/workflows/**`, `ci/*`, `scripts/*`, `.gitlab-ci.yml`, `Jenkinsfile`
- `build:` → `*.props`, `*.csproj`, `*.sln`, `package.json`, `requirements.txt`, `go.mod`,
  `Cargo.toml`, `pom.xml`, `build.gradle`, `Makefile`, `CMakeLists.txt`
- `chore:` → `.renovate/*`, `renovate.json5`, `.editorconfig`, `.gitignore`, linting configs,
  formatter configs
- `test:` → `tests/**`, `test/**`, `*_test.*`, `*Test.*`, `test_*.*`, `**/__tests__/**`
- `docs:` → `*.md`, `docs/**`, `LICENSE`, `README`, `CONTRIBUTING`, `CHANGELOG`

**For source files - inspect git diff + CHANGELOG:**

- `feat:` → New public APIs, CHANGELOG "Added" section, user-visible capabilities
- `fix:` → Bug fixes, CHANGELOG "Fixed", exception/error handling corrections
- `refactor:` → Internal restructuring, file moves/renames, no CHANGELOG entry
- `perf:` → Performance improvements without behavior changes

**Breaking changes (!:):**

- API/schema removals or incompatible changes
- CHANGELOG "Removed" section entries
- Migration code or deprecation warnings for users

**Scopes from paths:**

- Map primary source subdirectories to scopes (e.g., `src/api/*` → `(api)`)
```

Adapt glob patterns to actual repository structure found in step 2.

**When merging with existing partial rules:**

- Preserve project-specific customizations (unique scopes, special file patterns)
- Supplement missing categories from template
- Consolidate duplicate information
- Maintain token efficiency

### 8. Insert or Consolidate Rules in CLAUDE.md

**For new rules (no existing guidance):**

- Insert at identified location from step 6
- Update any "Conventional commits" mention to "Conventional commits (see rules below)"
- Add blank lines before/after for markdown formatting

**For consolidation (scattered/partial rules):**

- Remove all scattered conventional commit sections
- Create single consolidated section at best location
- Merge all existing content with generated template
- Update all cross-references to point to new consolidated section
- Preserve formatting and indentation

### 9. Verify Formatting

Check if markdown linting is present:

```bash
[ -f .markdownlint.json ] && echo "has-linting" || echo "no-linting"
```

If linting exists, ensure blank lines surround all list blocks in the inserted section.

## Output Format

Provide concise summary based on action taken:

**If no changes needed:**

```txt
CLAUDE.md already has comprehensive conventional commit rules. No changes needed.
```

**If consolidated:**

```txt
Consolidated scattered conventional commit rules into unified section at line X.
Preserved project-specific customizations: [list any unique patterns]
```

**If added/enhanced:**

```txt
Added conventional commit rules to CLAUDE.md at line X.
Rules cover: [list detected project patterns]
Enhanced existing partial rules with: [missing categories added]
```

## Error Handling

- If CLAUDE.md missing: "CLAUDE.md not found. Create it first with project context."
- If no suitable insertion point: "Could not locate appropriate section. Suggest adding after
  project description."
- If repository structure unclear: "Could not determine project structure. Manual rules
  customization needed."
