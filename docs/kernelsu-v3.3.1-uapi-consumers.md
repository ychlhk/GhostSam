# KernelSU UAPI consumer map — incremental source audit

Date: 2026-10-13. Scope: immutable upstream tag v3.3.1 at `0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d` and Samsung fork `kdp-s26` at `0fde5f940559d36c48c9516902b3a7ce944a80c5`.

## Verified call graph, upstream v3.3.1

### Services event (UAPI 5)
- Header defines `EVENT_SERVICES = 4`: `uapi/supercall.h`.
- Userspace `userspace/ksud/src/ksucalls.rs` function `report_services()` sends `KSU_IOCTL_REPORT_EVENT` with `EVENT_SERVICES`, and interprets ioctl result `== 1` as true.
- Kernel `kernel/supercall/dispatch.c` handles `EVENT_SERVICES` in the event dispatcher, including the already-started case.
- **Risk:** the userspace/kernel pair must agree on event number and returned status semantics. This is not a mere version label.

### Bundled flag (UAPI 4)
- Header defines `KSU_GET_INFO_FLAG_BUNDLED = (1U << 4)`.
- Kernel `kernel/supercall/dispatch.c` conditionally sets that flag in GET_INFO.
- Manager `manager/app/src/main/cpp/ksu.cc` checks it alongside `KSU_GET_INFO_FLAG_LKM` in `is_lkm_bundled()`.
- Userspace `userspace/ksud/src/cli.rs` reports the flag.
- **Risk:** capability reporting changes between the branches; a missing flag may affect UI/feature classification, but does not by itself establish a crash.

### Version provenance
- Kernel `kernel/supercall/dispatch.c` populates `cmd.uapi_version` from `KERNEL_SU_UAPI_VERSION`.
- Userspace `userspace/ksud/src/defs.rs` incorporates the compiled UAPI constant into the displayed `FULL_VERSION`.
- Manager `manager/app/src/main/cpp/ksu.cc` exposes the compiled UAPI version.
- **Risk:** output from `ksud --version` reflects its compiled value; it alone does **not** identify the loaded kernel module's version.

## Verified Samsung fork observations
- Fork `uapi/supercall.h` explicitly fixes `KERNEL_SU_UAPI_VERSION = 2`.
- Fork `userspace/ksud/src/late_load.rs` stages the daemon before module load and uses `ksuinit::load_module`.
- Both the fork and official v3.3.1 have `ksuinit::has_kernelsu()` and `ksuinit::load_module()` calls. These similar function names do not prove compatible behavior.
- Fork's inspected header does not define `EVENT_SERVICES` or `KSU_GET_INFO_FLAG_BUNDLED`.
- GitHub code search for the fork returned no indexed matches for these terms; this **is not** proof they are absent throughout all source files.

## Limits and follow-ups
- This is a *partial* consumer map. Not all UAPI 3 scoped-session call sites have been verified.
- No executable payloads, kernels, `ksud`, or APK were changed.
- The previous static checker covers declaration differences but **does not** verify consumer semantics. Its failed gate must be interpreted only as "version mismatch," not as definitive runtime incompatibility.
- Release decision remains **BLOCKED** pending full consumers audit, independent compilation and target ABI validation.

Official source references:
- https://github.com/tiann/KernelSU/blob/v3.3.1/uapi/supercall.h
- https://github.com/tiann/KernelSU/blob/v3.3.1/userspace/ksud/src/ksucalls.rs
- https://github.com/tiann/KernelSU/blob/v3.3.1/kernel/supercall/dispatch.c
- https://github.com/tiann/KernelSU/blob/v3.3.1/manager/app/src/main/cpp/ksu.cc
