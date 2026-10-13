# SM-S9360 KernelSU 32680: KDP/DEFEX symbol dependency findings

## Provenance
- Successful compile-only run: https://github.com/ychlhk/GhostSam/actions/runs/38341704581
- Reviewed artifact: `s9360-experimental-lkm-abi-metadata-NO-BINARY`, ID `11787386385`, file `SAMSUNG_SYMBOL_DEPENDENCIES.txt`.
- Device under review: SM-S9360, kernel `6.6.98-android15-8-p5a696e2-abogkiS9360ZCSCCZG1-4k`.

## Observations from actual artifact
- Experimental module compiled with generic Android 15 / Linux 6.6 DDK.
- Its `__versions` section is present but its size is **0x000000**; this is **not** evidence of target module symbol CRC parity.
- The undefined ELF symbols list includes ordinary imported kernel functions, such as `commit_creds`, but Samsung-private interfaces below are used through **runtime string-based resolution** and therefore must be audited separately from `nm -u`.
- In `compat/samsung_kdp.c`, named resolution and casts are used for `kdp_assign_pgd`, `kdp_usecount_sub_and_test`, and `kdp_usecount_dec_and_test`; the source also uses a `prepare_ro_creds_fn` function pointer.
- In `compat/samsung_defex.c`, named runtime resolution is used for `get_task_creds` and `set_task_creds`; a kprobe is requested by name for `task_defex_enforce`.
- Merely locating function *names* in `/proc/kallsyms` (even if possible) would not establish prototype, calling convention, compatibility, or runtime safety. Do not work around redacted addresses.

## Mandatory remaining gates
1. Establish exact target-firmware symbol versions/exports where applicable (firmware-matching `Module.symvers` or equivalent vendor build evidence).
2. Review runtime-resolved Samsung private function prototypes and ABI against exact firmware sources; these won't necessarily appear in `__versions`.
3. Review DEFEX kprobe semantics and KDP lifecycle, including error unwinding, in a controlled non-device test design.
4. Validate UAPI 5 userspace/kernel contract and late-load integration independently.

**Decision: BLOCKED / NOT INSTALLABLE.** This report does not authorize replacing the working device's KernelSU 32601 or installing/loading experimental 32680.
