"""Windows smoke tests: copying real ARM64 DLL data, not executing the game."""
from pathlib import Path
import ctypes
import os
import shutil
import subprocess
import sys
import tempfile

package = Path(sys.argv[1]).resolve()
helper = package / 'dxvk-test-check.exe'
names = ('d3d11.dll', 'dxgi.dll')
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    target = root / 'system32'; target.mkdir()
    backup = root / 'backup'; backup.mkdir()
    env = dict(os.environ, WOW_DXVK_TEST_TARGET=str(target), WOW_DXVK_TEST_BACKUP=str(backup))
    for name in names:
        shutil.copyfile(package/'stock'/name, target/name)
        shutil.copyfile(package/'stock'/name, backup/name)
    def run(mode, success=True):
        p = subprocess.run([str(helper), mode], env=env, text=True, capture_output=True)
        print(mode, p.returncode, p.stdout, p.stderr)
        assert (p.returncode == 0) == success
    def equal(folder):
        for name in names:
            assert (target/name).read_bytes() == (package/folder/name).read_bytes(), name
    run('status')
    run('install'); equal('payload')
    run('install'); equal('payload')
    run('restore'); equal('stock')
    # Bad payload must fail before either destination is touched.
    payload = package/'payload/dxgi.dll'; original = payload.read_bytes()
    payload.write_bytes(original+b'corruption')
    try:
        run('install', False); equal('stock')
    finally:
        payload.write_bytes(original)
    # Lock the second target against writes; the first target must roll back.
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.CreateFileW(str(target/'dxgi.dll'),0x80000000,1,None,3,0,None)
    assert handle != ctypes.c_void_p(-1).value
    try:
        run('install',False); equal('stock')
    finally:
        kernel.CloseHandle(handle)
    (target/'dxgi.dll').write_bytes(b'unknown build')
    run('install',False)
    assert (target/'dxgi.dll').read_bytes()==b'unknown build'
    assert (target/'d3d11.dll').read_bytes()==(package/'stock/d3d11.dll').read_bytes()
    shutil.copyfile(package/'stock/dxgi.dll',target/'dxgi.dll')
    (backup/'dxgi.dll').unlink()
    run('install',False);equal('stock')
print('PASS: SHA checks, install, repeat install, restore, corrupt payload, locked destination rollback, unknown DLL, missing backup')
