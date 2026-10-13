# SM-S9360 experimental 32680 Samsung symbol-dependency audit — 2026-10-13

## Evidence
- [Successful Actions run #38341704581](https://github.com/ychlhk/GhostSam/actions/runs/38341704581)
- Downloaded actual metadata artifact ID `11787386385` and inspected `SAMSUNG_SYMBOL_DEPENDENCIES.txt`.
- Environment: generic Android 15/Linux 6.6 DDK; **NOT** exact Samsung `S9360ZCSCCZG1` firmware.

## Findings

1. Module unresolved symbol list includes many generic kernel APIs and internal functions, including `commit_creds`, `prepare_creds`, `register_kprobe`, `register_kretprobe`, `kallsyms_lookup_name`, `selinux_state`, `avc_has_perm`, `security_secctx_to_secid`, and others. These `U` entries mean the linker relies on external resolution; they are not individually proof of loader failure or of exportability in Samsung firmware.
2. `readelf -SW` shows `__versions` with zero size, so this artifact **does not establish target CRC matches** for `CONFIG_MODVERSIONS=y`.
3. The Samsung KDP compatibility source dynamically resolves `kdp_assign_pgd`, `kdp_usecount_sub_and_test`, and `kdp_usecount_dec_and_test` via `ksu_resolve_symbol_for_functable_hook`, and uses a workqueue-based credential path.
4. Samsung DEFEX source resolves `get_task_creds` and `set_task_creds` dynamically and registers a kprobe for `task_defex_enforce`.
5. Neither successful compilation nor source-level symbol references demonstrate that these functions exist, are usable in this exact firmware, have compatible prototypes, or behave correctly under its security and CFI settings.

## Non-installable disposition

**BLOCKED:** obtain independently verified exact-device export/CRC and vendor API evidence; audit all dependent call sites, Samsung runtime invariants and UAPI 5. Do not use or distribute this generic test module as an installation candidate. Do not alter the phone's existing 32601 LKM/ksud.
