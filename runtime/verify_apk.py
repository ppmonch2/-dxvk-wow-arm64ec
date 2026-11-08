#!/usr/bin/env python3
"""Check the packaged manifest and pinned ntdll/server bytes inside the APK."""
import hashlib
import json
import pathlib
import sys
import zipfile


with zipfile.ZipFile(sys.argv[1]) as z:
    data = json.loads(z.read('assets/wehavephones/wehavephones-runtime-profiles.json'))
    assert data['defaultProfile'] == data['singleStageProfile'] == 'p11-ge9-wow-lab'
    assert list(data['profiles']) == ['p11-ge9-wow-lab']
    profile = data['profiles']['p11-ge9-wow-lab']
    assert profile['wineVersion'] == 'proton-11.0-9-arm64ec'
    assert profile['graphics']['version'] == 'turnip26.3.0-devel-1b51639c20'
    layer = profile['layer']
    with z.open('assets/' + layer['asset']) as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == layer['sha256']
    for a in profile['ntdll'] + profile['files']:
        assert hashlib.sha256(z.read('assets/wehavephones/' + a['asset'])).hexdigest() == a['sha256']
        assert '10.0-34' not in a['asset'] and '10.0-34' not in a['target']
    for relative, asset in [('lib/wine/aarch64-windows/ntdll.dll', 'ntdll/ntdll-wow-p11.dll'),
                            ('lib/wine/aarch64-unix/ntdll.so', 'ntdll/ntdll-wow-p11.so'),
                            ('bin/wineserver', 'server/wineserver-wow-p11')]:
        assert (pathlib.Path(sys.argv[2]) / relative).read_bytes() == z.read('assets/wehavephones/' + asset)
    print('APK verified: only P11 profile selected, matching runtime DLL/SO/server, SHA-256 verified, Turnip unchanged')
    expected = {
        'payload/d3d11.dll': 'a85a0671b6ee6cbba583c840b7cccfda7e63b9da21100ab508062bd5a262eff9',
        'payload/dxgi.dll': 'c37f3540f5c870e4b19bdc77a7d72e8f2c7ab8ddbc44da13eebaabdc89c7ac15',
        'stock/d3d11.dll': '5e3cf0b8075e5eed7ef2eb635eb91875573dfc47d42f15dca3a6626db00d2c0d',
        'stock/dxgi.dll': '176f667e69a948d853082d1859a4d0b97bd84f607f01f159799e434fadba0471',
    }
    for name, digest in expected.items():
        blob = z.read('assets/wehavephones/readback/' + name)
        assert hashlib.sha256(blob).hexdigest() == digest
        if name.startswith('payload/'):
            assert b'WOW-CUSTOM-ARM64-RB' in blob
    dex = b''.join(z.read(n) for n in z.namelist() if n.endswith('.dex'))
    assert b'WowReadbackLab' in dex and b'WOW_DXVK_EARLY_READBACK' in dex
    assert b'WoW-RB-logs' in dex
    print('Readback integration verified: stock/custom DLL pairs, DXVK marker and compiled startup/UI logic')
