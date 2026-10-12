#!/usr/bin/env python3
"""Read-only identification of ELF LKM resources embedded in a GhostSam ksud.

Never executes or loads the input binary. No extracted module is written to disk.
Only bounded ELF section headers and .modinfo are inspected.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import struct

EXPECTED_SHA256 = "9dcfda0240d859f41d70c404d145559c40c808b03800e78df527e43bee7f6fe0"
MAGIC = b"\x7fELF"
MAX_SECTIONS = 1024
MAX_ELF_BYTES = 12_000_000
REPORT_KEYS = {"name", "vermagic", "depends", "srcversion", "license", "intree", "retpoline"}


def read_embedded_module(data: bytes, start: int) -> dict | None:
    if start + 64 > len(data) or data[start:start + 6] != MAGIC + b"\x02\x01":
        return None
    # ELF64 / little-endian / relocatable AArch64; never interpret as executable.
    try:
        (e_type, e_machine, _version, _entry, _phoff, shoff, _flags,
         ehsize, _phentsize, _phnum, shentsize, shnum, shstridx) = struct.unpack_from(
            "<HHIQQQIHHHHHH", data, start + 16)
    except struct.error:
        return None
    if (e_type, e_machine, ehsize, shentsize) != (1, 183, 64, 64):
        return None
    if not (0 < shnum <= MAX_SECTIONS and 0 <= shstridx < shnum):
        return None
    if shoff < 64 or shoff + shnum * 64 > MAX_ELF_BYTES:
        return None
    if start + shoff + shnum * 64 > len(data):
        return None

    sections = []
    for index in range(shnum):
        try:
            name, kind, _flags, _addr, offset, size, link, _info, _align, _entsize = (
                struct.unpack_from("<IIQQQQIIQQ", data, start + shoff + index * 64)
            )
        except struct.error:
            return None
        if offset > MAX_ELF_BYTES or size > MAX_ELF_BYTES:
            return None
        if kind != 8 and start + offset + size > len(data):
            return None
        sections.append((name, kind, offset, size))
    _, kind, off, size = sections[shstridx]
    if kind == 8 or size > 500_000:
        return None
    names = data[start + off:start + off + size]

    modinfo = {}
    all_names = []
    for nameidx, sectkind, sectoff, sectsize in sections:
        if nameidx >= len(names):
            continue
        end = names.find(b"\0", nameidx)
        if end < 0:
            continue
        section_name = names[nameidx:end]
        all_names.append(section_name)
        if section_name != b".modinfo" or sectkind == 8 or sectsize > 200_000:
            continue
        raw = data[start + sectoff:start + sectoff + sectsize]
        for entry in raw.split(b"\0"):
            if b"=" not in entry:
                continue
            k, v = entry.split(b"=", 1)
            key = k.decode("ascii", errors="replace")
            if key in REPORT_KEYS:
                modinfo.setdefault(key, []).append(v.decode("utf-8", errors="replace")[:350])
    if b".modinfo" not in all_names:
        return None
    return {"offset": start, "sections": shnum, "modinfo": modinfo,
            "has_symbol_crc_section": any(x in all_names for x in (
                b"__versions", b"__version_ext_names", b"__version_ext_crcs"))}


def scan(path: Path) -> str:
    blob = path.read_bytes()
    sha = hashlib.sha256(blob).hexdigest()
    if sha != EXPECTED_SHA256:
        raise SystemExit(f"Unexpected ksud SHA-256: {sha}; refusing to treat as known 32601")
    lines = [
        "# GhostSam 32601 active ksud: read-only embedded LKM audit",
        "",
        f"- Input: \`{path.name}\` ({len(blob)} bytes)",
        f"- SHA-256: \`{sha}\`",
        "- Phone current ksud SHA-256: **matches** (owner's terminal output)",
        "- Parser: scans ELF64 ET_REL AArch64 headers, section names, and .modinfo; no code execution",
        "",
        "## KMI asset names found as raw strings (hints, not proof of selection)",
    ]
    hints = sorted(set(m.decode("ascii") for m in re.findall(
        rb"android\d{2}-\d+\.\d+(?:-exynos)?_kernelsu\.ko", blob)))
    if hints:
        lines.extend(f"- \`{h}\`" for h in hints[:100])
    else:
        lines.append("- None visible as uncompressed plain strings.")
    lines += ["", "## Embedded ELF kernel modules"]
    modules = []
    pos = 0
    while (pos := blob.find(MAGIC, pos)) != -1:
        if pos > 0:
            parsed = read_embedded_module(blob, pos)
            if parsed is not None:
                modules.append(parsed)
        pos += 4
    if not modules:
        lines += [
            "- No directly embedded ELF64 AArch64 relocatable module with \`.modinfo\` identified.",
            "- This does NOT prove absence: resources may be compressed or stored in another format.",
        ]
    for i, mod in enumerate(modules, 1):
        lines += [f"### Module candidate {i} (binary offset 0x{mod['offset']:x})",
                  f"- ELF section count: {mod['sections']}",
                  f"- Kernel symbol version section present: {mod['has_symbol_crc_section']}"]
        for key in sorted(mod["modinfo"]):
            for value in mod["modinfo"][key][:3]:
                lines.append(f"- \`{key}\`: \`{value}\`")
        lines.append("")
    lines += [
        "## Packaging signatures (diagnostic only)",
        f"- ELF64 marker count (including ksud executable): {blob.count(MAGIC)}",
        f"- XZ header count: {blob.count(bytes.fromhex('fd377a585a00'))}",
        f"- Zstandard header count: {blob.count(bytes.fromhex('28b52ffd'))}",
        "",
        "## Verified limitations",
        "- The source \`late_load.rs\` selects \`{kmi}_kernelsu.ko\` (or an Exynos alternative) and passes in-memory bytes to \`ksuinit::load_module\`.",
        "- Raw string matches and module offsets alone do not prove which module was loaded on the phone.",
        "- A compiled-in module's \`vermagic\` may differ from target and does not alone establish ABI compatibility under custom loaders.",
        "- Current phone module ELF and Samsung-specific symbol CRCs still require independent validation.",
        "- Do not install, load, patch or flash any file from this audit.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ksud", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = scan(args.ksud)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report)
    print(report)


if __name__ == "__main__":
    main()
