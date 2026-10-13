# KernelSU v3.3.1 / GhostSam: Samsung source audit (2026-10-13)

## Verified source references

- Target: upstream `tiann/KernelSU` tag `v3.3.1`, commit `0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d`.
- Samsung fork: `snothin/KernelSU` HEAD `0fde5f940559d36c48c9516902b3a7ce944a80c5`.
- GitHub commit comparison: **diverged**, fork ahead 6 / behind 56 relative to v3.3.1, 19 paths in upstream-to-fork diff. Counts describe commit ancestry; feature equivalence still needs review.
- Device: SM-S9360 / S9360ZCSCCZG1 / kernel `6.6.98-android15-8-...`, KMI `android15-6.6`.
- GhostSam starting point: v0.2.3 (61). **No new `.ko`, `ksud` or APK has been built or installed.**

## IMPORTANT: two different kernel modules

`app/app/src/main/assets/payloads/dirtyfrag/dfr_lkm-android15-6.6.ko` comes from `exploit/src/chains/dirtyfrag/lkm/dfr_lkm.c` and is a **DirtyFrag helper**, not the KernelSU core LKM.

The actual `<kmi>_kernelsu.ko` is embedded in the Samsung fork's `ksud` from `userspace/ksud/bin/aarch64` (see `assets.rs` and `late_load.rs`). A valid upgrade must build the Samsung-compatible `android15-6.6_kernelsu.ko`, embed it into a matched `ksud`, and only then replace GhostSam's `payloads/ksud/ksud`.

## SM-S9360 support boundary

GhostSam `SeriesTable.kt` explicitly lists the S22, S26 and Z Fold8 Ghostlock series, **not** the SM-S9360. Its separate DirtyFrag path advertises `android15-6.6` KMI support, but that is not confirmation that this exact S25+ firmware is compatible with a rebuilt KernelSU core LKM. Treat device support as **unverified** until build-specific checks pass.

## Integration constraints

Fork-specific delta includes `kernel/Kbuild`, Samsung KDP/DEFEX files, `kernel/feature/selinux_hide.c`, syscall hooks, `uapi/supercall.h`, and `userspace/ksud/src/{late_load,restorecon,utils}.rs`. Do not discard these changes when syncing upstream.

The companion workflow `.github/workflows/kernelsu-v331-merge-audit.yml` attempts a throwaway merge to report conflicts. It does **not** publish binaries, execute vulnerabilities, install modules or mutate upstream/fork repositories.

## Required gates before shipping

1. Resolve all upstream/fork merge conflicts with Samsung patches retained.
2. Build core KSU `android15-6.6_kernelsu.ko` for a suitable prepared kernel/DDK environment; review vermagic/config against SM-S9360.
3. Rebuild `ksud` with that core LKM embedded and confirm command/ABI compatibility.
4. Check Manager certificate/signature compatibility, version reporting, and any `ksud-next` interactions.
5. Verify SHA-256 provenance of all binaries, run GhostSam `:app:verifyPayloads` and APK static build, then perform an explicit deployment review.

**Status:** static audit; upgrade not completed. Do not flash `boot.img` on a locked-bootloader device.
