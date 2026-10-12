# KernelSU 32680 × GhostSam Samsung port — verified build and compatibility checkpoint

This is an **offline engineering status report**, not a device installation procedure.

## Exact source revisions

- Official KernelSU 32680: [tiann/KernelSU `0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d`](https://github.com/tiann/KernelSU/commit/0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d)
- Samsung GhostSam fork baseline: [snothin/KernelSU `0fde5f940559d36c48c9516902b3a7ce944a80c5`](https://github.com/snothin/KernelSU/commit/0fde5f940559d36c48c9516902b3a7ce944a80c5)
- Shared ancestor identified by CI: `58aecc40a6eebc677ec82cf8d6ca5bf5d18f2a4d`

## Confirmed GitHub Actions builds

| CI task | Result | Link |
|---|---|---|
| Static source/binary audit | success | [Run #38282972751](https://github.com/ychlhk/GhostSam/actions/runs/38282972751) |
| Official 32680 ARM64 reference ksud | success | [Run #38283595893](https://github.com/ychlhk/GhostSam/actions/runs/38283595893) |
| Official 32680 GKI android15-6.6 reference LKM | success | [Run #38283595893](https://github.com/ychlhk/GhostSam/actions/runs/38283595893) |
| Samsung fork ARM64 baseline ksud | success after fixing broken git dependency sources | [Run #38284357765](https://github.com/ychlhk/GhostSam/actions/runs/38284357765) |
| Samsung fork KDP/DEFEX experimental GKI LKM | success | [Run #38284357765](https://github.com/ychlhk/GhostSam/actions/runs/38284357765) |
| Port feasibility: source ancestry and merge simulation | success; **simulated merge has conflicts** | [Run #38284703518](https://github.com/ychlhk/GhostSam/actions/runs/38284703518) |

The historical `Kernel-SU` Git dependencies referenced by the Samsung fork's Cargo.lock were unavailable. CI's `url.insteadOf` remapping uses the publicly verified `KernelSU2` repository mirrors for the exact pinned commits. No Root implementation was modified to repair this.

## Source merge feasibility

The source-comparison artifact `samsung-32680-port-diff-audit` records:

- 226 files changed on official upstream since their common ancestor
- 19 files changed on the Samsung fork
- 12 paths modified on both sides
- 5 **actual content merge conflicts**:
  1. `kernel/core/init.c`
  2. `kernel/feature/selinux_hide.c`
  3. `kernel/hook/syscall_hook_manager.c`
  4. `uapi/supercall.h`
  5. `userspace/ksud/src/late_load.rs`

Other overlapping source paths, including `kernel/Kbuild`, merit manual review even when Git's three-way merge reports no conflict.

## Outstanding work — do not call this a Samsung 32680 release

1. Resolve all five conflicts by reviewing both control-flow paths, not by choosing one side wholesale.
2. Audit and reapply Samsung KDP/DEFEX and any security-related changes to the official 32680 baseline.
3. Compile **a newly merged source tree** and verify its real build-derived version; do not fake the reported version.
4. Verify any changes to `uapi/supercall.h`, `late_load.rs`, and the loader's wire protocol together.
5. Obtain a suitable build context and symbol compatibility evidence for SM-S9360 kernel `6.6.98-android15-8-p5a696e2-abogkiS9360ZCSCCZG1-4k`.
6. Independently verify manager authorization/signature compatibility, module `vermagic`, symbol CRCs, SELinux behavior, and KDP/DEFEX symbols.

**Safety gate:** none of the produced `.ko` or `ksud` artifacts are verified safe for installation on SM-S9360. Current on-device LKM 32601-2 and installed ksud were not changed. No phone operations, module loading, or flashing have been performed.

This document is intentionally confined to `ksu-32680-compat`, with no changes to `main`.
