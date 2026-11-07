#!/usr/bin/env python3
"""Inspect compiled PE files: architecture, executable code and live diagnostic strings."""
from pathlib import Path
import argparse
import struct

parser = argparse.ArgumentParser()
parser.add_argument("directory", type=Path)
args = parser.parse_args()

for name in ("d3d11.dll", "dxgi.dll"):
    data = (args.directory / name).read_bytes()
    assert data[:2] == b"MZ", name
    pe = struct.unpack_from("<I", data, 0x3c)[0]
    assert data[pe:pe + 4] == b"PE\0\0", name
    machine, sections = struct.unpack_from("<HH", data, pe + 4)
    optional = pe + 24
    assert struct.unpack_from("<H", data, optional)[0] == 0x20b, "Expected PE32+"
    # ARM64EC final images may use AMD64 machine type with CHPE metadata.
    image_base = struct.unpack_from("<Q", data, optional + 24)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    table = optional + opt_size
    entries = []
    for i in range(sections):
        s = table + i * 40
        vs, va, raw_size, raw = struct.unpack_from("<IIII", data, s + 8)
        flags = struct.unpack_from("<I", data, s + 36)[0]
        entries.append((va, max(vs, raw_size), raw, raw_size, flags))
    def offset(rva):
        for va, size, raw, raw_size, flags in entries:
            if va <= rva < va + min(size, raw_size):
                return raw + rva - va
        raise AssertionError(f"RVA not backed by file: {rva:x}")
    assert any(flags & 0x20000000 and raw_size for _, _, _, raw_size, flags in entries)
    if machine == 0x8664:
        load_rva, load_size = struct.unpack_from("<II", data, optional + 112 + 10 * 8)
        assert load_rva and load_size >= 208, "AMD64 image without ARM64EC load config"
        config = offset(load_rva)
        chpe = struct.unpack_from("<Q", data, config + 200)[0]
        assert chpe >= image_base and chpe != 0, "Missing CHPE metadata"
        offset(chpe - image_base)
    else:
        assert machine in (0xa641, 0xa64e), f"Unexpected machine {machine:#x}"
    assert b"WOW-CUSTOM-ARM64EC" in data
    assert ("module=" + name).encode() in data, "Missing module-specific log call string"
    assert b"DXVK instance initialized" in data
    print(f"{name}: PE machine={machine:#06x}, ARM64EC metadata/target OK, HUD and module log strings present")
