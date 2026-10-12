# NVIDIA 615.71.09 Black Screen on Wake (Driver Locked at 610.57.04)

System: Fedora 44 KDE Plasma (Wayland), kernel 7.2.7, RTX 3080, NVIDIA open kernel module, RPM
Fusion packages.

## Symptom

After upgrading to 615.71.09, the monitors stay black when the system wakes from sleep or idle
display power-off. Downgrading to 610.57.04 fixes it.

## Timeline

- 2026-09-28: the Topgrade offline upgrade (`dnf history` 163) installed 615.71.09 from
  `rpmfusion-nonfree-updates`. The same day, you rebuilt the 610.57.04 RPMs by hand in
  `~/nv610/rpmbuild` and installed them.
- 2026-10-01: the offline upgrade (`dnf history` 169) brought back 615.71.09. You reinstalled
  the 610.57.04 RPMs (`dnf history` 171-173), then ran:

  ```sh
  sudo dnf versionlock add akmod-nvidia xorg-x11-drv-nvidia* nvidia-settings \
    nvidia-persistenced nvidia-modprobe
  ```

  These commands ran in a terminal, not in an OpenCode session. Before this doc, nothing about
  the issue was written down.

`~/nv610` has the rpmbuild tree, the extracted sources, and the RPM Fusion 615.71.09 source RPMs.
These are build files only. You can delete the directory after you remove the lock.

## Upstream issue

The most likely match is
[NVIDIA/open-gpu-kernel-modules#1371](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1371):
"615.71.09: display deadlock on DPMS wake". With KWin, both monitors stay black after the displays
blank. One commenter (RTX 3090) reports that rolling back to 610.57.04 fixed it.

Related 615.71.09 reports in the same repository: #1392 (DisplayPort monitor power cycling hangs
KWin), #1361 (atomic commits block for 3 s per head), and #1408 (GSP channel allocation fails after
monitors wake).

## Status as of 2026-10-12

- #1371 is still open, and NVIDIA has not replied.
- The newest driver is 615.78.08 (2026-10-06). News coverage of its release notes mentions a
  suspend change (`NVreg_UseKernelSuspendNotifiers=1` is now the default) but no fix for a black
  screen on wake. The official release-notes page did not load, so this is unconfirmed.
- On #1371, people who tried 615.78.08 disagree. One says the problem is gone. Another says the
  login screen appears after wake, but the desktop stays black for about 45 seconds.
- RPM Fusion for Fedora 44 has 615.78.08 only in updates-testing. Stable updates still offer
  615.71.09.

Decision: keep the lock.

## Next check

1. Read the latest #1371 comments and status:
   `gh issue view 1371 -R NVIDIA/open-gpu-kernel-modules --comments`.
2. Check the release notes of every driver newer than 615.78.08 for a fix to the wake or
   display-blanking deadlock.
3. Check the versions that RPM Fusion offers: `dnf list --showduplicates xorg-x11-drv-nvidia`.

To test a fixed driver, remove the lock and upgrade:

```sh
sudo dnf versionlock delete akmod-nvidia 'xorg-x11-drv-nvidia*' nvidia-settings \
  nvidia-persistenced nvidia-modprobe
sudo dnf upgrade --refresh
```

Then test both sleep and idle display power-off. If the black screen comes back, reinstall the
610.57.04 RPMs from `~/nv610/rpmbuild/RPMS/x86_64` and add the lock again.

## Risk while locked

Each new kernel needs akmods to build 610.57.04. A future kernel can break that build. In #1408,
a reporter could not build 610.43.02 with DKMS on kernel 7.2.8. If a kernel update leaves no
NVIDIA module, boot the previous kernel from GRUB.
