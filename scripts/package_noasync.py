"""Make a no-async diagnostic kit without rebuilding or changing either DXVK DLL."""
from pathlib import Path
import hashlib
import json
import shutil

root = Path('package')
expected = {
    'd3d11.dll': 'a85a0671b6ee6cbba583c840b7cccfda7e63b9da21100ab508062bd5a262eff9',
    'dxgi.dll': 'c37f3540f5c870e4b19bdc77a7d72e8f2c7ab8ddbc44da13eebaabdc89c7ac15',
}
for name, digest in expected.items():
    blob = (root / 'payload' / name).read_bytes()
    assert hashlib.sha256(blob).hexdigest() == digest
    assert b'WOW-CUSTOM-ARM64-RB' in blob

for mode in ('off', 'on'):
    p = root / ('play-readback-' + mode + '.bat')
    text = p.read_text()
    assert text.count('set "DXVK_ASYNC=1"') == 1
    assert 'set "WOW_DXVK_EARLY_READBACK=' + ('1' if mode == 'on' else '0') + '"' in text
    text = text.replace('set "DXVK_ASYNC=1"', 'set "DXVK_ASYNC=0"')
    text = text.replace('WOW_DXVK_PROFILE=readback-' + mode,
                        'WOW_DXVK_PROFILE=readback-' + mode + '-noasync')
    p.write_bytes(text.replace('\n', '\r\n').encode('ascii'))
for p in root.glob('play-*.bat'):
    if p.name not in ('play-custom.bat', 'play-readback-off.bat', 'play-readback-on.bat'):
        p.unlink()
shutil.copyfile('NOASYNC-RU.md', root / 'START-HERE-RU.md')
for name in ('START-ASYNC-RU.md', 'PERFORMANCE-RU.md', 'LAB-RU.md', 'WAIT-RU.md', 'READBACK-RU.md'):
    (root / name).unlink(missing_ok=True)
for name, digest in expected.items():
    assert hashlib.sha256((root / 'payload' / name).read_bytes()).hexdigest() == digest
(root / 'NOASYNC-VERIFICATION.json').write_text(json.dumps({
    'dlls_unchanged': expected, 'DXVK_ASYNC': 0,
    'readback_off': 0, 'readback_on': 1,
    'purpose': 'Isolate missing UI with async disabled; runtime visual correctness not yet tested'
}, indent=2) + '\n')
print('PASS: original native RB DLL hashes unchanged; both launchers force DXVK_ASYNC=0; readback flag and other settings preserved')
