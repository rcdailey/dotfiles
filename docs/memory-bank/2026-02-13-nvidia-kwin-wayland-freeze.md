# NVIDIA 580 + kwin_wayland System Freeze

Date: 2026-02-13
Status: Mitigated (switched to proprietary kernel module; monitoring for recurrence)
System: Fedora 43 KDE Plasma, i5-13600KF, RTX 3080, 32GB RAM, NVIDIA 580.119.02

## Incident

At approximately 12:02 on Feb 13, 2026, the system became completely unresponsive, requiring a hard
reset. The user had just launched VS Code in ~/code/home-ops. The system had been up since Feb 5
(8-day uptime).

## Investigation Timeline

### What the logs showed

From `journalctl -b -1`:

- **11:58:59**: Screen unlock via fingerprint (fprintd)
- **11:59:02**: kscreenlocker_greet hit EGL_BAD_ALLOC (0x3003) three times during unlock (later
  determined to be a recurring, harmless bug)
- **12:02:33**: VS Code launched (`app-org.chromium.Chromium-2437683.scope`)
- **12:02:37**: First kwin_wayland warning: "event processing lagging behind by 79ms, your system
  is too slow"
- **12:02:42**: First of many "The main thread was hanging temporarily!" from kwin_wayland
- **12:02:42 to 12:05:18**: Repeated kwin hangs, never recovered
- **12:05:18**: Last log entry from previous boot (hard reset occurred around this time)

### Key finding: prior GPU instability in same boot

On Feb 12 at 21:12 (same boot, ~15 hours earlier), a shorter freeze occurred with a clear GPU
error. Vivaldi logged:

```
GPU state invalid after WaitForGetOffsetInRange
```

This is a Chromium GPU process error indicating the NVIDIA driver returned invalid state from its
command buffer. Kwin hung for ~20 seconds with input lag up to 632ms, then recovered.

### What was ruled out

- **OOM**: No OOM killer messages. 32GB RAM + 8GB zram swap, only 4GB used at current boot.
- **CPU overload from VS Code/mise**: User opens this workspace routinely without issues. The
  workspace is 78MB, 564 files; nothing unusual.
- **Kernel GPU Xid errors**: None logged (but absence is expected when GPU stalls so badly the
  driver can't even report).
- **NVIDIA NVRM errors**: None logged.
- **Coredumps**: No relevant coredumps from the event.
- **kscreenlocker EGL errors**: Occur on every single screen unlock across the entire boot (Feb 5
  through Feb 13). Not related to the freeze.

## Root Cause

**Known NVIDIA 580 driver regression on Wayland compositors.** The GPU command submission path
stalls, starving kwin_wayland of frames. Since kwin_wayland is the Wayland compositor, when it
blocks on the GPU, the entire desktop freezes (input, rendering, everything).

## Supporting Evidence from Community

This is a widespread, well-documented issue:

### NVIDIA Developer Forums

- ["Random crashes on wayland since driver 580 on Linux"](https://forums.developer.nvidia.com/t/random-crashes-on-wayland-since-driver-580-on-linux/345527)
  -- RTX 3070 user reports identical symptoms: system freeze requiring hard poweroff, no useful
  dmesg/journalctl output, only happens on Wayland (not X11). Persists through driver 590. Both
  `nvidia` and `nvidia-open` affected.

- ["Nvidia 580 on KDE wayland freezes"](https://forums.developer.nvidia.com/t/nvidia-580-on-kde-wayland-freezes/355175)
  -- RTX 3060 on Fedora 43 with KDE Wayland. Exact same symptoms.

- ["Kwin_Wayland page flip hang when fully loading system on 580.105.08"](https://forums.developer.nvidia.com/t/kwin-wayland-page-flip-hang-when-fully-loading-system-on-580-105-08/352526)
  -- Shows kwin pageflip hangs under CPU load can trigger GPU driver stall.

- Multiple "Pageflip timed out! This is a bug in the nvidia-drm kernel driver" reports across 570
  and 580 series.

### GitHub Issues

- [NVIDIA/open-gpu-kernel-modules#807](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/807)
  -- "Monitor freezes shortly after boot" with kwin_wayland pageflip timeouts.

- [NVIDIA/open-gpu-kernel-modules#1008](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1008)
  -- RTX 3070 on 590.48.01: Xid 69 errors and GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT causing black
  screens. Reporter confirms **proprietary driver does not exhibit the issue**.

- [zed-industries/zed#35948](https://github.com/zed-industries/zed/issues/35948) -- Hang after
  drawing first frame with NVIDIA 580 drivers on Wayland. Linked to wp_fifo_manager_v1 protocol
  support added in 580.65.06.

### KDE Bugzilla

- [Bug 495765](https://bugs.kde.org/show_bug.cgi?id=495765) -- "Resume from sleep and unlock
  screen freezes laptop" with kwin_wayland_drm hanging. Filed against kwin, but appears to be
  NVIDIA driver-side.

## Open vs Proprietary Driver Analysis

### For RTX 3080 (Ampere/Turing+):

- NVIDIA recommends open kernel modules for Turing and newer (RTX 20xx+).
- Both open and proprietary use the same proprietary userspace libraries.
- The difference is only in the kernel module: `nvidia-open` (open source) vs `nvidia` (proprietary
  blob).
- One GitHub reporter (issue #1008) explicitly confirmed the freeze does NOT happen with the
  proprietary kernel module on the same driver version (590.48.01).
- However, NVIDIA is phasing out the proprietary kernel module. The 590 series on Arch Linux already
  defaults to nvidia-open. Fedora RPM Fusion still ships both.

### Recommendation

Try switching to the **proprietary kernel module** (`kmod-nvidia` instead of `kmod-nvidia-open` on
RPM Fusion) as a diagnostic step, since at least one reporter confirmed it resolves the freeze.
This does not change the userspace driver, only the kernel module.

## Driver Availability

As of 2026-02-13:

- Fedora 43 RPM Fusion NVIDIA repo only has 580.x (580.95.05 and 580.119.02).
- 590.x is not yet packaged for Fedora 43 in RPM Fusion.
- 590.48.01 exists on Arch (nvidia-open 590.48.01-3) and has mixed reports; some Wayland freeze
  bugs persist.

## Monitoring

To watch for GPU faults going forward:

```sh
# Check for Xid errors (GPU faults) after any freeze
journalctl -b -t kernel --grep Xid

# Live monitoring
journalctl -f -t kernel --grep Xid
```

Common Xid codes to watch for:

- **Xid 13**: Graphics Engine Exception
- **Xid 31**: GPU memory page fault
- **Xid 43**: GPU stopped processing
- **Xid 62**: Internal micro-controller halt
- **Xid 69**: Class Error (seen in community reports with open kernel module)
- **Xid 79**: GPU fallen off the bus

## Action Taken (2026-02-13)

Switched from open to proprietary kernel module by disabling akmod auto-detection:

```sh
sudo sh -c 'echo "%_without_kmod_nvidia_detect 1" > /etc/rpm/macros.nvidia-kmod'
sudo akmods --rebuild --force
# reboot
```

Verify after reboot: `cat /proc/driver/nvidia/version` should show `NVIDIA UNIX x86_64 Kernel
Module` (not "Open Kernel Module").

### How to revert

Remove the macro file and rebuild to go back to the open kernel module:

```sh
sudo rm /etc/rpm/macros.nvidia-kmod
sudo akmods --rebuild --force
# reboot
```

## Follow-up Actions

1. **Monitor for recurrence.** If the freeze happens again with the proprietary module, the issue is
   deeper than the open/proprietary distinction and needs a different approach.
2. **When 590 stable lands on RPM Fusion for Fedora 43**, revert to the open kernel module (remove
   `/etc/rpm/macros.nvidia-kmod`, rebuild, reboot) and test whether the open module freeze is fixed
   in the new driver series. As of 2026-02-13, 590 is still beta on Linux; RPM Fusion waits for
   NVIDIA to promote it to stable before packaging. No ETA.
3. After any future kernel update, verify the proprietary module is still active
   (`cat /proc/driver/nvidia/version`). The macro file persists across kernel updates, so akmods
   should continue building the proprietary module automatically.
