# KernelSU 32680 / Samsung fork: interface compatibility review

Status: **review only, NOT merged, NOT device-ready**.

## Evidence and pinned revisions

- Official: [tiann/KernelSU at 0c0fdb9](https://github.com/tiann/KernelSU/blob/0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d/uapi/supercall.h)
- GhostSam fork: [snothin/KernelSU at 0fde5f9](https://github.com/snothin/KernelSU/blob/0fde5f940559d36c48c9516902b3a7ce944a80c5/uapi/supercall.h)

## Confirmed interface differences

| Area | Official 32680 | Samsung fork | Implication |
|---|---|---|---|
| `KERNEL_SU_UAPI_VERSION` | 5 | 2, explicitly pinned in the fork's comment | **Blocking compatibility gap** until callers/structs are jointly reviewed |
| `KSU_GET_INFO_FLAG_BUNDLED` | Defined | Absent | Additional feature bit; inspect consumers and fallbacks |
| `late_load.rs` | `utils::install(None, None)` | `stage_daemon_from(...)` then `finish_install(None)` | Different install sequencing and preconditions |
| `late_load.rs` | Default module asset selection | Additional `KSUD_TREE=exynos` asset handling | Device-specific selection behavior must be preserved or independently validated |
| `kernel/core/init.c` | Upstream initialization flow | Samsung KDP and DEFEX initialization/error paths | Security-sensitive vendor dependencies requiring independent review |

## Required checks before any merge candidate

1. Generate an exhaustive change inventory of UAPI definitions, command IDs, structure layout, and binary compatibility; both the userspace and kernel side must agree.
2. Establish whether an updated userspace component can talk to a previous kernel UAPI without breaking older installations; failing safely is preferable to silently accepting mismatched requests.
3. Review daemon staging, file replacement, SELinux context handling, and cleanup ordering with controlled offline tests.
4. Review initialization and teardown ordering separately, including all failure paths and Samsung-specific required symbols.
5. Check all five original conflicts and the overlap in `kernel/Kbuild`. A three-way merge without textual conflicts is NOT proof of correct semantics.
6. For SM-S9360, independently verify vendor module ABI and symbol-version requirements with the exact running kernel before discussing installation.

## Constraints

No code has been merged here. This document does not implement or modify credential transitions, security bypass hooks, exploit chains, or module loaders. The existing phone kernel, LKM, and ksud are unchanged. Neither reference build is certified for this device.
