#!/usr/bin/env python3
"""Static compatibility gate for temporary GhostSam 32680 merged sources.

Reads source only. Never executes a loader, uses a device, or writes a binary.
Expected checkout: pinned official 32680 HEAD, Samsung SHA in FETCH_HEAD,
with the two existing experimental merge-review scripts already applied.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

OFFICIAL = "0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d"
SAMSUNG = "0fde5f940559d36c48c9516902b3a7ce944a80c5"
ROOT = Path.cwd()
OUT = Path(os.environ.get("KSU_AUDIT_DIR", str(ROOT.parent / "contract-audit")))
OUT.mkdir(parents=True, exist_ok=True)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def src(rev: str, path: str) -> str:
    return subprocess.check_output(["git", "show", f"{rev}:{path}"], text=True)


def lines_between(code: str, *terms: str) -> dict[str, int | None]:
    rows = code.splitlines()
    return {
        term: next((i + 1 for i, row in enumerate(rows) if term in row), None)
        for term in terms
    }


def check_sequence(code: str, terms: list[str]) -> dict:
    present = lines_between(code, *terms)
    offsets = [present[t] for t in terms]
    return {"locations": present, "present": all(x is not None for x in offsets),
            "in_order": (all(x is not None for x in offsets)
                         and offsets == sorted(offsets))}


def fingerprint(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def ver(code: str) -> int | None:
    m = re.search(r"KERNEL_SU_UAPI_VERSION\s*=\s*(\d+)", code)
    return int(m.group(1)) if m else None


def main() -> None:
    if git("rev-parse", "HEAD") != OFFICIAL or git("rev-parse", "FETCH_HEAD") != SAMSUNG:
        raise SystemExit("Pinned inputs do not match audit's verified revisions")

    loader_path = "userspace/ksuinit/src/lib.rs"
    late_path = "userspace/ksud/src/late_load.rs"
    init_path = "kernel/core/init.c"
    uapi_path = "uapi/supercall.h"
    sel_path = "kernel/feature/selinux_hide.c"

    old_loader = src(SAMSUNG, loader_path)
    new_loader = src(OFFICIAL, loader_path)
    merged_loader = (ROOT / loader_path).read_text()
    loader_identical = old_loader == new_loader == merged_loader

    loader_checks = {
        "same_code_all_three": loader_identical,
        "has_init_module_path": "init_module(&buffer, params)" in merged_loader,
        "has_kallsyms_symbol_resolution": '"/proc/kallsyms"' in merged_loader,
        "has_vermagic_failure_retry": (
            "extract_required_vermagic" in merged_loader and
            "replace_module_vermagic(&mut buffer, &required_vermagic)" in merged_loader and
            "init_module(&buffer, params).context" in merged_loader
        ),
    }

    old_late = src(SAMSUNG, late_path)
    new_late = src(OFFICIAL, late_path)
    merged_late = (ROOT / late_path).read_text()
    samsung_sequence = check_sequence(old_late, [
        "stage_daemon_from(", "ksuinit::load_module(", "finish_install("
    ])
    candidate_sequence = check_sequence(merged_late, [
        "stage_daemon_from(", "ksuinit::load_module(", "finish_install("
    ])
    late_checks = {
        "samsung_staging_sequence": samsung_sequence,
        "candidate_staging_sequence": candidate_sequence,
        "candidate_has_upstream_install": "utils::install(None, None)" in merged_late,
        "candidate_has_exynos_variant": "KSUD_TREE" in merged_late,
        "candidate_has_upstream_daemonize": "utils::daemonize(false)" in merged_late,
        "official_has_daemonize": "utils::daemonize(false)" in new_late,
        "samsung_has_daemonize": "utils::daemonize(false)" in old_late,
        "candidate_uses_kmi_lkm": 'format!("{kmi}_kernelsu.ko")' in merged_late,
        "candidate_calls_common_loader": "ksuinit::load_module(&ko_data, params)" in merged_late,
        "official_hash": fingerprint(new_late),
        "samsung_hash": fingerprint(old_late),
        "candidate_hash": fingerprint(merged_late),
    }

    old_uapi, new_uapi = src(SAMSUNG, uapi_path), src(OFFICIAL, uapi_path)
    merged_uapi = (ROOT / uapi_path).read_text()
    ioctl_pat = r"\b(KSU_IOCTL_[A-Z_]+)\s*=\s*([^;]+);"
    get_ioctls = lambda s: dict(re.findall(ioctl_pat, s))
    old_ioctl, new_ioctl, candidate_ioctl = map(get_ioctls, (
        old_uapi, new_uapi, merged_uapi))
    ioctl_changes = sorted(k for k in set(old_ioctl) | set(new_ioctl)
                           if old_ioctl.get(k) != new_ioctl.get(k))
    uapi_checks = {
        "samsung_version": ver(old_uapi),
        "official_version": ver(new_uapi),
        "candidate_version": ver(merged_uapi),
        "candidate_matches_official_text": merged_uapi == new_uapi,
        "ioctl_declaration_changes": ioctl_changes,
        "candidate_ioctl_declarations_match_official": candidate_ioctl == new_ioctl,
        "samsung_has_bundled_feature_flag": "KSU_GET_INFO_FLAG_BUNDLED" in old_uapi,
        "official_has_bundled_feature_flag": "KSU_GET_INFO_FLAG_BUNDLED" in new_uapi,
    }

    old_init, new_init = src(SAMSUNG, init_path), src(OFFICIAL, init_path)
    merged_init = (ROOT / init_path).read_text()
    samsung_init_order = [
        "ksu_init_symbol_resolver();",
        "ksu_samsung_kdp_init();",
        "prepare_creds();",
        "ksu_samsung_defex_init();",
        "ksu_syscall_hook_init();",
    ]
    init_checks = {
        "samsung_init_order": check_sequence(old_init, samsung_init_order),
        "candidate_init_order": check_sequence(merged_init, samsung_init_order),
        "candidate_has_kdp_cleanup": "ksu_samsung_kdp_exit();" in merged_init,
        "candidate_has_defex_cleanup": "ksu_samsung_defex_exit();" in merged_init,
        "upstream_new_init_markers": {
            key: {"official": key in new_init, "candidate": key in merged_init}
            for key in ("ksu_module_blacklist_init();",
                        "ksu_shell_su_adb_only_init();",
                        "ksu_feature_apply_forced();")
        },
    }

    old_sel, new_sel = src(SAMSUNG, sel_path), src(OFFICIAL, sel_path)
    merged_sel = (ROOT / sel_path).read_text()
    selinux_checks = {
        "official_has_compat_wrapper": "ksu_avc_has_perm_compat" in new_sel,
        "candidate_has_compat_wrapper": "ksu_avc_has_perm_compat" in merged_sel,
        "samsung_has_kprobe_path": "KSU_SELINUX_HIDE_USE_KPROBE" in old_sel,
        "candidate_has_kprobe_path": "KSU_SELINUX_HIDE_USE_KPROBE" in merged_sel,
        "samsung_has_nocfi_write": "static ssize_t __nocfi my_write_context(" in old_sel,
        "candidate_has_nocfi_write": "static ssize_t __nocfi my_write_context(" in merged_sel,
    }

    gate = {
        "pinned_inputs": True,
        "source_loader_identity": loader_identical,
        "common_loader_path_present": all(loader_checks.values()),
        "samsung_stage_and_finish_order": candidate_sequence["in_order"],
        "no_duplicate_install_path": not late_checks["candidate_has_upstream_install"],
        "exynos_selection_preserved": late_checks["candidate_has_exynos_variant"],
        "uapi_stays_official_5": uapi_checks["candidate_version"] == 5,
        "uapi_ioctl_declarations_match_official": uapi_checks["candidate_ioctl_declarations_match_official"],
        "kdp_defex_init_order": init_checks["candidate_init_order"]["in_order"],
        "samsung_cleanup_paths_present": (
            init_checks["candidate_has_kdp_cleanup"]
            and init_checks["candidate_has_defex_cleanup"]
        ),
        "upstream_features_not_silently_dropped": all(
            x["candidate"] for x in init_checks["upstream_new_init_markers"].values()
            if x["official"]
        ),
        "selinux_compile_paths_present": all(
            selinux_checks[k] for k in ("candidate_has_compat_wrapper",
                                        "candidate_has_kprobe_path",
                                        "candidate_has_nocfi_write")
        ),
    }

    manual_review_blockers = [
        "Working Samsung userspace uses UAPI 2; merged kernel/userspace use UAPI 5: "
        "device and manager protocol interoperability not validated.",
        "Samsung KDP/DEFEX, SELinux and vendor private symbol semantics require "
        "exact-device review; source presence/ordering is not a runtime test.",
        "Exact SM-S9360 exported symbols/CRCs and module-vendor ABI are unknown.",
        "No validated controlled recovery / install test is approved.",
    ]
    if (late_checks["official_has_daemonize"]
            and not late_checks["candidate_has_upstream_daemonize"]):
        manual_review_blockers.append(
            "Official late-load daemonize(false) is absent from Samsung "
            "baseline and the merged candidate; process-lifecycle behavior "
            "requires an explicit review, not an automatic code insertion."
        )

    report = {
        "manual_review_blockers": manual_review_blockers,
        "inputs": {"official": OFFICIAL, "samsung": SAMSUNG},
        "loader": loader_checks, "late_load": late_checks,
        "uapi": uapi_checks, "init": init_checks, "selinux": selinux_checks,
        "static_gate": gate, "static_gate_passed": all(gate.values()),
        "runtime_compatible": False,
        "note": "Source presence/ordering only. Runtime/ABI/recovery NOT validated.",
    }
    (OUT / "SOURCE_CONTRACT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n")
    rows = [
        "# Samsung 32601 vs experimental 32680: source contract gate",
        "",
        "This is a **source-only, non-installable** comparison.",
        "",
        f"- Samsung reference: `{SAMSUNG}`",
        f"- Official reference: `{OFFICIAL}`",
        "- Same `ksuinit/src/lib.rs` code in Samsung, official, and merged: "
        + str(loader_identical),
        "- Common loader does kallsyms symbol rewriting, invokes `init_module`, "
        "and conditionally patches `vermagic` on log-indicated mismatch.",
        f"- Baseline UAPI: {uapi_checks['samsung_version']}; official/merged: "
        f"{uapi_checks['official_version']}/{uapi_checks['candidate_version']}.",
        "",
        "## Static contract checks (NOT runtime validation)",
    ]
    rows.extend(f"- {'PASS' if passed else 'BLOCKED'}: {name}"
                for name, passed in gate.items())
    rows += [
        "",
        "## Observed source differences",
        f"- Candidate late-load order: {candidate_sequence['locations']}",
        f"- Candidate also invokes upstream install: {late_checks['candidate_has_upstream_install']}",
        f"- UAPI ioctl declaration changes between references: {ioctl_changes}",
        "- Upstream init feature presence in merged:",
    ]
    rows.extend(f"  - {key}: {'present' if x['candidate'] else 'MISSING'}"
                for key, x in init_checks["upstream_new_init_markers"].items())
    rows += [
        "",
        "## Outstanding semantic and device-specific blockers",
        *[f"- {item}" for item in manual_review_blockers],
        "",
        "## Release decision: **BLOCKED / NOT INSTALLABLE**",
        "Passing these static gates would still not verify memory safety, symbol CRCs, "
        "kernel structure layouts, Samsung KDP/DEFEX, SELinux, UAPI wire runtime, "
        "or manager authorization on SM-S9360.",
        "Do not use this audit for loading, flashing, signing, installing, "
        "or changing the phone's working 32601 root.",
    ]
    (OUT / "SOURCE_CONTRACT.md").write_text("\n".join(rows) + "\n")
    print((OUT / "SOURCE_CONTRACT.md").read_text())


if __name__ == "__main__":
    main()
