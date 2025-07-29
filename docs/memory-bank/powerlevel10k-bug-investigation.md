# Powerlevel10k Bug Investigation Memory Bank

## Issue Summary

**GitHub Issue**: [#2887](https://github.com/romkatv/powerlevel10k/issues/2887) - "Tab completion triggers 'bad pattern: (utf|UTF)(-|)8' error in _p9k_on_expand"

**Status**: Active bug report filed with minimal reproduction case provided to maintainer

**Core Problem**: Powerlevel10k's `_p9k_on_expand` function continuously spams error messages during tab completion, creating an infinite loop that requires terminal restart.

**Error Pattern**:

```
_p9k_on_expand:7: bad pattern: (utf|UTF)(-|)8
git commit
_p9k_on_expand:7: bad pattern: (utf|UTF)(-|)8
git commit  
_p9k_on_expand:7: bad pattern: (utf|UTF)(-|)8
git commit
```

## Root Cause Analysis

**Technical Details**:

- The issue stems from a malformed pattern in the `__p9k_intro_locale` variable
- Pattern `(utf|UTF)(-|)8` is malformed for zsh pattern matching
- This pattern appears in: `readonly __p9k_intro_locale='[[ $langinfo[CODESET] != (utf|UTF)(-|)8 ]] && _p9k_init_locale && { [[ -n $LC_ALL ]] && local LC_ALL=$__p9k_locale || local LC_CTYPE=$__p9k_locale }'`
- The pattern is hardcoded in Powerlevel10k's locale detection logic

**Trigger Condition**: The bug requires **fzf-tab** to be present. Without fzf-tab, tab completion works normally with just Powerlevel10k + compinit.

## Environment Details

- **OS**: macOS 14.5 (Darwin 24.5.0)
- **Zsh version**: 5.9  
- **Powerlevel10k version**: Latest (commit 36f3045)
- **Terminal**: iTerm2
- **Locale**: All UTF-8 (LANG=en_US.UTF-8, LC_ALL=en_US.UTF-8, LC_CTYPE=en_US.UTF-8)

## Minimal Reproduction Case

**Critical**: This minimal `.zshrc` reproduces the issue (provided to maintainer):

```zsh
# Enable Powerlevel10k instant prompt
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# Load zinit
source ~/.local/share/zinit/zinit.git/zinit.zsh

# Load Powerlevel10k
zinit ice depth=1
zinit load romkatv/powerlevel10k

# Basic completion setup
autoload -Uz compinit
compinit

# Load fzf and fzf-tab
zinit ice silent
zinit load "junegunn/fzf"
zinit ice silent  
zinit load "Aloxaf/fzf-tab"

# Enable fzf-tab
enable-fzf-tab

# Load p10k config
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

# Finalize Powerlevel10k
p10k finalize
```

**Reproduction Steps**:

1. Use the above `.zshrc`
2. Open new terminal
3. Type `git commit` (with trailing space)
4. Press TAB
5. Observe continuous error spam that cannot be interrupted with Ctrl+C

## Working Workaround

**Location**: `/Users/robert/.local/share/chezmoi/home/dot_config/exact_zsh/completion.sh`

```bash
# Workaround for Powerlevel10k bug: malformed pattern (utf|UTF)(-|)8 in __p9k_intro_locale
# This suppresses stderr from _p9k_on_expand until the upstream bug is fixed
# See: hardcoded pattern in __p9k_intro_locale variable causes "bad pattern" errors
if (( $+functions[_p9k_on_expand] )); then
    functions[_p9k_on_expand_orig]=$functions[_p9k_on_expand]
    _p9k_on_expand() {
        { _p9k_on_expand_orig "$@" } 2>/dev/null
    }
fi
```

**Why This Works**: Wraps the `_p9k_on_expand` function to suppress stderr output while preserving functionality.

## Investigation Timeline

1. **Initial Problem**: User reported fzf-tab completion issues (arrow keys not working, no selection visible)
2. **fzf-tab Fix**: Resolved by fixing plugin loading order and adding `enable-fzf-tab` command
3. **New Bug Discovery**: Error spam appeared during `git commit <TAB>` completion
4. **Systematic Debugging**: Eliminated various suspects (noglob alias, Oh-My-Zsh plugins, locale settings)
5. **Root Cause Identification**: Found malformed pattern in `__p9k_intro_locale` variable
6. **Attempted Solutions**: Tried proper UTF-8 locale configuration and other research-based fixes
7. **Workaround Implementation**: Applied stderr suppression when proper fixes failed
8. **Minimal Reproduction**: Systematically identified that fzf-tab is required to trigger the bug
9. **Bug Report Filed**: Created GitHub issue #2887 with comprehensive details

## Key Configuration Files Modified

### `/Users/robert/.local/share/chezmoi/home/dot_config/exact_zsh/init/03-plugins.sh`

- Modified plugin loading order to load fzf-tab immediately after compinit
- Added `enable-fzf-tab` command

### `/Users/robert/.local/share/chezmoi/home/dot_config/exact_zsh/completion.sh`  

- Contains the stderr suppression workaround
- Previously removed then restored explicit fzf-tab configurations

### `/Users/robert/.local/share/chezmoi/home/dot_config/exact_zsh/init/02-environment.sh`

- Added UTF-8 locale configuration (didn't fix the bug but kept for compatibility)

### `/Users/robert/.local/share/chezmoi/home/dot_zshrc`

- Added shell options for Powerlevel10k compatibility
- Added `p10k finalize` at the end

### `/Users/robert/.local/share/chezmoi/home/dot_config/exact_zsh/aliases.sh`

- Restored `alias git='noglob git'` (was temporarily removed during debugging)

## Communication with Maintainer

**GitHub Issue**: <https://github.com/romkatv/powerlevel10k/issues/2887>

**Maintainer Request**: Asked for minimal `.zshrc` that reproduces the problem
**Our Response**: Provided the minimal reproduction case above, demonstrating that fzf-tab is required to trigger the bug

**Current Status**: Awaiting maintainer response to the minimal reproduction case

## Important Notes for Future Sessions

1. **DO NOT** reply to GitHub issues without explicit user approval
2. The workaround is legitimate and addresses an upstream bug - not a "hack"
3. User has working fzf-tab completion with the workaround in place
4. The pattern `(utf|UTF)(-|)8` appears to be a regex that needs proper escaping for zsh pattern matching
5. The bug creates an infinite loop requiring terminal restart - Ctrl+C is unresponsive
6. Testing should be done by modifying `~/.zshrc` directly for faster turnaround, then restored with `chezmoi apply`

## Environment Setup

- **Dotfiles Manager**: chezmoi with root at `home/` directory
- **Plugin Manager**: zinit
- **Shell**: zsh with modular configuration in `~/.config/zsh/`
- **Zinit Location**: `~/.local/share/zinit/zinit.git/zinit.zsh`
- **User Preference**: Commands provided as one-liners piped to `pbcopy` when possible

## Next Steps (When Maintainer Responds)

1. Monitor GitHub issue for maintainer response
2. Provide any additional information requested
3. Test any proposed fixes against the minimal reproduction case
4. Update workaround or remove it once upstream fix is available
5. Document resolution in this memory bank
