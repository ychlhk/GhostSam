# GhostSam × KernelSU v3.3.1 — upstream alignment and release gate

**Scope:** isolated GitHub audit and build checks only. **Status: NOT a 3.3.1-compatible Samsung release. Do not install the resulting reference binaries.**

## Verified upstream identity (2026-10-13)

- Official release: [tiann/KernelSU v3.3.1](https://github.com/tiann/KernelSU/releases/tag/v3.3.1), published 2026-10-12 UTC.
- Official Git tag `v3.3.1` resolves to `0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d`.
- Official Manager release: `KernelSU_v3.3.1_32680-release.apk` (version code **32680**).
- Official `ksud-aarch64-linux-android` SHA-256 (from release asset metadata):
  `049491e2b4cc0a6c913d3920cb90b8c94c9e8ca96c0ee92818293304973bfb1b`.
- Existing [`ksu-32680-compat`](https://github.com/ychlhk/GhostSam/tree/ksu-32680-compat) reports and compile checks **already pin exactly the v3.3.1 source commit**. No new upstream source merge is required merely to adopt the release tag.
- **Important:** the upstream v3.3.1 tag does **not** mean that the Samsung-specific downstream code, bundled LKM, or embedded `ksud` in GhostSam has been upgraded.

## This branch

[`ksu-3.3.1-compat`](https://github.com/ychlhk/GhostSam/tree/ksu-3.3.1-compat) was branched from `ksu-32680-compat`, preserving all previous offline Samsung-source, UAPI and ABI audits. Nothing was merged into `main`.

New [CI workflow](../.github/workflows/ksu-v3.3.1-provenance.yml):

1. Check official Git tag resolves to the pinned source commit.
2. Independently inspect GitHub release metadata and SHA-256-check the reference Android/ARM64 `ksud`.
3. Inspect the reference ELF architecture and the original GhostSam prebuilt `ksud` and `ksud-next` hashes **without executing them**.
4. Run Gradle payload verification and compile the unchanged GhostSam debug manager in a cloud CI runner.
5. Upload **text-only** provenance reports. The workflow does **not** upload an APK, an LKM or a replacement daemon, does **not** change the packaged binaries, and has no device-install step.

## What is NOT established

- A new Samsung KernelSU 3.3.1 LKM and matching downstream daemon have **not** been implemented or validated for **SM-S9360**, Samsung firmware `S9360ZCSCCZG1`.
- The existing bundled GhostSam `ksud` is an older Samsung-fork build. Replacing it with the official generic `ksud` asset would discard or alter device-specific assumptions and **is not approved** solely on the basis of a matching version code.
- Existing reference audits documented **UAPI 2 versus UAPI 5**, 5 original source-merge conflicts, Samsung KDP/DEFEX behavior, manager authorization, generic GKI versus phone ABI/CRC uncertainty, and differences in late-load daemon lifecycle. These remain subject to proper source review and device-specific validation.
- The user's statement that the kernel is now at 3.3.1 is **not** proof of which LKM is currently loaded, which `ksud` is running, or of its UAPI; collect these separately via read-only diagnostics before any proposed live integration.
- A passing APK build tests the pre-existing app and its unchanged packaged payloads, **not** a functional 3.3.1 upgrade.

## Release decision

**BLOCKED for package release and on-device installation.** Leave the working phone and `main` unchanged until exact version/UAPI, signed-manager identity, Samsung ABI/exported symbol compatibility, and KDP/DEFEX + SELinux + lifecycle behavior are independently confirmed. Do not fake module versions, force-install a mismatched module, bypass signing checks, or replace the phone's working daemon.

Related evidence: [existing port status](KERNELSU_32680_PORT_STATUS.md), [Manager/UAPI audit](KSU_32680_MANAGER_UAPI_REVIEW.md), [device ABI verdict](SM_S9360_ABI_VERDICT.md), and [source contract](KSU_32680_SOURCE_CONTRACT_CHECKPOINT.md).
