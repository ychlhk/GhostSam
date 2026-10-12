# GhostSam SM-S9360 — verified embedded 32601 module baseline

This is a **read-only binary inventory**, not a replacement-module release or an install guide.

## Input provenance

- Phone reported `/data/adb/ksud --version`: `pre-sync-20260929-67-g9263f621 (uapi: 2)`.
- Phone and GhostSam `main` packaged `app/app/src/main/assets/payloads/ksud/ksud` share identical SHA-256: `9dcfda0240d859f41d70c404d145559c40c808b03800e78df527e43bee7f6fe0`.
- Phone: `SM-S9360`, running `6.6.98-android15-8-p5a696e2-abogkiS9360ZCSCCZG1-4k`, `getconf PAGESIZE=4096`.
- `/proc/modules` reports `kernelsu ... Live ... (O)`, and root `uid=0` / `u:r:ksu:s0`; this verifies a working LKM but not its on-device byte-for-byte identity.
- [Read-only inventory run #38289275625](https://github.com/ychlhk/GhostSam/actions/runs/38289275625), [text-only artifact](https://github.com/ychlhk/GhostSam/actions/runs/38289275625/artifacts/11763769827).

## Measured embedded module metadata

The SHA-pinned `ksud` contains 8 identifiable **compressed** ARM64 ELF ET_REL resources, each with `.modinfo` naming `kernelsu` and a symbol-version section. Static DEFLATE analysis recovered these `vermagic` strings:

| Kernel ABI family | Embedded module vermagic (release part) |
|---|---|
| Android 12 / 5.10 | `5.10.236` |
| Android 13 / 5.10 | `5.10.245` |
| Android 13 / 5.15 | `5.15.202-android13-5.15.202_r00-dirty` |
| Android 14 / 5.15 | `5.15.202-dirty` |
| Android 14 / 6.1 | `6.1.166-dirty` |
| **Android 15 / 6.6** | **`6.6.127-4k-g46a034eca005-dirty`** |
| Android 16 / 6.12 | `6.12.38-android16-5-p8aa82f3-abogkiS947BXXS4AZHA-4k` |
| Android 17 / 6.18 | `6.18.32-4k-g47cc22554442-dirty` |

The table associates families by filenames observed in the same binary and kernel release families; static analysis did **not** cryptographically map each filename to its decompressed byte range. The unique 6.6-family candidate is strong evidence for `android15-6.6_kernelsu.ko`, not a proof of precisely which byte sequence the phone has loaded.

The original Samsung fork's `userspace/ksud/src/late_load.rs` chooses `{kmi}_kernelsu.ko` (or `{kmi}-exynos_kernelsu.ko` with `KSUD_TREE=exynos`) and calls `ksuinit::load_module(&ko_data, ...)`, described there as manual relocation. `userspace/ksud/Cargo.toml` enables `rust-embed` `compression`, explaining why raw ELF scanning did not find the modules.

## Impact on the experimental 32680 port

**Important correction:** the current working **32601 family's embedded 6.6 LKM** and the experimental **32680 GKI reference LKM** both report:

```text
6.6.127-4k-g46a034eca005-dirty SMP preempt mod_unload modversions aarch64
```

Therefore the fact that the SM-S9360 phone runs `6.6.98-...` does **not**, by itself, prove that a newer 6.6.127-built LKM is impossible to use with the specialized loader. It does prevent claiming ordinary stock `insmod` version-string compatibility. The working 32601 is empirical evidence that custom loading paths may overcome the version-string mismatch under that older module's exact ABI and code.

**No inference of 32680 runtime safety follows:** UAPI 2 (working baseline) vs UAPI 5 (official 32680), module exported symbols/CRC, changes in KernelSU hooks, Samsung KDP/DEFEX, manager authorization, SELinux, and `ksuinit` relocation must all be independently audited before attempting a controlled device test. Do not force-load or flash any experimental LKM; leave phone's working 32601 and `ksud` intact.

## Source/reproduction

- Read-only script: [`scripts/audit-bundled-ksud.py`](https://github.com/ychlhk/GhostSam/blob/ksu-32680-compat/scripts/audit-bundled-ksud.py)
- Text-only workflow: [`ksu-32601-embedded-audit.yml`](https://github.com/ychlhk/GhostSam/blob/ksu-32680-compat/.github/workflows/ksu-32601-embedded-audit.yml)

The SHA-pinned scanner does not execute or output decompressed binaries.
