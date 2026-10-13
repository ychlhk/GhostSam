#!/usr/bin/env python3
"""Read-only release gate for the GhostSam Samsung 3.3.1 experimental branch.

Reports evidence completeness. A green CI audit is never a device approval.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
requirements = {
    "uapi": ("KSU_32680_MANAGER_UAPI_REVIEW.md", ["UAPI 2", "UAPI 5"]),
    "source_contract": ("KSU_32680_SOURCE_CONTRACT_CHECKPOINT.md", ["KDP", "DEFEX", "late_load.rs"]),
    "target_abi": ("SM_S9360_ABI_VERDICT.md", ["SM-S9360", "Module.symvers", "6.6.98"]),
    "port_status": ("KERNELSU_32680_PORT_STATUS.md", ["conflicts", "NOT FOR INSTALLATION"]),
    "release_statement": ("KERNELSU_V3_3_1_GHOSTSAM_STATUS.md", ["BLOCKED", "UAPI"]),
}
result = {"schema": 1, "target": "SM-S9360/S9360ZCSCCZG1",
          "upstream": "KernelSU v3.3.1 / 32680",
          "checks": {}, "device_release_approved": False,
          "reason": "Samsung ABI/CRC, KDP/DEFEX, UAPI runtime and daemon lifecycle unverified"}
for category, (name, terms) in requirements.items():
    file = DOCS / name
    data = file.read_text(encoding="utf-8") if file.exists() else ""
    missing = [word for word in terms if word.casefold() not in data.casefold()]
    result["checks"][category] = {"document": str(file.relative_to(ROOT)),
                                  "evidence_document_present": bool(data),
                                  "missing_review_markers": missing,
                                  "status": "present" if data and not missing else "missing"}
output = ROOT / "audit" / "samsung-release-gate.json"
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(output.read_text(encoding="utf-8"))
if any(v["status"] != "present" for v in result["checks"].values()):
    raise SystemExit("Required review evidence missing; release remains blocked.")
print("Evidence-document presence PASS; device release remains BLOCKED.")
