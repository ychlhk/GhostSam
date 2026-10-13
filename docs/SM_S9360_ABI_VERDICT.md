# SM-S9360 KernelSU 32680 — ABI evidence and release gate

**Verdict: BLOCKED FOR INSTALLATION.** This document records facts from an experimental **generic GKI** reference build, not a Samsung-ready LKM.

## Verified evidence

- Audit run: [#38287004026](https://github.com/ychlhk/GhostSam/actions/runs/38287004026), success (audit execution, **not device compatibility**).
- Evidence artifact: [s9360-experimental-lkm-abi-metadata-NO-BINARY](https://github.com/ychlhk/GhostSam/actions/runs/38287004026/artifacts/11763557242).
- Experimental source: official tiann/KernelSU at `0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d` merged for compile-only comparison with snothin/KernelSU at `0fde5f940559d36c48c9516902b3a7ce944a80c5`.
- Builder: `ghcr.io/ylarod/ddk-min:android15-6.6-20260828`.
- Generated module ELF: `ELF64`, relocatable, `AArch64`.
- Generated `modinfo vermagic`: `6.6.127-4k-g46a034eca005-dirty SMP preempt mod_unload modversions aarch64`.
- Target model: `SM-S9360`.
- Previously reported target `uname -r`: `6.6.98-android15-8-p5a696e2-abogkiS9360ZCSCCZG1-4k`.
- **Mismatch:** build module `6.6.127-4k` vs target `6.6.98-...-4k`; this is not a matching Samsung target build.
- `__versions` section present. No `Module.symvers` or exported CRC evidence matching the **exact** phone firmware has been checked.
- `llvm-nm -u` (undefined external symbol references) yielded **228 unique symbols**. These are references awaiting resolution, **not proof that 228 exports are missing**.
- `modinfo depends` is empty; this does not prove Samsung KDP/DEFEX symbol availability, particularly for dynamically resolved names.

## Confirmed on-device identification (terminal output; 2026-10-13)

Read-only terminal commands completed with exit code 0:

| Field | Confirmed value |
|---|---|
| `ro.product.model` | `SM-S9360` |
| `uname -r` | `6.6.98-android15-8-p5a696e2-abogkiS9360ZCSCCZG1-4k` |
| `ro.build.display.id` | `BP4A.251205.006.S9360ZCSCCZG1` |
| `ro.boot.bootloader` | `S9360ZCSCCZG1` |
| `getconf PAGESIZE` | `4096` |

External firmware catalogs list `S9360ZCSCCZG1` under **SM-S9360 / CHC (China)**, Android 16:
- https://samfw.com/firmware/SM-S9360/CHC
- https://www.sammobile.com/samsung/galaxy-s25-plus/firmware/

**Source availability:** Samsung's official release site offers mobile source downloads, but a publicly indexed, exact-version `S9360ZCSCCZG1` kernel source package and its matching `Module.symvers` were **not independently located or verified** as of this review. A full consumer firmware ZIP is **not** a kernel source/build tree or an ABI validation by itself.
- Official release center: https://opensource.samsung.com/uploadList?classification1=mobile_phone&menuItem=mobile
- Official source-code inquiry: https://opensource.samsung.com/requestInquiry

**Version mismatch is not a standalone rejection proof:** the working 32601 ksud contains an Android15-6.6 LKM with the **same** generic GKI `6.6.127-4k-g46a034eca005-dirty` vermagic as our experimental 32680. The GhostSam late-load path uses custom in-memory relocation, not necessarily the stock kernel module loader. This does NOT prove 32680 compatibility: Samsung symbol/CRC, loader semantics, UAPI, KDP/DEFEX, and SELinux remain unresolved. See [32601 embedded baseline](KSU_32601_EMBEDDED_BASELINE.md).

## Device-specific verification still required

1. Confirm exact phone `uname -r`, fingerprint, AP/baseband/firmware and page size without altering the device.
2. Obtain the matching Samsung **model and firmware** source/build context or independently verified kernel KMI and target `Module.symvers` / CRCs; check full ABI and relevant proprietary symbol availability.
3. Compare the target build's exported module symbol CRCs with this experiment; generic GKI results cannot substitute for the Samsung checks.
4. Audit the merged `KDP` / `DEFEX` code and the kernel/daemon UAPI and boot/late-load lifecycle. A green CI compilation is **not** runtime validation.
5. Only after all above items are evidenced should a controlled lab-only runtime test even be considered, with a validated recovery procedure.

## Safe read-only device facts

The following captures low-risk identification data. It does **not** load modules, switch SELinux modes, dump kernel memory or change root installations:

```sh
printf 'MODEL='; getprop ro.product.model
printf 'KERNEL='; uname -r
printf 'FINGERPRINT='; getprop ro.build.fingerprint
printf 'BUILD_ID='; getprop ro.build.display.id
printf 'BOOTLOADER='; getprop ro.boot.bootloader
printf 'ANDROID='; getprop ro.build.version.release
printf 'SECURITY_PATCH='; getprop ro.build.version.security_patch
printf 'PAGESIZE='; getconf PAGESIZE
```

Do not publish identifiers beyond these build-related fields without reviewing for private data.

## Release decision

**Not installable / not flashable** as tested. The existing Samsung KernelSU LKM and `ksud` remain untouched. Never use `insmod --force`, modify a version string to masquerade as a match, or replace the phone's working daemon to paper over this mismatch.

## Confirmed exact production build metadata (read-only, 2026-10-13)

- Fingerprint: `samsung/pa2qzcx/pa2q:16/BP4A.251205.006/S9360ZCSCCZG1_CHCCCZG1:user/release-keys`.
- Android security patch: `2026-07-05`.
- Bootloader: `S9360ZCSCCZG1`.
- Kernel release: `6.6.98-android15-8-p5a696e2-abogkiS9360ZCSCCZG1-4k`.
- Compiler: Android Clang 18.0.0, toolchain build `11368308`, LLVM revision `477610d4d0d988e69dbc3fae4fe86bff3f07f2b5`; kernel built Wed Jul 8 09:14:14 UTC 2026.
- Live module reports `version: 32601`, `uapi_version: 2`, `lkm: true`, `runtime_mode: late-load` via `ksud debug info`. The installed userspace `ksud` reports `uapi: 2`; Manager package reports `versionCode=32680`.
- Live `/proc/modules`: `kernelsu 180224 0 - Live ... (O)`.

**Interpretation:** this confirms the actual on-device LKM is KernelSU 32601, not the experimental 32680. The 32680 Manager package is not evidence of a 32680 LKM. The exact target `Module.symvers` and exported symbol CRCs have not been obtained. The generic GKI reference ELF is not approved for the device.

**Source lookup (2026-10-13):** Samsung provides an official mobile source Release Center: https://opensource.samsung.com/uploadList?classification1=mobile_phone&menuItem=mobile . The public search results checked did not independently verify a matching `S9360ZCSCCZG1` source archive. This absence of a verified match is not proof the archive does not exist. Request the exact version from Samsung if unavailable in the Release Center. Linux Kbuild documentation describes `Module.symvers` and per-symbol CRC checks: https://docs.kernel.org/kbuild/modules.html .
