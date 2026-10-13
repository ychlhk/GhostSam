# KernelSU 32601 Samsung → 32680: Manager & UAPI compatibility audit

**Status: 10/10 checked source invariants pass. Device/runtime compatibility remains UNVERIFIED. Never install on production SM-S9360 based on this report.**

## Source evidence

- [Read-only GitHub Actions run #38326243227](https://github.com/ychlhk/GhostSam/actions/runs/38326243227) — completed successfully.
- [Machine-readable JSON and Markdown audit artifact](https://github.com/ychlhk/GhostSam/actions/runs/38326243227/artifacts/11780723174).
- [Audit script](../scripts/ksu-manager-uapi-contract.py) and [workflow](../.github/workflows/ksu-manager-uapi-contract.yml).
- Official KernelSU **32680** commit: `tiann/KernelSU@0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d`.
- Samsung reference **32601** commit: `snothin/KernelSU@0fde5f940559d36c48c9516902b3a7ce944a80c5`.
- Verified phone baseline: `SM-S9360`, `6.6.98-android15-8-p5a696e2-abogkiS9360ZCSCCZG1-4k`, `ksud pre-sync-20260929-67-g9263f621 (uapi: 2)`.

## Confirmed phone Manager (read-only terminal, 2026-10-13)

Android package manager confirms installed `me.weishu.kernelsu`, `versionCode=32680`, `versionName=v3.3.0-79-g0c0fdb96`. Previous read-only probes reported working LKM `32601-2` and `ksud pre-sync-20260929-67-g9263f621 (uapi: 2)`.

Official pinned 32680 Manager source expects UAPI 5, so a kernel-update or UAPI-mismatch warning is expected with the older running kernel. This is NOT evidence that the installed APK signature matches build defaults. Actual signer digest remains to be verified. A `dumpsys package | grep -m 2` "Broken pipe" is due to grep closing the pipe early, not a Root failure.

## Measured differences

| Contract | Samsung reference | Official 32680 | Offline conclusion |
|---|---|---|---|
| `KERNEL_SU_UAPI_VERSION` | 2 | 5 | Version negotiation differs |
| UAPI struct declarations | Baseline | Same fields in audited structs | **0 textual declaration differences** |
| Named IOCTL declarations | Baseline | Same | **0 textual command differences** |
| Kernel IOCTL dispatch permission entries | 24 | 24 | No named permission-map differences detected by audited parser |
| Source-level default Manager primary signing values | Baseline | Same | Equal in pinned build defaults; not an installed APK certificate check |
| Alternative Manager signature option | Conditionally supported | Not present in verified official signature check | Extra Samsung option may matter only if the installed Manager actually uses it |
| `KSU_GET_INFO_FLAG_BUNDLED` | Absent | Present | Status feature flag, not evidence of root authorization |
| UAPI fallback in Manager native `get_info()` | New info / legacy fallback | New info / legacy fallback | Both report kernel and manager UAPI |
| Manager frontend | `checkUAPIMismatch()` / `requireNewKernel()` | `isFullFeatured()` requires `isManager`, same UAPI and root availability | Manager feature-completeness is gated on equal UAPI versions |

The audit's **10/10 static checks** verify source-level presence, equality and selected control paths only. No APK signature or runtime ioctl traffic was tested.

## Key implications

1. The user's currently running **UAPI 2** kernel/ksud must not be treated as a UAPI 5 kernel solely because a 32680 Manager is installed. A newer Manager can read version information but disable or warn about feature completeness.
2. Because the audited struct fields, named command declarations and named permission map agree, **no direct modification to ioctl IDs or ABI structs is currently justified by this evidence**.
3. The stock primary signing defaults match. Therefore an **automatic blanket claim of a Manager signing incompatibility would be inaccurate**. A Samsung-specific secondary certificate option remains a source difference. Without the installed APK's actual certificate identity and exact compiled Kbuild flags, no authorization compatibility conclusion follows.
4. This report does **not** validate kernel KDP/DEFEX, credential handling, SELinux, module ABI/CRC, custom loader outcomes, or manager recognition on the SM-S9360 target.
5. Working 32601 and experimental 32680 embedded 6.6 modules both report a generic `6.6.127` vermagic; custom loader changes to vermagic do not validate ABI or new module safety. See [baseline](KSU_32601_EMBEDDED_BASELINE.md) and [source contract](KSU_32680_SOURCE_CONTRACT_CHECKPOINT.md).

## Release gate / next steps

- Keep source review restricted to `ksu-32680-compat`, with production `main` and the phone unchanged.
- Read-only verify the actually installed Manager's package name, claimed version, and signing certificate SHA-256 using a trustworthy package API or an offline APK signature inspector **without modifying signing checks**. Do not assume the APK uses the source defaults.
- Assess feature flag semantics, manager-appid attribution, and error signaling across UAPI 2 vs 5 without attempting authorization bypass.
- Validate Samsung vendor symbols/CRCs and independently review KDP/DEFEX and late-load lifecycle before considering any device runtime experiment.

**Outcome: PASS SOURCE CONTRACT / BLOCK DEVICE RELEASE.** No generated LKM or `ksud` is safe for installation based only on this audit.
