# SM-S9360 task_struct drift: direct-reference scan result

Run: https://github.com/ychlhk/GhostSam/actions/runs/38336444430
Artifact: s9360-experimental-lkm-abi-metadata-NO-BINARY (ID 11784932750), inspected `TASK_STRUCT_SOURCE_REFERENCES.txt`.

## Observations
The merged experimental KernelSU kernel source was scanned (C/H files) for `android_vendor_data2`, `kretprobe_instances` and `android_kabi_reserved2` through `android_kabi_reserved8`. No direct text matches were found in the scan.

The scan did find general `task_struct` references in `policy/allowlist.c`, `policy/app_profile.c`, `hook/tp_marker.c`, `feature/shell_su_adb_only.c`, `feature/selinux_hide.c`, `infra/su_mount_ns.c`, `supercall/dispatch.c`, `compat/samsung_defex.c`, and `compat/samsung_kdp.c`.

## Limits
- Absence of named direct field references does **not** prove safety. Macro expansions, nested type dependencies, task-related helper calls, CFI, Samsung vendor hooks and indirect member access were not resolved.
- This source scan also does not test module symbol CRC matching, target compiler configuration, Samsung security runtime, the late-loader, or UAPI 5 interoperability.
- Device-matching `Module.symvers` / equivalent export CRC evidence remains missing.

## Next audit gate
Perform targeted source review of task-related accesses in `samsung_kdp.c`, `samsung_defex.c`, `selinux_hide.c` and the hook/dispatch paths; identify each access and whether it depends on a compiler-calculated offset, external vendor function, or an exported kernel API. Independently validate exact-firmware ABI symbols and CRCs before any installation.

**Release remains BLOCKED.** Leave current SM-S9360 32601 LKM/UAPI2 unchanged.
