from pathlib import Path
import hashlib,json,shutil,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from inspect_pe import PE
root=Path('out'); root.mkdir(exist_ok=True)
names=('d3d11.dll','dxgi.dll')
baseline=('3e38c0c6eda66eb98beaeb807b52908a884e736aeb9a5a274297154ce60032bf','0fad624223a1d9feaa7dc412d2866238c5bc1fadb40f178b05f205a64c4b5e05')
stock=('5e3cf0b8075e5eed7ef2eb635eb91875573dfc47d42f15dca3a6626db00d2c0d','176f667e69a948d853082d1859a4d0b97bd84f607f01f159799e434fadba0471')
rb=('a85a0671b6ee6cbba583c840b7cccfda7e63b9da21100ab508062bd5a262eff9','c37f3540f5c870e4b19bdc77a7d72e8f2c7ab8ddbc44da13eebaabdc89c7ac15')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
new=[]; reports=[]
for i,name in enumerate(names):
    source=Path('dxvk/build-arm64-native/src')/('d3d11' if i==0 else 'dxgi')/name
    old=Path('control-source')/name
    assert sha(old)==baseline[i]
    original=list(Path('stock-unpack').rglob(name)); assert len(original)==1
    assert sha(original[0])==stock[i]
    pe=PE(source); previous=PE(old)
    assert pe.machine==previous.machine==0xaa64
    assert pe.exports()==previous.exports(), (name,'exports changed')
    assert b'WOW-CUSTOM-ARM64-DXVK271' in pe.b
    assert not any(x in pe.b for x in (b'WOW_DXVK_EARLY_READBACK',b'WOW_DXVK_DEDUP',b'DXVK_ASYNC'))
    assert not any(x.lower().startswith(('libstdc++','libc++','libgcc','libwinpthread')) for x in pe.imports())
    report=pe.report(); report['imports_added_vs_231']={k:sorted(set(v)-set(previous.imports().get(k,[]))) for k,v in pe.imports().items() if set(v)-set(previous.imports().get(k,[]))}
    reports.append(report); new.append(sha(source))
    for kit,payload in ((root,source),(root/'control-231',old)):
        for folder,src in (('payload',payload),('stock',original[0])):
            (kit/folder).mkdir(parents=True,exist_ok=True); shutil.copy2(src,kit/folder/name)
    (root/'baseline').mkdir(exist_ok=True); shutil.copy2(old,root/'baseline'/name)
(root/'PE-AUDIT.json').write_text(json.dumps(reports,indent=2))
(root/'source').mkdir(exist_ok=True)
for kit,hashes,label in ((root,new,'DXVK 2.7.1'),(root/'control-231',baseline,'DXVK 2.3.1 control')):
    template=Path('tools/dxvk-test.c').read_text()
    for a,b in zip(baseline,hashes): template=template.replace(a,b)
    extra='\nstatic const char *known[3][2] = '+json.dumps([list(baseline),list(rb),list(new)]).replace('[','{').replace(']','}')+';\n'
    template=template.replace('static int path(',extra+'\nstatic int known_hash(int i, const char *value) {\n  if (!strcmp(value, stock[i]) || !strcmp(value, custom[i])) return 1;\n  for (int j=0;j<3;j++) if (!strcmp(value,known[j][i])) return 1;\n  return 0;\n}\n\nstatic int path(')
    template=template.replace('(strcmp(previous[i], stock[i]) && strcmp(previous[i], custom[i]))','!known_hash(i, previous[i])')
    template=template.replace('Custom ARM64 pair bcec80c1e075 installed and verified.',label+' ARM64 pair installed and verified.').replace('Use the verified bcec80c1e075 DLL pair.','Extract the complete verified kit again.')
    filename=root/'source'/('helper-271.c' if kit==root else 'helper-231.c'); filename.write_text(template)
    subprocess.run(['aarch64-w64-mingw32-clang','-O2','-Wall','-Wextra','-Werror','-municode','-static',str(filename),'-ladvapi32','-o',str(kit/'dxvk-test.exe')],check=True)
    assert PE(kit/'dxvk-test.exe').machine==0xaa64
for p in Path('launcher').iterdir(): shutil.copy2(p,root/p.name)
shutil.copy2('START-RU.md',root/'START-RU.md')
shutil.copy2('dxvk/LICENSE',root/'LICENSE-DXVK')
shutil.copy2('diagnostic.patch',root/'source/diagnostic-271.patch')
shutil.copy2('control-source/diagnostic.patch',root/'source/diagnostic-231.patch')
shutil.copy2('control-source/BUILD-INFO.txt',root/'source/CONTROL-231-BUILD-INFO.txt')
(root/'SHA256-PAYLOAD.json').write_text(json.dumps({'271':new,'231':baseline,'stock':stock},indent=2))
print(json.dumps({'271':new,'231':baseline,'machine':'ARM64 0xaa64','exports':'compatible'},indent=2))
