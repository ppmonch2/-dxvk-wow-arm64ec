from pathlib import Path
import hashlib,json,struct,sys
root=Path(sys.argv[1])
payload=json.loads((root/'SHA256-PAYLOAD.json').read_text())
stock={'d3d11.dll':'5e3cf0b8075e5eed7ef2eb635eb91875573dfc47d42f15dca3a6626db00d2c0d',
       'dxgi.dll':'176f667e69a948d853082d1859a4d0b97bd84f607f01f159799e434fadba0471'}
for folder,manifest in [('payload',payload),('stock',stock)]:
    for name,digest in manifest.items():
        data=(root/folder/name).read_bytes()
        assert hashlib.sha256(data).hexdigest()==digest,(folder,name)
        pe=struct.unpack_from('<I',data,60)[0]
        assert struct.unpack_from('<H',data,pe+4)[0]==0xaa64
data=(root/'dxvk-test.exe').read_bytes();pe=struct.unpack_from('<I',data,60)[0]
assert struct.unpack_from('<H',data,pe+4)[0]==0xaa64
assert b'C:\\DXVK-backup' not in data
assert 'C:\\DXVK-backup'.encode('utf-16-le') not in data
assert not (root/'dxvk-test-check.exe').exists()
print('PASS: unchanged LAB payload, original stock, native installer, no fixed C backup dependency')
