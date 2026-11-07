#!/usr/bin/env python3
"""Verify the native ARM64 syscall exports, rather than searching README text."""
import hashlib
import json
import pathlib
import struct
import sys


def main(root):
    path = root / 'lib/wine/aarch64-windows/ntdll.dll'
    b = path.read_bytes()
    u16 = lambda o: struct.unpack_from('<H', b, o)[0]
    u32 = lambda o: struct.unpack_from('<I', b, o)[0]
    pe = u32(60)
    assert b[pe:pe+4] == b'PE\0\0' and u16(pe+4) == 0xaa64
    opt = pe + 24
    assert u16(opt) == 0x20b
    sections = []
    for i in range(u16(pe+6)):
        s = opt + u16(pe+20) + 40*i
        vs, va, size, raw = struct.unpack_from('<IIII', b, s+8)
        sections.append((va, max(vs, size), raw))

    def off(rva):
        for va, size, raw in sections:
            if va <= rva < va+size:
                return raw+rva-va
        raise ValueError(hex(rva))

    exp = off(u32(opt+112))
    funcs, names, ords = (off(u32(exp+x)) for x in (28, 32, 36))
    exports = {}
    for i in range(u32(exp+24)):
        n = off(u32(names+4*i))
        exports[b[n:b.index(b'\0', n)].decode()] = u32(funcs+4*u16(ords+2*i))
    # ldr x16,[x18,#0x2f8]; nop; blr x16; ret. No absolute ntdll pointer.
    expected = struct.pack('<IIII', 0xf9400000 | ((0x2f8//8)<<10) | (18<<5) | 16,
                           0xd503201f, 0xd63f0200, 0xd65f03c0)
    checked = []
    for name in ('NtClose', 'NtDelayExecution', 'NtQueryInformationThread', 'NtWaitForSingleObject'):
        start = off(exports[name])
        code = b[start:start+48]
        assert expected in code, (name, code.hex())
        checked.append(name)
    hashes = {}
    for relative in ('lib/wine/aarch64-windows/ntdll.dll', 'lib/wine/aarch64-unix/ntdll.so', 'bin/wineserver'):
        p = root / relative
        data = p.read_bytes()
        hashes[relative] = hashlib.sha256(data).hexdigest()
        if p.suffix != '.dll':
            assert data[:4] == b'\x7fELF' and struct.unpack_from('<H', data, 18)[0] == 183
            assert b'libc.so\0' in data and b'libc.so.6\0' not in data
    print(json.dumps(dict(native_machine='0xaa64', dispatcher_teb_offset='0x2f8',
                          verified_exports=checked, sha256=hashes), indent=2))


if __name__ == '__main__':
    main(pathlib.Path(sys.argv[1]))
