# SM-S9360 KernelSU 32680 × GhostSam — source contract checkpoint

**Status: 12/12 static source contract gates passed; 5 runtime/device blockers remain. NOT FOR INSTALLATION.**

## Reproducible evidence

- [Source contract review, completed successfully: run #38290085836](https://github.com/ychlhk/GhostSam/actions/runs/38290085836).
- [Full text/JSON audit artifact (no kernel or daemon binaries)](https://github.com/ychlhk/GhostSam/actions/runs/38290085836/artifacts/11764499339).
- [Audit script](../scripts/ksu-32680-source-contract.py) and [CI workflow](../.github/workflows/ksu-32680-source-contract.yml).
- Official reference: `tiann/KernelSU` commit `0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d`, version 32680.
- Samsung reference: `snothin/KernelSU` commit `0fde5f940559d36c48c9516902b3a7ce944a80c5`, version fallback 32601.
- User-provided live phone: Samsung SM-S9360, Android 16, `6.6.98-android15-8-p5a696e2-abogkiS9360ZCSCCZG1-4k`, 4096-byte pages.
- Verified on-device `ksud` SHA-256 matches the packaged GhostSam `main` `ksud`: `9dcfda0240d859f41d70c404d145559c40c808b03800e78df527e43bee7f6fe0`. Phone reports `ksud pre-sync-20260929-67-g9263f621 (uapi: 2)`.
- See [existing 32601 embedded-module evidence](KSU_32601_EMBEDDED_BASELINE.md) and [target ABI audit](SM_S9360_ABI_VERDICT.md).

## Source comparison results

| Subject | Verified source-level result | Limitation |
|---|---|---|
| `userspace/ksuinit/src/lib.rs` | **Identical file blob SHA** (`1a62d4c2b18197d338451a4c809edd1308acc481`) in pinned Samsung 32601, official 32680, and experimentally merged source | Does not prove installed 32601 binary build provenance or new module compatibility |
| Loader operation | Resolves undefined ELF symbol references against `/proc/kallsyms`, calls `init_module`; on specifically detected `vermagic` mismatch, retries after adjusting its `.modinfo` `vermagic` | Version-string substitution is not a general ABI/CRC verification |
| `userspace/ksud/src/late_load.rs` | Merged flow preserves Samsung `stage_daemon_from` (line 44) → `ksuinit::load_module` (line 87) → `finish_install` (line 103), without a second `utils::install(None, None)` | Process lifetime, failover and SELinux filesystem semantics still need manual review |
| KMI selection | Merged flow retains `{kmi}_kernelsu.ko`, `KSUD_TREE=exynos` alternative and common loader call | Resource selection on the live device has not been independently traced |
| Kernel KDP and DEFEX | Required Samsung init order and teardown function references present | Link-time symbols, kernel credential structure, vendor-specific behavior unverified |
| New official init calls | `ksu_module_blacklist_init`, `ksu_shell_su_adb_only_init`, `ksu_feature_apply_forced` present | Source presence does not establish semantics |
| SELinux | Both `KSU_SELINUX_HIDE_USE_KPROBE` and `ksu_avc_has_perm_compat`, plus Samsung CFI annotation, present | Hook behavior/return paths/SELinux vendor policy not validated |
| UAPI | Samsung reference = **2**, official/merged = **5**; identical named IOCTL declarations and no textual struct differences found by the existing comparison | Feature negotiation, manager authorization and runtime interoperability not demonstrated |

## Five outstanding blockers

1. **UAPI and manager compatibility**: existing phone uses UAPI 2. Experimental kernel/userspace are UAPI 5. The fact that named IOCTL declarations match is insufficient for device protocol compatibility.
2. **Samsung vendor behavior**: independently audit KDP/DEFEX, SELinux kprobe and CFI behavior. Compilation with flags is not a vendor runtime test.
3. **Target kernel ABI**: exported symbol set/CRCs, kernel private symbol resolution and relevant data structures for `S9360ZCSCCZG1` are not verified. Both working 32601 embedded 6.6 and experimental 32680 reference modules report 6.6.127 `vermagic`, so that string is **not a sufficient standalone rejection or acceptance test** for the specialized loader.
4. **Recovery/test readiness**: no controlled deployment, known-good backup or validated recovery runbook is approved; production phone unchanged.
5. **Daemon lifecycle divergence**: official 32680 has `utils::daemonize(false)` at late-load entry; Samsung reference and merged experimental flow do not. Need an explicit review of process/wait/SELinux sequencing; **do not blindly insert this call**.

## Safe next engineering work

- Review feature-flag handling and manager version authorization against UAPI 5 using pinned static source/ABI declarations, without changing protocol implementation.
- Obtain exact Samsung kernel build symbol/CRC evidence and compare against the module metadata offline.
- Review lifecycle divergence and error unwinding with source-only control-flow diagrams or tests, without updating device loader code.

**Decision: no install, no flash, no module insertion, no daemon replacement, no change to the existing 32601 root environment.** Work confined to `ksu-32680-compat`; default `main` remains untouched.
