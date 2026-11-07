"""Prepare a self-contained on/off trial using the newly compiled DLL pair."""
from pathlib import Path
import hashlib
import json
import shutil

root = Path('package')
for d in ['payload','stock','source','logs','baseline']:
    (root/d).mkdir(parents=True,exist_ok=True)
names = ('d3d11.dll','dxgi.dll')
baseline = ['3e38c0c6eda66eb98beaeb807b52908a884e736aeb9a5a274297154ce60032bf',
            '0fad624223a1d9feaa7dc412d2866238c5bc1fadb40f178b05f205a64c4b5e05']
digests=[]
for i,name in enumerate(names):
    src=Path('dxvk/build-arm64-native/src')/('d3d11' if i==0 else 'dxgi')/name
    shutil.copyfile(src,root/'payload'/name)
    digests.append(hashlib.sha256(src.read_bytes()).hexdigest())
    stock=list(Path('stock-unpack').rglob(name))
    assert len(stock)==1
    shutil.copyfile(stock[0],root/'stock'/name)
    assert hashlib.sha256((root/'baseline'/name).read_bytes()).hexdigest()==baseline[i]
previous=json.loads(Path('previous/SHA256-PAYLOAD.json').read_text())
for name in names:
    assert hashlib.sha256((Path('previous/payload')/name).read_bytes()).hexdigest()==previous[name]
source=Path('tools/dxvk-test.c').read_text()
for old,new in zip(baseline,digests):
    assert source.count(old)==1
    source=source.replace(old,new)
declaration='static const char *priorTrial[2] = {\"'+previous[names[0]]+'\",\"'+previous[names[1]]+'\"};\n'
declaration+='static const char *baseline[2] = {"'+baseline[0]+'","'+baseline[1]+'"};\n'
source=source.replace('static const char *custom[2]',declaration+'static const char *custom[2]')
source=source.replace('(strcmp(previous[i], stock[i]) && strcmp(previous[i], custom[i]))',
                      '(strcmp(previous[i], stock[i]) && strcmp(previous[i], custom[i]) && strcmp(previous[i], baseline[i]) && strcmp(previous[i], priorTrial[i]))')
source=source.replace('Custom ARM64 pair bcec80c1e075 installed and verified.',
                      'Custom ARM64 RB pair installed and verified.')
source=source.replace('Use the verified bcec80c1e075 DLL pair.', 'Use this package verified LAB DLL pair.')
(root/'source/dxvk-test.c').write_text(source)
(root/'SHA256-PAYLOAD.json').write_text(json.dumps(dict(zip(names,digests)),indent=2))
for p in Path('launcher').glob('*.bat'):
    (root/p.name).write_bytes(p.read_text().replace('\n','\r\n').encode('ascii'))
for p in ['START-ASYNC-RU.md','PERFORMANCE-RU.md','LAB-RU.md','WAIT-RU.md','READBACK-RU.md']:
    shutil.copyfile(Path('launcher')/p,root/p)
for p in ['BUILD-INFO.txt','diagnostic.patch','LICENSE-DXVK','meson-log.txt','VERIFICATION.txt']:
    shutil.copyfile(Path('out')/p,root/p)
shutil.copyfile('patches/dxvk-gplasync-2.3.1-1.patch',root/'source/gplasync-upstream.patch')
shutil.copyfile('patches/PROVENANCE.md',root/'source/PROVENANCE.md')

shutil.copytree('patches/lab',root/'source/lab',dirs_exist_ok=True)
