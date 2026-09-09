# NVIDIA 580 + kwin_wayland System Freeze

Date: 2026-02-13
Status: Open module installed for next boot; reboot and runtime verification pending (2026-09-09)
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

## Review and repository repair (2026-09-09)

The February root-cause statement was stronger than the evidence supports. Logs implicated the
GPU/Wayland path but did not prove an open-module defect. No upstream fix for this exact incident
was verified in the follow-up research. Switching back is a stability retest, not a proven repair.

Inspection found Fedora 44, RTX 3080, kernel `7.1.12-200.fc44.x86_64`, and proprietary NVIDIA
`610.57.04`. The February RPM macro still forced proprietary builds. Secure Boot was disabled.
No matching KWin hang/pageflip warnings were found since August 1. Earlier GPU faults involved
Plex on February 20 and Python on June 20; these do not establish recurrence of the original freeze.

### Package-source conflict and completed repair

NVIDIA's CUDA repository offered `nvidia-driver-common` 615.71.09 while RPM Fusion supplied
610.57.04. Their packages overlapped on driver libraries and executables, blocking DNF upgrades.
This conflict is separate from the open/proprietary kernel-module choice.

- Removed NVIDIA's `nvidia-driver-common`; RPM Fusion packages retain its required driver files.
- Replaced `nvidia-libXNVCtrl` with Fedora's `libXNVCtrl`.
- Reinstalled `nvidia-modprobe`, `nvidia-persistenced`, and `nvidia-settings` from RPM Fusion.
- Reinstalled the affected RPM Fusion graphics, CUDA-library, and power packages at 610.57.04.
- Restored the previously enabled `nvidia-powerd` service after a removal script disabled it.
- Kept NVIDIA's CUDA repository enabled and preserved the CUDA 13.3 toolkit.

DNF config-manager now excludes competing packages from `cuda-fedora44-x86_64`:

```ini
excludepkgs=nvidia*,libnvidia*,kmod-nvidia*,xorg-x11-nvidia*,cuda-drivers*,dnf-plugin-nvidia
```

This override is specific to the Fedora 44 repository ID. When changing Fedora releases or adding
a replacement CUDA repository, verify that the exclusions apply to the new repository too.

`dnf check` and RPM verification of the repaired packages passed. An all-repository upgrade with
`tsflags=test` passed the RPM transaction check without installing the proposed system updates.
The repair invalidated the previously prepared offline update; rerun Topgrade to prepare it again.

ComfyUI uses GPU computation. Its existing environment at `~/diffusion/comfyui/.venv` reported
PyTorch `2.13.0+cu130`, CUDA runtime 13.0, and successfully computed a small tensor on the RTX 3080
after the repair. The system toolkit is distinct from that runtime and was left unchanged.

### Authorized open-module retest

Recorded before changing the kernel-module selection. The user stopped ComfyUI and authorized
returning to the open module. Preserve the driver version, CUDA packages, and repository repair.

1. Inspect the current akmods selection and installed kernels; preserve a proprietary fallback.
2. Back up and remove `/etc/rpm/macros.nvidia-kmod`, then rebuild the target NVIDIA module.
3. Verify the open module on disk and update the target initramfs if necessary.
4. Leave reboot to the user; verify the loaded module and ComfyUI GPU computation afterward.

If the retest fails, restore `%_without_kmod_nvidia_detect 1` in the original macro file, rebuild
the proprietary module and target initramfs, and reboot. Do not undo the repository repair.

### Open module installed (2026-09-09)

Backed up the original macro and the current kernel's proprietary module RPM under
`/var/lib/nvidia-cutover-2026-09-09/` (root-only directory), then removed the active macro and ran:

```sh
pkexec akmods --rebuild --force --akmod nvidia --kernels 7.1.12-200.fc44.x86_64
```

The build and installation succeeded. The module on disk reports version `610.57.04` and license
`Dual MIT/GPL`, confirming the open variant. The default boot kernel is `7.1.12-200.fc44.x86_64`.
Its initramfs contains no NVIDIA display-driver modules, so no stale proprietary display module
needs replacing there. `dnf check` passed after the build.

Kernel `7.1.8-200.fc44.x86_64` retains its proprietary module as a fallback; select it from GRUB if
the new boot fails. The oldest installed kernel was also left untouched. Future akmods builds use
automatic selection because the override is absent.

The running kernel still has the proprietary module loaded. No reboot, module unload, or full
system upgrade was performed. After reboot, check `/proc/driver/nvidia/version` for
`Open Kernel Module`, run `nvidia-smi`, and test ComfyUI rendering. Stability remains unverified.

To restore the saved proprietary build for the current kernel without recompiling:

```sh
pkexec cp /var/lib/nvidia-cutover-2026-09-09/macros.nvidia-kmod /etc/rpm/macros.nvidia-kmod
pkexec dnf reinstall --disablerepo=cuda-fedora44-x86_64 \
  /var/lib/nvidia-cutover-2026-09-09/kmod-nvidia-7.1.12-200.fc44.x86_64-610.57.04-1.fc44.x86_64.rpm
```

Verify the restored on-disk module reports license `NVIDIA` before rebooting. These recovery
instructions are specific to the saved kernel and driver version; do not apply that RPM to a
different kernel. If a later initramfs embeds the display modules, rebuild it after restoring.
