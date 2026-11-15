# NVIDIA 615.71.09 Black Screen on Wake (Driver Locked at 610.57.04)

- Date: 2026-09-28
- Status: Mitigated: driver locked at 610.57.04, kernel locked at 7.2.15 (2026-11-15)
- System: Fedora 44 KDE Plasma (Wayland), kernel 7.2.15, RTX 3080, NVIDIA open kernel module, RPM
  Fusion packages

## Symptom

After upgrading to 615.71.09, the monitors stay black when the system wakes from sleep or idle
display power-off. Downgrading to 610.57.04 fixes it.

## Cause

Suspected, not confirmed. The most likely match is
[NVIDIA/open-gpu-kernel-modules#1371](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1371):
"615.71.09: display deadlock on DPMS wake". With KWin, both monitors stay black after the displays
blank. One commenter (RTX 3090) reports that rolling back to 610.57.04 fixed it.

Related 615.71.09 reports in the same repository: #1392 (DisplayPort monitor power cycling hangs
KWin), #1361 (atomic commits block for 3 s per head), and #1408 (GSP channel allocation fails after
monitors wake).

## Actions

- 2026-09-28: the Topgrade offline upgrade (`dnf history` 163) installed 615.71.09 from
  `rpmfusion-nonfree-updates`. The same day, you rebuilt the 610.57.04 RPMs by hand in
  `~/nv610/rpmbuild` and installed them.
- 2026-10-01: the offline upgrade (`dnf history` 169) brought back 615.71.09. You reinstalled the
  610.57.04 RPMs (`dnf history` 171-173), then ran:

  ```sh
  sudo dnf versionlock add akmod-nvidia xorg-x11-drv-nvidia* nvidia-settings \
    nvidia-persistenced nvidia-modprobe
  ```

  These commands ran in a terminal, not in an OpenCode session. Before this doc, nothing about the
  issue was written down.

`~/nv610` has the rpmbuild tree, the extracted sources, and the RPM Fusion 615.71.09 source RPMs.
These are build files only. You can delete the directory after you remove the lock.

- 2026-11-15: the Topgrade offline upgrade installed kernel 7.3.3. akmods could not build 610.57.04
  for it: `nvidia/os-interface.c:2820` passes an integer where 7.3 changed
  `dmem_cgroup_register_region` to take a pointer. The log is
  `/var/cache/akmods/nvidia/610.57.04-1-for-7.3.3-200.fc44.x86_64.failed.log`. The machine booted
  7.3.3 on nouveau, with a low-resolution login screen and a black desktop after login. Fixed by
  making 7.2.15 (which has the 610.57.04 open module) the default and locking every installed
  kernel:

  ```sh
  sudo grubby --set-default /boot/vmlinuz-7.2.15-200.fc44.x86_64
  sudo dnf versionlock add kernel kernel-core kernel-modules kernel-modules-core \
    kernel-modules-extra kernel-devel
  ```

  The lock covers 7.2.11, 7.2.15, and 7.3.3. Without it, Fedora makes each new kernel the default
  (`UPDATEDEFAULT=yes` in `/etc/sysconfig/kernel`) and keeps only three, so later upgrades would
  remove 7.2.15. To undo, run `sudo dnf versionlock delete 'kernel*'`, then set the new default with
  `grubby`.

## Current state

As of 2026-11-15:

- #1371 is still open with no fix released. A 2026-11-04 comment thanks someone for filing it
  internally; who filed it is unverified.
- RPM Fusion stable for Fedora 44 offers 620.70.06 (2026-11-04). It builds on 7.3.3: a CachyOS user
  runs it on that kernel. That user reported on #1371 (2026-11-12, RTX 4080, GNOME) one hard hang in
  six blanking events on 620.70.06, so the bug is not specific to KWin.
- Newer reports of the same symptom on 615.78.08:
  [#1476](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1476) (one comment: RTX 3080
  desktop, KDE Wayland, kernel 7.3, black screen after resume; another reporter also saw it on
  610.57.04) and the Arch forum thread [315387](https://bbs.archlinux.org/viewtopic.php?id=315387)
  (KDE, intermittent black screens after resume).
- The released highlights for 615.78.08 and 620.70.06 list no wake or blanking fix. These came from
  secondhand summaries, not NVIDIA's release-note pages.

Decision: keep both locks. Kernel updates stop until a driver fixes the wake bug.

## Next check

1. Read the latest #1371 comments and status:
   `gh issue view 1371 -R NVIDIA/open-gpu-kernel-modules --comments`.
2. Read new comments on #1476: `gh issue view 1476 -R NVIDIA/open-gpu-kernel-modules --comments`.
3. Check the release notes of every driver newer than 620.70.06 for a fix to the wake or
   display-blanking deadlock.
4. Check the versions that RPM Fusion offers: `dnf list --showduplicates xorg-x11-drv-nvidia`.

To test a fixed driver, remove both locks and upgrade:

```sh
sudo dnf versionlock delete akmod-nvidia 'xorg-x11-drv-nvidia*' nvidia-settings \
  nvidia-persistenced nvidia-modprobe 'kernel*'
sudo dnf upgrade --refresh
```

After the reboot, check that `/proc/driver/nvidia/version` shows the new driver on the new kernel.
Then test both sleep and idle display power-off. If the black screen comes back, boot 7.2.15 from
GRUB, reinstall the 610.57.04 RPMs from `~/nv610/rpmbuild/RPMS/x86_64`, and add both locks again.

### Risk while locked

610.57.04 does not build on kernel 7.3 or newer, so the kernel cannot move forward until the driver
does. 7.2.15 gets no more security or bug fixes while the lock holds.
