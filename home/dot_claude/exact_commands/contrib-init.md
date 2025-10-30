---
allowed-tools: Read, Grep, Glob, mcp__octocode__githubSearchCode, mcp__octocode__githubSearchRepositories, mcp__octocode__githubViewRepoStructure, mcp__octocode__githubGetFileContent, mcp__context7__resolve-library-id, mcp__context7__get-library-docs
argument-hint: [focus-area or directive]
description: Initialize session for third-party repository contribution
---

# Third-Party Repository Contribution Initialization

**IMPORTANT**: This command initializes a research-only session for contributing to repositories you
do not own. You are strictly prohibited from making ANY changes to code, configuration, or files
during this initialization phase.

## Focus Area

**Optional Focus**: $ARGUMENTS

If focus guidance is provided, interpret and prioritize research accordingly. Examples:

**Specific paths/areas**:

- `frontend`, `api`, `packages/ui`, `src/auth` - Focus on specific directories or modules
- `documentation`, `tests`, `build system` - Focus on particular aspects

**Natural directives**:

- `Focus on the XYZ tool` - Research XYZ tool integration, configuration, and usage patterns
- `Focus on testing framework` - Deep dive into test structure, patterns, and requirements
- `Focus on deployment pipeline` - Analyze CI/CD, build processes, and deployment workflows

For monolithic repositories, focused analysis helps:

- Concentrate research on relevant areas
- Identify focus-specific conventions and patterns
- Optimize context window usage for targeted contribution
- Find area-specific tooling and configuration

If no focus is provided, perform comprehensive repository-wide analysis.

## Phase 1: Repository Discovery & Analysis

### 1. Repository Structure Analysis

- Examine the root directory structure and key files (README.md, package.json, Cargo.toml, setup.py,
  etc.)
- Identify the project type, language, and overall architecture
- Look for standard configuration files (.gitignore, .editorconfig, etc.)
- **If focus area specified**: Pay special attention to the target directory/project structure, its
  specific dependencies, and how it relates to the broader repository

### 2. Contributing Guidelines Discovery

Search for and thoroughly read contribution documentation:

- CONTRIBUTING.md (root and docs/ directory)
- docs/contributing/ directory
- .github/CONTRIBUTING.md
- docs/development.md or docs/dev.md
- DEVELOPMENT.md
- README sections on contributing
- Wiki pages related to contribution

### 3. Code Convention Analysis

- Examine existing code files to understand:
  - Indentation style (tabs vs spaces)
  - Naming conventions (camelCase, snake_case, PascalCase)
  - File organization patterns
  - Comment styles and documentation patterns
  - Import/include organization
- Look for style guide documentation (STYLE.md, style guides in docs/)
- Check for .editorconfig, .eslintrc, .prettierrc, or similar configuration files
- **If focus area specified**: Analyze code patterns specifically within the target area, as
  conventions may vary between different parts of large repositories

### 4. Testing Framework Identification

- Identify testing tools and frameworks used
- Locate test directories and files
- Find test configuration files (jest.config.js, pytest.ini, Cargo.toml [dev-dependencies], etc.)
- Understand test execution commands from README or package.json scripts
- Look for CI/CD configuration (.github/workflows/, .gitlab-ci.yml, etc.)
- **If focus area specified**: Look for area-specific test patterns, test directories, and testing
  requirements that may differ from the general repository approach

### 5. Linting & Formatting Tools Discovery

- Identify linting tools (ESLint, Pylint, Clippy, etc.)
- Find formatting tools (Prettier, Black, rustfmt, etc.)
- Locate configuration files for these tools
- Check package.json scripts, Makefile, or justfile for lint/format commands
- Look for pre-commit hooks configuration

### 6. Dependency & Tooling Inventory

- List all major dependencies and their versions
- Identify build tools (Webpack, Vite, Cargo, etc.)
- Note development dependencies and tools
- Check for dependency management files (package-lock.json, Cargo.lock, requirements.txt, etc.)
- **If focus area specified**: Prioritize dependencies and tooling relevant to the target area,
  including area-specific build processes, scripts, or configuration files

## Phase 2: Tool Documentation Lookup

**AFTER** completing Phase 1 discovery, use context7 to research the specific tools and libraries
identified:

### 7. Library & Framework Documentation

For each major library, framework, or tool discovered in Phase 1:

- Use context7 resolve-library-id to find the proper library ID
- Use context7 get-library-docs to obtain authoritative documentation
- Focus on best practices, coding conventions, and contribution guidelines specific to each tool

### 8. Technology Stack Research

- Research best practices for the identified tech stack combination
- Look up current versions and compatibility requirements
- Understand proper usage patterns and anti-patterns

## Core Instructions & Safety Constraints

### Research-Only Mode

- **NEVER make any changes to code, configuration, or files**
- **NEVER run commands that modify the repository state**
- Focus exclusively on understanding and documentation
- All work must be investigative and read-only

### Systematic Approach

- Complete Phase 1 BEFORE moving to Phase 2
- Take comprehensive notes on findings
- Identify any conflicting or unclear requirements
- Ask for clarification if contribution guidelines are ambiguous

### Contribution Compliance

- Follow ALL discovered contribution guidelines exactly
- Respect existing code conventions without exception
- Use the same tools and processes as the existing codebase
- Adhere to any specified commit message formats or PR requirements

### Verification Requirements

- Identify all linting, formatting, and testing tools
- Note the exact commands needed to verify work
- Understand the full development workflow expected by maintainers
- Prepare to use existing tooling for validation

## Expected Outcome

After running this command, you should have:

1. Complete understanding of the repository structure and purpose
2. Clear knowledge of contribution requirements and processes
3. Comprehensive documentation of coding conventions and style
4. Inventory of all tools and their configurations
5. Authoritative documentation for all identified technologies
6. Ready-to-follow checklist for future contribution work

**Remember**: This is initialization only. All actual development work should happen in subsequent
sessions with explicit user permission and following the guidelines discovered here.
