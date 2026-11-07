#!/usr/bin/env python3
"""Verify native ARM64 PE DLLs and diagnostic strings in the final binaries."""
from pathlib import Path
import argparse
import struct

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
args = parser.parse_args()
for name in ('d3d11.dll', 'dxgi.dll'):
    data = (args.directory / name).read_bytes()
    assert data[:2] == b'MZ', name
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    assert data[pe:pe + 4] == b'PE\0\0', name
    machine, sections = struct.unpack_from('<HH', data, pe + 4)
    assert machine == 0xaa64, f'{name}: expected native ARM64 0xaa64, got {machine:#x}'
    assert struct.unpack_from('<H', data, pe + 24)[0] == 0x20b, 'Expected PE32+'
    assert struct.unpack_from('<H', data, pe + 22)[0] & 0x2000, 'Expected DLL'
    table = pe + 24 + struct.unpack_from('<H', data, pe + 20)[0]
    assert any(struct.unpack_from('<I', data, table + i * 40 + 36)[0] & 0x20000000 for i in range(sections))
    assert b'WOW-CUSTOM-ARM64-NATIVE [' in data, 'Missing HUD marker'
    assert b'WOW-CUSTOM-ARM64-NATIVE build=' in data, 'Missing log marker'
    assert ('module=' + name).encode() in data, 'Missing per-module log marker'
    assert b'DXVK instance initialized' in data, 'Missing instance marker'
    print(f'{name}: machine=0xaa64 (native ARM64), PE32+ DLL; HUD and per-module log strings verified')
