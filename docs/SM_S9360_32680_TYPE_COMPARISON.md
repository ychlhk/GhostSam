# SM-S9360 exact-device BTF vs generic-GKI experimental 32680 DWARF

Evidence: target BTF SHA256 `d66603646376671fc567fd73b67dc877d0c2242ec05472b6b914ca4a645fddca`; [run #38335921141](https://github.com/ychlhk/GhostSam/actions/runs/38335921141) artifact `TYPE_LAYOUTS.txt` for generic-GKI experimental module.

The seven inspected type **total sizes agree**: task_struct 4800, cred 184, mm_struct 1216, file 264, files_struct 704, linux_binprm 416, module 1536 bytes.

## Detected field-offset differences

`task_struct` has a sequence of offsets differing by 8 bytes (device BTF vs generic DWARF):
- `kretprobe_instances`: 3576 vs 3568
- `android_kabi_reserved2`: 3592 vs 3584
- `android_kabi_reserved3`: 3600 vs 3592
- `android_kabi_reserved4`: 3608 vs 3592
- `android_kabi_reserved5`: 3616 vs 3608
- `android_kabi_reserved6`: 3624 vs 3616
- `android_kabi_reserved7`: 3632 vs 3624
- `android_kabi_reserved8`: 3640 vs 3632

Other clearly parsed fields in the examined structures had no detected differences, but text extraction left some anonymous, bitfield or nested members unresolved. In particular `task_struct` returned 191 exact field matches and 19 text-parser-unresolved fields; `cred` 26 matches, `file` 22 matches. **This is a partial comparison**, not a field-complete ABI certification.

Crucially, identical total sizes are *not* proof of ABI identity. The structure offset discrepancies call for explanation against exact target kernel sources/ABI, and target symbol CRCs are still unavailable. This document does not authorize loading or installing the experimental LKM or replacing ksud.

**Release decision: BLOCKED.** Keep phone's working 32601 LKM / UAPI 2 environment unchanged.
