from pathlib import Path
import sys,json,hashlib,struct
from inspect_pe import PE

root=Path(sys.argv[1])
expected=json.loads((root/'SHA256-PAYLOAD.json').read_text())
stock={'d3d11.dll':'5e3cf0b8075e5eed7ef2eb635eb91875573dfc47d42f15dca3a6626db00d2c0d',
       'dxgi.dll':'176f667e69a948d853082d1859a4d0b97bd84f607f01f159799e434fadba0471'}
for name in ['d3d11.dll','dxgi.dll']:
    new=PE(root/'payload'/name);original=PE(root/'stock'/name)
    assert new.machine==original.machine==0xaa64
    assert hashlib.sha256(new.b).hexdigest()==expected[name]
    assert hashlib.sha256(original.b).hexdigest()==stock[name]
    assert new.imports()==original.imports(),f'{name}: imports changed; inspect before shipping'
    assert new.exports()==original.exports(),f'{name}: exports changed'
    assert b'WOW-CUSTOM-ARM64-WAIT' in new.b
    assert ('module='+name).encode() in new.b
    print(name,'SHA256, ARM64, markers and exact import/export compatibility: PASS')
assert b'async_pipeline_scheduled' in (root/'payload/d3d11.dll').read_bytes()
assert b'WOW_METRICS' in (root/'payload/d3d11.dll').read_bytes()
assert b'WOW_LAB workers=' in (root/'payload/d3d11.dll').read_bytes()
assert PE(root/'dxvk-test.exe').machine==0xaa64
assert not (root/'dxvk-test-check.exe').exists()
print('ARM64 installer and async execution marker: PASS')

assert b'WOW_DXGI_METRICS' in (root/'payload/dxgi.dll').read_bytes()
