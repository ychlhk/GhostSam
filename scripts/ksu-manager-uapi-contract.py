#!/usr/bin/env python3
"""Pinned offline KernelSU 32601/32680 Manager/UAPI interface inventory.

Reads source files only; never builds, patches, loads, signs or runs privileged code.
All signing material is deliberately redacted; only equality of source defaults is reported.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path

FILES = {
    "uapi": "uapi/supercall.h",
    "manager_native": "manager/app/src/main/cpp/ksu.cc",
    "manager_kotlin": "manager/app/src/main/java/me/weishu/kernelsu/Natives.kt",
    "dispatch": "kernel/supercall/dispatch.c",
    "apk_sign": "kernel/manager/apk_sign.c",
    "throne": "kernel/manager/throne_tracker.c",
    "identity": "kernel/manager/manager_identity.h",
    "kbuild": "kernel/Kbuild",
}
OFFICIAL_SHA = "0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d"
SAMSUNG_SHA = "0fde5f940559d36c48c9516902b3a7ce944a80c5"


def read_source(directory: Path) -> dict[str, str]:
    result = {label: (directory / name).read_text(encoding="utf-8")
              for label, name in FILES.items()}
    for name, value in result.items():
        if len(value) < 100:
            raise ValueError(f"Unexpectedly short source: {name}")
    return result


def detect_uapi(s: str) -> int:
    m = re.search(r"KERNEL_SU_UAPI_VERSION\s*=\s*(\d+)", s)
    if not m:
        raise ValueError("Missing UAPI version")
    return int(m.group(1))


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"/\*.*?\*/|//[^\n]*", "", s, flags=re.S)).strip()


def structs(s: str) -> dict[str, str]:
    return {n: normalize(body) for n, body in re.findall(
        r"\bstruct\s+(ksu_[a-zA-Z0-9_]+)\s*\{(.*?)\}\s*;", s, flags=re.S
    )}


def ioctls(s: str) -> dict[str, str]:
    return {n: normalize(v) for n, v in re.findall(
        r"\b(KSU_IOCTL_[A-Z0-9_]+)\s*=\s*([^;]+);", s)}


def flags(s: str) -> dict[str, str]:
    return {n: normalize(v) for n, v in re.findall(
        r"\b(KSU_GET_INFO_FLAG_[A-Z0-9_]+)\s*=\s*([^;]+);", s)}


def defaults(s: str) -> dict[str, str]:
    pairs = re.findall(
        r"^\s*(KSU_EXPECTED_(?:SIZE|HASH))\s*[:?]?=\s*([^\s#]+)",
        s, flags=re.M
    )
    return dict(pairs)


def dispatch_permissions(s: str) -> dict[str, str]:
    matches = re.findall(
        r"\{\s*\.cmd\s*=\s*(KSU_IOCTL_[A-Z0-9_]+)\s*,(.*?)\n\s*\}",
        s, flags=re.S,
    )
    result = {}
    for name, body in matches:
        found = re.search(r"\.perm_check\s*=\s*([a-zA-Z0-9_]+)", body)
        result[name] = found.group(1) if found else "(none)"
    return result


def matched(old: str, new: str, keys: list[str]) -> dict[str, bool]:
    return {key: (key in old and key in new) for key in keys}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--samsung", type=Path, required=True)
    p.add_argument("--official", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    samsung, official = read_source(args.samsung), read_source(args.official)
    old_u, new_u = samsung["uapi"], official["uapi"]
    old_v, new_v = detect_uapi(old_u), detect_uapi(new_u)
    if (old_v, new_v) != (2, 5):
        raise RuntimeError(f"Expected pinned UAPI (2,5), got ({old_v},{new_v})")
    old_structs, new_structs = structs(old_u), structs(new_u)
    old_ioc, new_ioc = ioctls(old_u), ioctls(new_u)
    old_flags, new_flags = flags(old_u), flags(new_u)
    old_perm, new_perm = (dispatch_permissions(samsung["dispatch"]),
                          dispatch_permissions(official["dispatch"]))
    old_defaults, new_defaults = defaults(samsung["kbuild"]), defaults(official["kbuild"])

    # Compare primary source defaults without exposing any certificate hash or size.
    primary_equal = (len(old_defaults) == 2 and old_defaults == new_defaults)
    struct_delta = sorted(n for n in set(old_structs) | set(new_structs)
                          if old_structs.get(n) != new_structs.get(n))
    ioctl_delta = sorted(n for n in set(old_ioc) | set(new_ioc)
                         if old_ioc.get(n) != new_ioc.get(n))
    permission_delta = [
        {"command": n, "old": old_perm.get(n), "new": new_perm.get(n)}
        for n in sorted(set(old_perm) | set(new_perm))
        if old_perm.get(n) != new_perm.get(n)
    ]
    auth = {
        "samsung_supports_conditional_second_signature":
            "#ifdef EXPECTED_SIZE2" in samsung["apk_sign"] and
            "EXPECTED_HASH2" in samsung["apk_sign"],
        "official_source_uses_only_primary_signature":
            "EXPECTED_SIZE2" not in official["apk_sign"] and
            "EXPECTED_HASH2" not in official["apk_sign"],
        "source_default_primary_signature_identical": primary_equal,
        "samsung_optional_package_guard":
            "#ifdef KSU_MANAGER_PACKAGE" in samsung["apk_sign"],
        "both_verify_manager_apk_signature":
            "check_v2_signature" in samsung["apk_sign"] and
            "check_v2_signature" in official["apk_sign"],
        "both_require_signature_for_manager_tracking":
            "is_manager_apk(" in samsung["throne"] and
            "is_manager_apk(" in official["throne"],
    }
    native = {
        "both_read_kernel_uapi":
            matched(samsung["manager_native"], official["manager_native"],
                    ["get_kernel_uapi_version()", "get_info()", "KSU_IOCTL_GET_INFO"]),
        "both_read_manager_compiled_uapi":
            matched(samsung["manager_native"], official["manager_native"],
                    ["get_manager_uapi_version()", "KERNEL_SU_UAPI_VERSION"]),
        "both_use_legacy_info_fallback":
            matched(samsung["manager_native"], official["manager_native"],
                    ["KSU_IOCTL_GET_INFO_LEGACY", "g_version.uapi_version = 0"]),
        "official_bundled_flag_consumer":
            "KSU_GET_INFO_FLAG_BUNDLED" in official["manager_native"],
        "samsung_bundled_flag_consumer":
            "KSU_GET_INFO_FLAG_BUNDLED" in samsung["manager_native"],
        "samsung_requires_matching_uapi_for_full_manager":
            "kernelUAPIVersion != managerUAPIVersion" in samsung["manager_kotlin"],
        "official_requires_matching_uapi_for_full_manager":
            "kernelUAPIVersion == managerUAPIVersion" in official["manager_kotlin"],
    }
    info = {
        "old_reports_runtime_uapi": "cmd.uapi_version = KERNEL_SU_UAPI_VERSION" in samsung["dispatch"],
        "new_reports_runtime_uapi": "cmd.uapi_version = KERNEL_SU_UAPI_VERSION" in official["dispatch"],
        "both_set_manager_flag": matched(samsung["dispatch"], official["dispatch"],
                                         ["KSU_GET_INFO_FLAG_MANAGER", "if (is_manager())"]),
        "old_bundled_flag_server": "KSU_GET_INFO_FLAG_BUNDLED" in samsung["dispatch"],
        "new_bundled_flag_server": "KSU_GET_INFO_FLAG_BUNDLED" in official["dispatch"],
    }

    release_blockers = [
        "Current phone LKM/ksud is UAPI 2 while official 32680 Manager/kernel are UAPI 5. "
        "Manager feature completeness requires runtime UAPI equality; on-device negotiation not validated.",
        "Only source defaults for the main Manager certificate were compared. Actual "
        "installed Manager APK certificate, its package identity and compiled KernelSU configuration "
        "were NOT verified.",
        "Samsung fork's conditional second-signature code path differs from upstream 32680. "
        "No device requirement for the alternate certificate has been established.",
        "The official bundled feature flag changes Manager-facing status semantics; "
        "not tested on this model or merged runtime.",
        "Presence/equality of struct and IOCTL declarations does not verify "
        "runtime permission checks, SELinux, KDP/DEFEX, vendor ABI or safety.",
    ]
    static_checks = {
        "source_reference_versions_are_2_and_5": (old_v, new_v) == (2, 5),
        "all_uapi_struct_field_declarations_match": not struct_delta,
        "all_named_uapi_ioctl_declarations_match": not ioctl_delta,
        "expected_manager_primary_signature_defaults_match": primary_equal,
        "both_read_kernel_and_manager_uapi_versions":
            all(native["both_read_kernel_uapi"].values()) and
            all(native["both_read_manager_compiled_uapi"].values()),
        "both_have_get_info_legacy_fallback":
            all(native["both_use_legacy_info_fallback"].values()),
        "both_report_kernel_uapi_and_manager_flag":
            info["old_reports_runtime_uapi"] and info["new_reports_runtime_uapi"] and
            all(info["both_set_manager_flag"].values()),
        "both_validate_manager_apk_signatures": auth["both_verify_manager_apk_signature"],
        "both_manager_frontends_enforce_matching_uapi":
            native["samsung_requires_matching_uapi_for_full_manager"] and
            native["official_requires_matching_uapi_for_full_manager"],
        "official_bundled_flag_is_server_and_client_visible":
            info["new_bundled_flag_server"] and native["official_bundled_flag_consumer"],
    }
    results = {
        "pinned_revisions": {"samsung": SAMSUNG_SHA, "official": OFFICIAL_SHA},
        "uapi": {"samsung_version": old_v, "official_version": new_v,
                 "struct_names_old": len(old_structs), "struct_names_new": len(new_structs),
                 "struct_differences": struct_delta,
                 "ioctl_names_old": len(old_ioc), "ioctl_names_new": len(new_ioc),
                 "ioctl_differences": ioctl_delta,
                 "flags_added": {k: new_flags[k] for k in sorted(new_flags.keys() - old_flags.keys())},
                 "flags_removed": sorted(old_flags.keys() - new_flags.keys())},
        "manager_protocol": native, "kernel_get_info": info, "manager_authorization": auth,
        "kernel_dispatch_permissions": {
            "old_entry_count": len(old_perm), "new_entry_count": len(new_perm),
            "differences": permission_delta,
        },
        "static_checks": static_checks,
        "static_checks_passed": all(static_checks.values()),
        "runtime_compatible": False,
        "blockers": release_blockers,
        "note": "Text-only source comparison: not a compiled ABI, signing, or device-level verification."
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "manager-uapi-contract.json").write_text(
        json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    rows = [
        "# GhostSam Samsung 32601 vs official 32680: Manager/UAPI static contract",
        "",
        "**Offline read-only source review; NOT a device compatibility certificate.**",
        "",
        f"- Source UAPI: Samsung **{old_v}** / official **{new_v}**",
        f"- UAPI struct declaration differences: {len(struct_delta)} ({', '.join(struct_delta) or 'none'})",
        f"- Named IOCTL declaration differences: {len(ioctl_delta)} ({', '.join(ioctl_delta) or 'none'})",
        f"- New feature flags: {', '.join(sorted(new_flags.keys() - old_flags.keys())) or 'none'}",
        f"- Manager primary signing defaults equal at source level: **{primary_equal}**",
        "- Secondary signature support in Samsung source: "
          f"**{auth['samsung_supports_conditional_second_signature']}**; "
          "same in official: **"
          f"{not auth['official_source_uses_only_primary_signature']}**",
        "- Installed Manager certificate verification: **NOT PERFORMED**",
        "- Old/new distinct kernel permission dispatch entries: "
          f"{len(old_perm)}/{len(new_perm)}",
        "",
        "## Static invariants",
    ]
    rows.extend(f"- {'PASS' if v else 'NEEDS REVIEW'}: {k}" for k, v in static_checks.items())
    if permission_delta:
        rows.extend(["", "## Kernel IOCTL permission metadata changes"])
        for change in permission_delta:
            rows.append(f"- {change['command']}: {change['old']} -> {change['new']}")
    else:
        rows.append("- No named dispatch permission changes detected by this regex-based inventory.")
    rows.extend(["", "## Blockers — do not install", *[f"- {b}" for b in release_blockers]])
    rows.append("")
    rows.append("**Decision: runtime unverified / do not change existing 32601 root.**")
    (args.output / "manager-uapi-contract.md").write_text("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
