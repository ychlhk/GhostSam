#!/usr/bin/env bash
# Experimental, compile-only KernelSU source merge for engineering review.
# DO NOT package, install, load, or flash the resulting code.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
OFFICIAL_SHA=0c0fdb960178fa12d80d6cbcfdcb6ad8be6a865d
SAMSUNG_SHA=0fde5f940559d36c48c9516902b3a7ce944a80c5
OUT_DIR="${KSU_AUDIT_DIR:-$ROOT/../ksu-audit}"
mkdir -p "$OUT_DIR"
test "$(git rev-parse HEAD)" = "$OFFICIAL_SHA"
test "$((30000 + $(git rev-list --count HEAD)))" -eq 32680

echo "Fetching fixed Samsung reference $SAMSUNG_SHA"
git fetch --no-tags https://github.com/snothin/KernelSU.git "$SAMSUNG_SHA"
test "$(git rev-parse FETCH_HEAD)" = "$SAMSUNG_SHA"
printf '%s\n' "$OFFICIAL_SHA" > "$OUT_DIR/official-sha.txt"
printf '%s\n' "$SAMSUNG_SHA" > "$OUT_DIR/samsung-sha.txt"

# -X ours resolves conflicting hunks mechanically in favor of official 32680,
# but leaves non-conflicting Samsung lines. It is NOT an accepted port.
set +e
git -c user.name=CI-Reference -c user.email=ci@example.invalid merge --no-commit --no-ff -X ours FETCH_HEAD > "$OUT_DIR/mechanical-merge.log" 2>&1
merge_rc=$?
set -e
echo "$merge_rc" > "$OUT_DIR/merge-exit.txt"
git status --short > "$OUT_DIR/status.txt"
git diff --cached --stat > "$OUT_DIR/staged-change-stat.txt" || true
git diff --cached --check > "$OUT_DIR/whitespace-check.txt" 2>&1 || true

{
 echo "# Experimental KernelSU 32680 Samsung merge gate"
 echo
 echo "Official: $OFFICIAL_SHA"
 echo "Samsung: $SAMSUNG_SHA"
 echo "Automatic source merge exit: $merge_rc"
 echo "This uses -X ours only as a diagnostic. It is NOT a validated resolution."
 echo "No binary artifacts from this merged tree may be installed on any device."
 echo
 echo "## Mandatory code-preservation checks"
} > "$OUT_DIR/RESULT.md"

if [ "$merge_rc" -ne 0 ]; then
 echo "BLOCKED: unresolved merge conflicts remain" | tee -a "$OUT_DIR/RESULT.md"
 git diff --name-only --diff-filter=U >> "$OUT_DIR/RESULT.md"
 exit 20
fi

checks=(
  "uapi/supercall.h|KERNEL_SU_UAPI_VERSION = 5"
  "kernel/Kbuild|compat/samsung_kdp.o"
  "kernel/Kbuild|compat/samsung_defex.o"
  "kernel/core/init.c|ksu_samsung_kdp_init"
  "kernel/core/init.c|ksu_samsung_defex_init"
  "kernel/hook/syscall_hook_manager.c|samsung_sucompat_hook_init"
  "kernel/feature/selinux_hide.c|KSU_SELINUX_HIDE_USE_KPROBE"
  "userspace/ksud/src/late_load.rs|stage_daemon_from"
  "userspace/ksud/src/late_load.rs|finish_install"
  "userspace/ksud/src/late_load.rs|ScriptWait"
)
failed=0
for check in "${checks[@]}"; do
  file="${check%%|*}"
  needle="${check#*|}"
  if grep -Fq "$needle" "$file"; then
    echo "PRESENT: $file -> $needle" >> "$OUT_DIR/RESULT.md"
  else
    echo "MISSING: $file -> $needle" | tee -a "$OUT_DIR/RESULT.md"
    failed=1
  fi
done
if [ "$failed" -ne 0 ]; then
  echo "BLOCKED: required official and Samsung paths are not all preserved." | tee -a "$OUT_DIR/RESULT.md"
  exit 21
fi
echo "PRESENCE CHECK PASSED (does not demonstrate runtime correctness)" | tee -a "$OUT_DIR/RESULT.md"

# Repair a compile-only declaration omission caused by the mechanical merge.
# The Samsung init path uses ret, while official 32680 removed its declaration.
# This patch declares only that local variable and changes no call or branch.
python3 - <<'PY'
from pathlib import Path
p = Path("kernel/core/init.c")
s = p.read_text()
anchor = "int __init kernelsu_init(void)\n{\n"
if s.count(anchor) != 1:
    raise SystemExit("Expected init function signature not uniquely found")
before, after = s.split(anchor, 1)
if after.lstrip().startswith("int ret;"):
    raise SystemExit("Unexpected ret declaration already present; review required")
s = before + anchor + "    int ret;\n" + after
p.write_text(s)
PY
echo "COMPILE-ONLY: declared local int ret in merged kernel/core/init.c" >> "$OUT_DIR/RESULT.md"

# Retain the original Samsung init/exit state marker when the automatic
# three-way merge keeps its use sites but drops the declaration.
# Fail closed if the source shape is different than the audited case.
python3 - <<'PY'
from pathlib import Path
p = Path("kernel/hook/syscall_hook_manager.c")
s = p.read_text()
marker = "syscall_hook_manager_initialized"
declaration = "static bool syscall_hook_manager_initialized;"
if s.count(marker) != 2 or declaration in s:
    raise SystemExit("Unexpected syscall hook manager source; manual review required")
anchor = '#include "hook/syscall_event_bridge.h"\n'
if s.count(anchor) != 1:
    raise SystemExit("Cannot locate unique declaration anchor")
s = s.replace(anchor, anchor + "\n" + declaration + "\n", 1)
p.write_text(s)
PY
echo "COMPILE-ONLY: restored missing original Samsung state declaration" >> "$OUT_DIR/RESULT.md"
