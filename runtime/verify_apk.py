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
        assert hashlib.sha256(z.read('assets/' + a['asset'])).hexdigest() == a['sha256']
        assert '10.0-34' not in a['asset'] and '10.0-34' not in a['target']
    for relative, asset in [('lib/wine/aarch64-windows/ntdll.dll', 'ntdll/ntdll-wow-p11.dll'),
                            ('lib/wine/aarch64-unix/ntdll.so', 'ntdll/ntdll-wow-p11.so'),
                            ('bin/wineserver', 'server/wineserver-wow-p11')]:
        assert (pathlib.Path(sys.argv[2]) / relative).read_bytes() == z.read('assets/' + asset)
    print('APK verified: only P11 profile selected, matching runtime DLL/SO/server, SHA-256 verified, Turnip unchanged')
