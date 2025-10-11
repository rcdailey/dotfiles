# Disabling Automatic Copy-on-Select (PRIMARY → CLIPBOARD Sync)

## Problem

Text selection in UI applications was automatically copying to the clipboard, overwriting previously
copied content. This was unwanted behavior that interfered with normal clipboard workflow.

## Root Cause

The Cinnamon Settings Daemon clipboard plugin (`csd-clipboard`) was spawning `autocutsel` to perform
bidirectional clipboard synchronization between X11's two selection buffers:

- **PRIMARY** - Auto-filled on text selection (paste with middle-click)
- **CLIPBOARD** - Filled by Ctrl+C (paste with Ctrl+V)

Two `autocutsel` processes were running:
1. `autocutsel` - Syncing CLIPBOARD ↔ cutbuffer
2. `autocutsel -s PRIMARY` - Syncing PRIMARY ↔ cutbuffer

This created unwanted bidirectional sync: selecting text → PRIMARY → CLIPBOARD.

## Solution

Disabled `csd-clipboard` by adding it to Cinnamon's autostart blacklist:

```bash
gsettings set org.cinnamon.SessionManager autostart-blacklist \
  "['gnome-settings-daemon', 'org.gnome.SettingsDaemon', 'gnome-fallback-mount-helper', \
    'gnome-screensaver', 'mate-screensaver', 'mate-keyring-daemon', 'indicator-session', \
    'gnome-initial-setup-copy-worker', 'gnome-initial-setup-first-login', 'gnome-welcome-tour', \
    'xscreensaver-autostart', 'nautilus-autostart', 'nm-applet', 'caja', 'xfce4-power-manager', \
    'touchegg', 'cinnamon-settings-daemon-clipboard']"
```

Then killed running processes:
```bash
killall -9 csd-clipboard autocutsel
```

## Current Behavior

- **Text selection** → PRIMARY only (middle-click paste works)
- **Ctrl+C** → CLIPBOARD (normal copy behavior)
- **No sync** between PRIMARY and CLIPBOARD
- **CopyQ** continues managing clipboard history and persistence

## Background: X11 Clipboard System

### Two Separate Clipboards

X11 has two independent selection buffers:
- **PRIMARY**: Automatically filled when text is selected, paste with middle-click
- **CLIPBOARD**: Filled by explicit copy (Ctrl+C), paste with Ctrl+V

### csd-clipboard Details

Part of `cinnamon-settings-daemon`, a collection of background services managing session-wide
settings in Cinnamon desktop:
- `csd-keyboard` - keyboard settings
- `csd-media-keys` - multimedia key handling
- `csd-power` - power management
- **`csd-clipboard`** - clipboard synchronization and persistence

The clipboard daemon ensures clipboard content persists after source applications close by:
1. Monitoring clipboard changes
2. Taking ownership of selections
3. Using `autocutsel` as backend for PRIMARY ↔ CLIPBOARD sync

### Why autocutsel Was Used

`autocutsel` is specifically designed for bidirectional clipboard synchronization. It tracks changes
in both selections and keeps them synchronized. This is useful for users who want Windows/Mac-like
behavior where selection and clipboard are unified.

### Alternative Considered: One-Way Sync

The original requirement was one-way CLIPBOARD → PRIMARY sync only (opposite direction). This would
allow:
- Clipboard as authoritative source
- Ctrl+C content available in PRIMARY for apps that only support middle-click paste
- No selection → clipboard interference

However, `autocutsel` only supports bidirectional sync. A custom solution would require:
- Clipnotify or custom script watching CLIPBOARD
- Updating PRIMARY on CLIPBOARD changes only
- Running as systemd user service

This was deemed unnecessary since CopyQ already provides clipboard management, and disabling the
sync entirely solved the immediate problem.

## CopyQ Configuration

CopyQ is already configured correctly with `copy_selection=false` in `~/.config/copyq/copyq.conf`,
meaning it doesn't sync selections to clipboard on its own.

## Research Notes

Based on web research (Tavily searches):
- No native Cinnamon/LMDE UI setting exists for controlling selection sync
- Common issue across Linux desktops (many forum discussions)
- Solutions typically involve:
  1. Disabling clipboard manager sync features (e.g., "Sync Selections" in Clipman)
  2. Killing sync daemons like `autocutsel`
  3. Using third-party tools like `hax11` (X11 event interceptor)
- PRIMARY selection behavior is built into X11 itself and cannot be disabled

## Persistence

The gsettings change persists across reboots. The blacklist prevents `csd-clipboard` from
auto-starting on login.

## CRITICAL: CopyQ Must Be Running

**Important finding:** Disabling `csd-clipboard` removes ALL clipboard management, not just
selection sync. Without a clipboard manager running, clipboard data (including screenshots)
disappears immediately after the source application releases it.

**Symptoms when CopyQ not running:**
- Screenshots taken with Ctrl+Shift+PrtScr don't persist in clipboard
- `xclip -selection clipboard -t TARGETS -o` returns "Error: target TARGETS not available"
- VS Code/Claude Code reports "no image data" when trying to paste
- Any copied data vanishes when source application closes

**Solution:** CopyQ must be running to provide clipboard persistence. It's configured to auto-start
(`~/.config/autostart/copyq.desktop`), but if it's not running:

```bash
copyq &
```

**Verification:**
```bash
# Check if CopyQ is running
ps aux | rg copyq | rg -v "rg"

# Should see something like:
# copyq
# /usr/bin/copyq --clipboard-access monitorClipboard
```

**Why CopyQ works perfectly for this use case:**
- `check_clipboard=true` - Monitors and persists clipboard content (including images)
- `check_selection=false` - Doesn't monitor PRIMARY selection
- `copy_selection=false` - Doesn't sync selection to clipboard

This gives exactly the desired behavior: clipboard persistence without selection sync.

## Screenshot Workflow Verification

Tested workflow that confirms working setup:
1. Ctrl+Shift+PrtScr (LMDE built-in screenshot tool)
2. Select region
3. Image captured to clipboard by `gnome-screenshot -a -c`
4. CopyQ takes ownership and persists the image data
5. Can paste into VS Code/Claude Code with Ctrl+V
6. Image data includes proper MIME types (image/png, etc.)

## Trade-offs

Disabling `csd-clipboard` removes the default clipboard manager, but this is intentional. CopyQ
provides superior clipboard management as a full-featured replacement without the unwanted selection
sync behavior.

## Date

2025-10-11
