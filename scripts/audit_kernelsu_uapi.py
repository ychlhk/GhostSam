#!/usr/bin/env python3
"""Read-only comparison of KernelSU userspace/kernel interface declarations."""
import argparse
import hashlib
import json
import re
from pathlib import Path

def inspect(root):
    header = root / "uapi" / "supercall.h"
    kbuild = root / "kernel" / "Kbuild"
    if not header.is_file() or not kbuild.is_file():
        raise SystemExit(f"Required source missing under {root}")
    h, k = header.read_text(), kbuild.read_text()
    match = re.search(r"\bKERNEL_SU_UAPI_VERSION\s*=\s*(\d+)\s*;", h)
    if not match:
        raise SystemExit(f"No UAPI version found in {header}")
    dispatch_file = root / "kernel" / "supercall" / "dispatch.c"
    supercall_file = root / "kernel" / "supercall" / "supercall.c"
    calls_file = root / "userspace" / "ksud" / "src" / "ksucalls.rs"
    dispatch = dispatch_file.read_text() if dispatch_file.is_file() else ""
    supercall = supercall_file.read_text() if supercall_file.is_file() else ""
    calls = calls_file.read_text() if calls_file.is_file() else ""
    return {
        "uapi3_scoped_session_kernel": (
            "ksu_install_su_fd(" in supercall
            and "ksu_is_su_session_fd(" in supercall
            and "allow_su_session" in dispatch
        ) if dispatch and supercall else None,
        "uapi4_bundled_dispatch": "KSU_GET_INFO_FLAG_BUNDLED" in dispatch if dispatch else None,
        "uapi5_services_dispatch": "case EVENT_SERVICES:" in dispatch if dispatch else None,
        "uapi5_services_userspace": "EVENT_SERVICES" in calls if calls else None,
        "uapi": int(match.group(1)),
        "header_sha256": hashlib.sha256(header.read_bytes()).hexdigest(),
        "kbuild_sha256": hashlib.sha256(kbuild.read_bytes()).hexdigest(),
        "scoped_session_documented": bool(re.search(r"scoped su-session driver fd", h)),
        "bundled_flag": bool(re.search(r"^\s*static const .*\bKSU_GET_INFO_FLAG_BUNDLED\b", h, re.M)),
        "services_event": bool(re.search(r"^\s*static const .*\bEVENT_SERVICES\b", h, re.M)),
        "samsung_kdp_object": "compat/samsung_kdp.o" in k,
        "samsung_defex_object": "compat/samsung_defex.o" in k,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--upstream", required=True, type=Path)
    p.add_argument("--fork", required=True, type=Path)
    p.add_argument("--output", default="build/ksu-uapi-audit", type=Path)
    p.add_argument("--fail-on-mismatch", action="store_true", help="Return exit code 2 when source UAPI versions differ")
    args = p.parse_args()
    upstream, fork = inspect(args.upstream), inspect(args.fork)
    mismatch = upstream["uapi"] != fork["uapi"]
    result = {"upstream": upstream, "fork": fork, "uapi_mismatch": mismatch,
              "status": "BLOCKED" if mismatch else "REQUIRES_FURTHER_REVIEW"}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    rows = ["| Check | Official | GhostSam fork |", "|---|---|---|"]
    for key in ("uapi", "bundled_flag", "services_event", "samsung_kdp_object", "samsung_defex_object", "header_sha256", "kbuild_sha256", "uapi3_scoped_session_kernel", "uapi4_bundled_dispatch", "uapi5_services_dispatch", "uapi5_services_userspace"):
        rows.append(f"| `{key}` | `{upstream[key]}` | `{fork[key]}` |")
    report = (
        "# KernelSU source compatibility audit\n\n"
        f"**Status: {result['status']}** — this is a declaration-only review, not a binary compatibility test.\n\n"
        + "\n".join(rows)
        + "\n\nThis audit does not build, load, package, or execute any kernel code. "
          "An equal UAPI version does not establish ABI compatibility.\n"
    )
    (args.output / "report.md").write_text(report)
    print(report)
    if args.fail_on_mismatch and mismatch:
        raise SystemExit(2)
    # Report remains available even when the compatibility gate fails.
if __name__ == "__main__":
    main()
