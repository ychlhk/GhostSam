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
    return {
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
    args = p.parse_args()
    upstream, fork = inspect(args.upstream), inspect(args.fork)
    mismatch = upstream["uapi"] != fork["uapi"]
    result = {"upstream": upstream, "fork": fork, "uapi_mismatch": mismatch,
              "status": "BLOCKED" if mismatch else "REQUIRES_FURTHER_REVIEW"}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    rows = ["| Check | Official | GhostSam fork |", "|---|---|---|"]
    for key in ("uapi", "bundled_flag", "services_event", "samsung_kdp_object", "samsung_defex_object", "header_sha256", "kbuild_sha256"):
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
    # Observation-only workflow: incompatibility is reported, not concealed.
if __name__ == "__main__":
    main()
