from pathlib import Path
import re,subprocess
p=Path('dxvk/src/d3d9/d3d9_include.h')
s=p.read_text()
pattern=r'^[ \t]*typedef\s+struct\s+_D3DDEVINFO_RESOURCEMANAGER\s*\{[^{}]*\}\s*D3DDEVINFO_RESOURCEMANAGER(?:\s*,\s*\*\s*LPD3DDEVINFO_RESOURCEMANAGER)?\s*;'
s,n=re.subn(pattern,'',s,flags=re.MULTILINE); assert n==1,n;p.write_text(s)
allowed={'src/d3d9/d3d9_include.h','src/d3d11/d3d11_main.cpp','src/dxgi/dxgi_main.cpp','src/dxvk/dxvk_instance.cpp','src/dxvk/hud/dxvk_hud_item.cpp'}
changed=set(subprocess.check_output(['git','-C','dxvk','diff','--name-only'],text=True).splitlines())
assert changed==allowed,changed
subprocess.run(['git','-C','dxvk','diff','--check'],check=True)
Path('diagnostic.patch').write_bytes(subprocess.check_output(['git','-C','dxvk','diff']))
print('PASS: only marker sites and compiler typedef compatibility changed')
