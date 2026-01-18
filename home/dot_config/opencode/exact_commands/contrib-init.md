---
description: Initialize research-only session for third-party repository contribution
---

Analyze this repository for contribution requirements. This is research-only - do not modify any
files. Optional focus area: $ARGUMENTS

## Phase 1: Repository Discovery

Run in parallel:

1. **Structure**: Examine root files (README.md, package.json, Cargo.toml, etc.) to identify project
   type, language, architecture
2. **Contributing docs**: Search CONTRIBUTING.md, docs/contributing/, .github/CONTRIBUTING.md,
   DEVELOPMENT.md, README contribution sections
3. **Code conventions**: Analyze existing code for naming, indentation, import organization. Check
   .editorconfig, .eslintrc, .prettierrc
4. **Testing**: Identify test framework, locate test directories, find test commands in
   README/package.json scripts, check CI config
5. **Linting/Formatting**: Find ESLint, Prettier, Black, rustfmt configs and execution commands
6. **Dependencies**: List major dependencies, build tools, dev dependencies

If focus area provided, prioritize analysis of that directory/module.

## Phase 2: Tool Documentation

After Phase 1, use Context7 to research each major library/framework discovered:

- Resolve library IDs and query docs for best practices
- Focus on contribution guidelines specific to each tool

## Output

Summarize findings:

1. Repository structure and purpose
2. Contribution requirements and processes
3. Coding conventions and style
4. Tool inventory with configurations
5. Development workflow checklist

Do not make changes. All actual development happens in subsequent sessions with explicit permission.
