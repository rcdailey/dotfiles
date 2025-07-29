# Zsh Configuration Reorganization Project Memory Bank

## Project Overview

**Objective**: Completely reorganize zsh shell scripts sourced from `.zshrc` to prioritize correct initialization order based on comprehensive research, while consolidating for maintainability.

**Date**: July 29, 2025
**Status**: Implementation Phase
**Priority**: CRITICAL - Initialization order correctness over all other concerns

## Research Foundation

### Primary Research Source
Comprehensive research on optimal zsh shell component initialization order based on current best practices and official documentation. Key findings:

1. **Environment Variables & PATH modifications** (including mise/rtx) - FIRST
2. **Powerlevel10k Instant Prompt** (if used) - VERY EARLY
3. **Zinit Plugin Manager initialization** - BEFORE compinit
4. **Completion system setup** (fpath, then compinit) - FOUNDATION
5. **fzf-tab plugin** (after compinit, before widget-wrapping plugins) - STRICT TIMING
6. **Widget-wrapping plugins** (autosuggestions, syntax highlighting) - AFTER fzf-tab
7. **Aliases, functions, and platform-specific configurations** - LAST

### Critical Timing Requirements Discovered

#### Powerlevel10k Instant Prompt
- Must be placed very early in `.zshrc`
- Any code requiring console input (password prompts, confirmations) must go ABOVE instant prompt block
- Console output during initialization may appear uncolored
- Environment variables and PATH modifications should be placed before instant prompt for best compatibility

#### fzf-tab Strict Dependencies
- Must load AFTER `compinit`
- Must load BEFORE plugins that wrap widgets (zsh-autosuggestions, syntax highlighting)
- Completions should be configured BEFORE `compinit`
- Without proper timing, tab completion breaks

#### Mise/RTX Tool Activation
Research showed optimal approach:
```zsh
# Environment setup BEFORE instant prompt
eval "$(mise env -s zsh)"

# Powerlevel10k instant prompt here

# Hook activation AFTER instant prompt
eval "$(mise activate zsh)"
```

## Chicken-and-Egg Issues Identified

### Critical Issue #1: XDG Variables + Zinit Initialization
**Problem**: Zinit uses `ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"` but numbered file approach would set XDG variables AFTER Zinit initializes.

**Research Finding**: XDG variables should be set in `.zshenv`, not `.zshrc`, to be available before any plugin managers initialize.

**Solution**: Create `dot_zshenv` with XDG variable declarations.

### Critical Issue #2: Powerlevel10k vs Environment Variables
**Problem**: P10k instant prompt should be "close to the top of ~/.zshrc" but environment setup may produce console output.

**Research Finding**: "Initialization code that may require console input must go above instant prompt block; everything else may go below."

**Solution**: Split environment setup - console-safe components before instant prompt, others after.

### Critical Issue #3: fzf-tab vs Zinit Turbo Mode
**Problem**: fzf-tab requires strict sequential timing but Zinit turbo mode loads asynchronously.

**Research Finding**: fzf-tab "needs to be loaded after compinit, but before plugins which will wrap widgets."

**Solution**: Load fzf-tab immediately (no turbo), use turbo only for safe-to-defer plugins.

### Critical Issue #4: Mise Split Strategy
**Problem**: Research inconsistency - splitting `mise env` and `mise activate` may eliminate project-aware functionality.

**Web Search Finding**: "`mise activate` provides dynamic directory-aware updates while `mise env` is static."

**Resolution**: Maintain split for instant prompt compatibility but preserve dynamic capability through strategic placement.

## Cross-Reference Analysis Results

Comprehensive cross-reference between original research and additional web search findings showed:

- **100% alignment** on Powerlevel10k instant prompt placement
- **100% alignment** on fzf-tab timing requirements  
- **100% alignment** on Zinit turbo mode benefits
- **100% alignment** on XDG variables early placement
- **One inconsistency identified**: Mise split strategy conflicts with core functionality, but resolved through strategic implementation

## Final Solution Architecture

### Directory Structure
```
home/
├── dot_zshenv                      # XDG variables (critical dependency fix)
├── dot_zshrc                       # Simplified with instant prompt + single loop
└── dot_config/exact_zsh/
    ├── 01-environment.sh           # Non-console-output environment setup
    ├── 02-zinit.sh                # Zinit plugin manager initialization
    ├── 03-completion.sh           # Completion system + P10k bug workaround
    ├── 04-plugins.sh              # All plugin loading (strict timing order)
    ├── 05-configuration.sh        # Aliases, functions, shell options
    └── 06-platform.sh.tmpl        # Consolidated platform-specific configs
```

### Key Design Decisions

#### Single Loop System
**Requirement**: Replace dual loop system in `.zshrc` with single numbered file loop
**Implementation**: One `for` loop loading `~/.config/zsh/*.sh` in numerical order

#### Platform Consolidation
**Requirement**: Consolidate `platforms/darwin.sh`, `linux.sh`, `windows.sh` into single template
**Implementation**: Use chezmoi conditionals: `{{ if eq .chezmoi.os "darwin" }}`
**Benefit**: Easier maintenance with numbered load order approach

#### Powerlevel10k Bug Preservation
**Critical**: Preserve existing workaround for GitHub issue #2887
**Implementation**: Include workaround in `03-completion.sh` with issue link
**Context**: Active upstream bug causing infinite error loop during tab completion

## File Content Mapping

### dot_zshenv (NEW)
**Purpose**: Critical dependency resolution for XDG variables
**Contents**: XDG_CONFIG_HOME, XDG_DATA_HOME, XDG_CACHE_HOME, XDG_STATE_HOME
**Rationale**: Ensures Zinit can resolve ZINIT_HOME before any .zshrc processing

### dot_zshrc (MAJOR RESTRUCTURE)
**New Structure**:
1. Pre-instant prompt: `eval "$(mise env -s zsh)"` (console-safe)
2. Powerlevel10k instant prompt block
3. Single numbered file loading loop
4. Post-loop: `eval "$(mise activate zsh)"` (dynamic functionality)

### 01-environment.sh
**Source Files**: Portions of `exports.sh`, `mise.sh`
**Contents**: EDITOR, LESS, basic exports, history settings
**Excludes**: PATH modifications that might produce output, mise activation
**Rationale**: Environment setup without console output risk

### 02-zinit.sh
**Source Files**: `init/01-zinit.sh`
**Contents**: ZINIT_HOME setup, git clone logic, source zinit.zsh
**Dependencies**: Requires XDG_DATA_HOME from .zshenv
**Rationale**: Plugin manager foundation with proper dependency resolution

### 03-completion.sh
**Source Files**: `completion.sh` + P10k workaround
**Contents**: compinit, completion styles, Powerlevel10k bug workaround
**Critical**: GitHub issue link (https://github.com/romkatv/powerlevel10k/issues/2887)
**Rationale**: Completion foundation before fzf-tab, preserve bug fix

### 04-plugins.sh
**Source Files**: `init/03-plugins.sh` with timing fixes
**Immediate Loading**: P10k theme, completions, fzf-tab (strict timing)
**Turbo Loading**: Syntax highlighting, autosuggestions (safe to defer)
**Rationale**: Maintains fzf-tab requirements within zinit turbo compatibility

### 05-configuration.sh
**Source Files**: `aliases.sh`, `functions.sh`, shell options, `path.sh`
**Contents**: Aliases, functions, shell options, key bindings, PATH modifications
**Rationale**: Configuration that depends on plugins being loaded

### 06-platform.sh.tmpl
**Source Files**: `platforms/darwin.sh`, `platforms/linux.sh`, `platforms/windows.sh`
**Implementation**: Chezmoi conditionals for platform-specific logic
**Rationale**: Single file for platform-specific overrides, easier maintenance

## Testing Strategy

### Automated Testing Limitations
- Non-interactive Bash environment restricts comprehensive testing
- Can validate syntax, file structure, basic functionality
- Cannot fully test interactive features like tab completion

### Manual Testing Requirements
- Critical functionality tests in actual terminal environment
- Plugin loading verification
- Performance benchmarking
- Regression testing for existing functionality
- Platform-specific behavior validation

## Critical Success Criteria

1. **Shell starts without errors or warnings**
2. **All plugins load correctly with proper timing**
3. **Tab completion works without P10k bug triggers**
4. **Platform-specific configurations active**
5. **Performance maintained or improved**
6. **All existing functionality preserved**

## Rollback Strategy

If implementation fails:
1. Use chezmoi to restore previous configuration
2. Backup files created during testing
3. Manual restoration procedures documented
4. User can revert to working state quickly

## Important Notes for Future Sessions

- **Priority Order**: Correctness of initialization > Consolidation > Performance
- **Critical Timing**: fzf-tab must load after compinit, before widget plugins
- **P10k Bug**: Workaround is essential, not optional - GitHub issue #2887
- **XDG Dependencies**: Must be in .zshenv, not .zshrc
- **Mise Functionality**: Split preserves both static and dynamic capabilities
- **Platform Logic**: Consolidated but preserves all existing functionality
- **Testing Required**: Manual verification essential due to interactive nature

## Research Sources Referenced

1. Powerlevel10k GitHub repository documentation
2. Zinit plugin manager documentation and examples
3. fzf-tab plugin requirements and timing documentation
4. Mise tool activation best practices
5. Zsh completion system documentation
6. XDG Base Directory Specification
7. Performance benchmarking tools and methodologies

This reorganization represents a comprehensive modernization of zsh configuration prioritizing correctness, maintainability, and performance while preserving all existing functionality.
