#!/usr/bin/env python3
"""Offline, experimental conflict-resolution probe. Never install built results.

The source inputs are exact pinned Git objects. This script only repairs the
5 known mechanical conflict sites for COMPILE TESTS, and deliberately keeps
the device runtime-compatibility gate closed.
"""
from __future__ import annotations

import pathlib
import subprocess
import os
import hashlib

ROOT = pathlib.Path.cwd()
SAMSUNG_SHA = "0fde5f940559d36c48c9516902b3a7ce944a80c5"
OFFICIAL_SHA = "0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d"
OUT = pathlib.Path(os.environ.get("KSU_AUDIT_DIR", str(ROOT.parent / "ksu-audit")))
OUT.mkdir(parents=True, exist_ok=True)

def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()

assert git("rev-parse", "HEAD") == OFFICIAL_SHA, "Unexpected official source"
assert git("rev-parse", "FETCH_HEAD") == SAMSUNG_SHA, "Unexpected Samsung source"

def file(path: str) -> str:
    return (ROOT / path).read_text()

def save(path: str, data: str) -> None:
    (ROOT / path).write_text(data)

def replace_once(s: str, original: str, replacement: str, path: str) -> str:
    if s.count(original) != 1:
        raise RuntimeError(f"Expected exactly one anchor in {path}: {original!r}, found {s.count(original)}")
    return s.replace(original, replacement, 1)

changes = []

# Conflict 1: preserve the Samsung error-return variable and upstream banner.
path = "kernel/core/init.c"
s = file(path)
anchor = "int __init kernelsu_init(void)\n{\n"
if "    int ret;\n" not in s[s.index(anchor): s.index(anchor) + 150]:
    s = replace_once(s, anchor, anchor + "    int ret;\n", path)
    save(path, s)
    changes.append(path + ": restore Samsung init error-return variable")

# Conflict 2: preserve Samsung CFI annotation AND upstream SELinux compatibility.
path = "kernel/feature/selinux_hide.c"
s = file(path)
before = "static ssize_t my_write_context(struct file *file, char *buf, size_t size)"
after = "static ssize_t __nocfi my_write_context(struct file *file, char *buf, size_t size)"
if before in s:
    s = replace_once(s, before, after, path)
    save(path, s)
    changes.append(path + ": restore Samsung __nocfi annotation")
assert after in s
assert "ksu_avc_has_perm_compat" in s

# Conflict 3: preserve the fork's original complete Samsung hook declarations
# alongside the upstream architecture include without manufacturing new logic.
path = "kernel/hook/syscall_hook_manager.c"
s = file(path)
fork = git("show", f"{SAMSUNG_SHA}:{path}")
start = fork.index('#include "policy/allowlist.h"')
end = fork.index("\n#ifdef CONFIG_KRETPROBES\n", start)
block = fork[start:end]
if "static int samsung_sucompat_hook_init(" not in s:
    s = replace_once(s, "\n#ifdef CONFIG_KRETPROBES\n\nstatic struct kretprobe *init_kretprobe", "\n" + block + "\n\n#ifdef CONFIG_KRETPROBES\n\nstatic struct kretprobe *init_kretprobe", path)
    save(path, s)
    changes.append(path + ": preserve existing Samsung hook definitions")
assert '#include "hook/riscv64/syscall_regs.h"' in s
assert "static int samsung_sucompat_hook_init(" in s

# Conflict 4: preserve the real upstream protocol version. This is NOT a
# backport or a claim of compatibility with the user's active UAPI 2 module.
path = "uapi/supercall.h"
s = file(path)
assert "KERNEL_SU_UAPI_VERSION = 5;" in s
assert "KERNEL_SU_UAPI_VERSION = 2;" not in s
changes.append(path + ": retain official UAPI 5 (runtime review REQUIRED)")

# Conflict 5: retain upstream stage timeouts and Samsung daemon staging while
# eliminating a no-longer-used import if the restart block was removed.
path = "userspace/ksud/src/late_load.rs"
s = file(path)
old = "use std::{process::Command, time::Instant};"
if old in s and "Command::" not in s:
    s = replace_once(s, old, "use std::time::Instant;", path)
    save(path, s)
    changes.append(path + ": remove dead import after Samsung manager restart removal")
for required in ["ScriptWait", "stage_daemon_from", "finish_install"]:
    assert required in s, f"Missing late-load capability {required}"

# Additional overlapping source: upstream moved old_pol assignment under the
# mutex, whereas the Samsung fork inserted its null guard before the mutex.
# Preserve the guard, but move it after the locked pointer fetch.
path = "kernel/selinux/rules.c"
s = file(path)
start_marker = "    /* No policy loaded yet; ksu_dup_sepolicy() would oops on the NULL policy. */"
lock_marker = "    mutex_lock(&selinux_state.policy_mutex);"
assign_marker = "    old_pol = rcu_dereference_protected(selinux_state.policy, lockdep_is_held(&selinux_state.policy_mutex));"
if start_marker in s:
    start = s.index(start_marker)
    end = s.index(lock_marker, start)
    guard = s[start:end]
    assert guard.count("if (!old_pol)") == 1
    assert guard.count("        return;") == 1
    s = s[:start] + s[end:]
    guard = guard.replace("        return;", "        mutex_unlock(&selinux_state.policy_mutex);\n        return;", 1)
    s = replace_once(s, assign_marker, assign_marker + "\n" + guard.rstrip(), path)
    save(path, s)
    changes.append(path + ": preserve Samsung null guard after official locked policy lookup")
assert s.count("if (!old_pol)") == 1
assert s.index(lock_marker) < s.index(assign_marker) < s.index("if (!old_pol)")

subprocess.run(["git", "diff", "--check"], check=True)
with (OUT / "CONFLICT_RESOLUTIONS.md").open("w") as report:
    report.write("# Experimental Samsung 32680 source-resolution audit\n\n")
    report.write("This is a **non-installable compile-only** candidate.\n")
    report.write("The git merge used -X ours; this script restores specific fork functionality that was overwritten.\n")
    report.write("The five conflict decisions have NOT been runtime verified.\n\n")
    for item in changes:
        report.write(f"- {item}\n")
    report.write("\n## Remaining blockers\n")
    report.write("- Validate all 12 overlapping source paths beyond mechanical merge.\n")
    report.write("- Review SELinux, syscall hooks, KDP/DEFEX, and security implications.\n")
    report.write("- Validate UAPI5/ksud/manager and staged loader together.\n")
    report.write("- Verify SM-S9360 exact vendor kernel ABI, symbols and policies.\n")
    report.write("- No module, loader, ksud, or patch may be installed on the phone based on this build.\n")

with (OUT / "SHA256-RESOLVED-SOURCES.txt").open("w") as report:
    for path in ["kernel/core/init.c", "kernel/feature/selinux_hide.c",
                 "kernel/hook/syscall_hook_manager.c", "uapi/supercall.h",
                 "userspace/ksud/src/late_load.rs"]:
        digest = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        report.write(f"{digest}  {path}\n")

print("Five conflict sites integrated for compile-only tests (NOT validated for device use).")
for item in changes:
    print(item)
