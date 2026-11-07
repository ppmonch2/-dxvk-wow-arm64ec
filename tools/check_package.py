from pathlib import Path
import hashlib
import struct
import sys

root = Path(sys.argv[1])
expected = {
    'payload/d3d11.dll':'3e38c0c6eda66eb98beaeb807b52908a884e736aeb9a5a274297154ce60032bf',
    'payload/dxgi.dll':'0fad624223a1d9feaa7dc412d2866238c5bc1fadb40f178b05f205a64c4b5e05',
    'stock/d3d11.dll':'5e3cf0b8075e5eed7ef2eb635eb91875573dfc47d42f15dca3a6626db00d2c0d',
    'stock/dxgi.dll':'176f667e69a948d853082d1859a4d0b97bd84f607f01f159799e434fadba0471',
}
for name, digest in expected.items():
    data = (root/name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, name
    pe = struct.unpack_from('<I', data, 60)[0]
    assert struct.unpack_from('<H', data, pe+4)[0] == 0xaa64, name
data = (root/'dxvk-test.exe').read_bytes()
pe = struct.unpack_from('<I',data,60)[0]
assert data[pe:pe+4] == b'PE\0\0'
assert struct.unpack_from('<H',data,pe+4)[0] == 0xaa64
assert not (root/'dxvk-test-check.exe').exists(), 'Do not ship the test executable'
print('PASS: original/custom DLL hashes and native ARM64 helper architecture')
