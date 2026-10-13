# SM-S9360 S9360ZCSCCZG1 on-device BTF — verified type-layout snapshot

## Provenance
- Device firmware fingerprint (provided by owner): `samsung/pa2qzcx/pa2q:16/BP4A.251205.006/S9360ZCSCCZG1_CHCCCZG1:user/release-keys`
- Kernel release: `6.6.98-android15-8-p5a696e2-abogkiS9360ZCSCCZG1-4k`.
- Source: owner-uploaded exact copy of `/sys/kernel/btf/vmlinux`.
- Raw BTF length: **6,387,446 bytes**.
- SHA-256: `d66603646376671fc567fd73b67dc877d0c2242ec05472b6b914ca4a645fddca` (matches owner's export).
- BTF header: magic `0xeb9f`, version 1, header length 24; type bytes 3,791,004; string bytes 2,596,418.
- Parsed **146,854 BTF types**, with the type section terminating at the declared boundary.

## Observed primary structure layouts (size bytes)
| Type | Size |
| --- | ---: |
| `task_struct` | 4800 |
| `cred` | 184 |
| `mm_struct` | 1216 |
| `file` | 264 |
| `files_struct` | 704 |
| `linux_binprm` | 416 |
| `module` | 1536 |

### Representative BTF field offsets (bytes, measured; not proposed patch constants)
- `task_struct.mm`: 1440; `real_cred`: 2072; `cred`: 2080; `security`: 2984.
- `cred.uid`: 8; `euid`: 24; `security`: 128.
- `module.state`: 0; `name`: 24; `init`: 392; `mem`: 448; `kallsyms`: 1184.

These are reported for forensic comparison only. Do not hardcode or apply offsets to a loader, privileged-memory tool, or root transition.

## Interpretation and release gate
- The target has `CONFIG_MODULES=y`, `CONFIG_MODVERSIONS=y`, `CONFIG_CFI_CLANG=y`, `CONFIG_DEBUG_INFO_BTF=y`, per owner's read-only configuration check.
- `/proc/kallsyms` returned names but redacted address values; BTF does not restore the missing symbol addresses or provide matching `Module.symvers` CRCs.
- The live KernelSU module reports version **32601**, UAPI **2**, LKM mode and late-load. The experimental target is **32680**, UAPI **5**.
- **No full layout comparison with the experimental 32680 build's BTF, target exported CRC parity, KDP/DEFEX runtime verification, or loader compatibility validation was completed here.**
- **Verdict: type metadata extracted successfully; Samsung 32680 LKM/ksud installation remains BLOCKED.** This document is an evidence snapshot, not a working port or an install guide.

## Experimental 32680 LKM CI result (2026-10-13)

- [GitHub Actions run #38334319543](https://github.com/ychlhk/GhostSam/actions/runs/38334319543) **success** for a generic GKI compile and ABI metadata collection.
- [ABI report artifact #11783449831](https://github.com/ychlhk/GhostSam/actions/runs/38334319543/artifacts/11783449831) was downloaded and inspected.
- The final `kernelsu.ko` ELF contains `__versions`, but **no retained `.BTF` or `.debug_info` type section** according to `readelf -S -W`.
- The build emitted `BTF [M]` during module generation, but that alone does not establish that type metadata survived in the final module ELF.
- Consequently **no complete reference-to-device field-layout parity test has run**; any claim that the target is ABI-compatible would be premature.
- Follow-up: prepare a debug-information-enabled, compile-only module build and extract text-based type metadata; obtain exact-firmware export CRCs independently. Do not publish or install module binaries solely from this audit.

**Release remains BLOCKED.**

## DWARF/BTF-enabled experimental module build (2026-10-13)

- [GitHub Actions run #38335088957](https://github.com/ychlhk/GhostSam/actions/runs/38335088957) completed **successfully** with compile-only `KCFLAGS=-g`.
- [Text ABI metadata artifact #11784229093](https://github.com/ychlhk/GhostSam/actions/runs/38335088957/artifacts/11784229093) was downloaded and inspected.
- Actual `readelf -S -W` report confirms `.debug_info`, `.debug_abbrev`, `.debug_str`, and `.BTF` in the experimental `kernelsu.ko`.
- Report also lists `__versions` with **zero section size**. This must not be interpreted as demonstrated module symbol CRC parity.
- DWARF statistics show 664 functions and 3034 unique source variables, establishing the presence of useful compiler-emitted debugging data, **not** Samsung target compatibility.
- The artifact contains text reports, **not the module ELF or extracted per-type layouts**. Therefore an actual field-by-field comparison against the uploaded target BTF is still outstanding.
- Next offline gate: produce structured, text-only DWARF/BTF type-layout metadata from the experimental module and compare relevant types to the independently supplied SM-S9360 BTF; separately acquire firmware-matching module export CRC evidence.

**Installation verdict: BLOCKED.** Existing 32601 device Root and production `main` remain unchanged.
