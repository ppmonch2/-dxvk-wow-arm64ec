from pathlib import Path
import os,shutil,subprocess,tempfile
p=Path('package').resolve()
with tempfile.TemporaryDirectory() as d:
    target=Path(d)
    for f in (p/'stock').glob('*.dll'): shutil.copy2(f,target/f.name)
    env=dict(os.environ,WOW_DXVK_TEST_TARGET=str(target))
    for kit in (p,p/'control-231',p,p/'control-231'):
        subprocess.run([str(kit/'dxvk-test-check.exe'),'install'],env=env,check=True)
        for f in (kit/'payload').glob('*.dll'): assert (target/f.name).read_bytes()==f.read_bytes()
    subprocess.run([str(p/'control-231/dxvk-test-check.exe'),'restore'],env=env,check=True)
    for f in (p/'stock').glob('*.dll'): assert (target/f.name).read_bytes()==f.read_bytes()
print('PASS: 271 -> 231 -> 271 -> 231 -> stock')
