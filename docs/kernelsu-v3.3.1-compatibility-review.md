# KernelSU v3.3.1 upgrade: static compatibility review

Status: REVIEW ONLY — **no executable payloads updated or verified**.

Date: 2026-10-13

## Fixed upstream target

- Source: https://github.com/tiann/KernelSU/releases/tag/v3.3.1
- Release: v3.3.1 (2026-10-12)
- Tag commit (short): `0c0fdb9`
- Do **not** equate Manager build number 32680 with the LKM or ksud version.

## Current GhostSam architecture (verified from repository)

- `app/app/src/main/assets/payloads/ksud/ksud` is a prebuilt binary originating from `snothin/KernelSU`, not automatically compiled from the upstream release.
- `app/app/src/main/assets/payloads/dirtyfrag/dfr_lkm-android15-6.6.ko` is KMI-selected, prebuilt kernel code.
- `app/app/build.gradle.kts` defines `verifyPayloads`: file presence, nonzero length, and ELF magic checks on selected executables. It does not authenticate versions, module provenance, or device-specific compatibility.
- App packaging with `assembleRelease` does not regenerate a compatible LKM or ksud.

## Compatibility gate (fail closed)

1. Record exact target `uname -r`, firmware fingerprint, original `ksud --version`, and running module details.
2. Pin the GhostSam fork source to immutable commits and review differences against upstream `v3.3.1`; do not assume a tag match or binary compatibility.
3. Inventory each prebuilt artifact with SHA-256, ELF architecture/type and, for .ko, `modinfo` (vermagic, license, dependencies, symbol versions if available).
4. Compare required module metadata and symbol ABI against the prepared Samsung/GKI KMI build; KMI match alone is not sufficient proof of loadability.
5. Review kernel↔ksud UAPI matching and GhostSam-specific late-load behavior **without deploying or executing the privilege-escalation path**.
6. Perform reproducible builds and offline/static checks before even considering tests on an owned device.
7. Keep temporary-root working binaries backed up. Do not silently replace an existing `ksud`, LKM, or APK.
8. Acceptance requires recorded commit IDs, checksums, detailed CI results, and explicit device-specific compatibility findings. Otherwise mark BLOCKED.

## Verification performed

- [x] Confirmed official upstream v3.3.1 GitHub release
- [x] Read GhostSam README for origin, build system and KMI policy
- [x] Read `app/app/build.gradle.kts` for payload verification behavior
- [ ] Review exact fork-vs-upstream patch set
- [ ] Identify current payload SHA-256 and version
- [ ] Compile / test new LKM or ksud
- [ ] Build APK
- [ ] Device testing

**No claim that GhostSam has been upgraded is made by this document.**
