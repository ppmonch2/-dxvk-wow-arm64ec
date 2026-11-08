"""Fetch the unchanged upstream asset bytes through GitHub release asset IDs."""
from pathlib import Path
import hashlib,json,subprocess,sys
root=Path(sys.argv[1]).resolve()
manifest=json.loads((root/'scripts/large-assets.json').read_text())
ids=json.loads(Path(__file__).with_name('asset-ids.json').read_text())
for a in manifest['assets']:
    if a['group']!='apk': continue
    p=root/a['path'];p.parent.mkdir(parents=True,exist_ok=True)
    def valid(file):
        if not file.is_file() or file.stat().st_size!=a['size']:return False
        with file.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()==a['sha256']
    if valid(p):continue
    asset_id=ids[p.name]
    part=p.with_name(p.name+'.part')
    subprocess.run(['curl','-fL','--retry','3','--connect-timeout','20','--max-time','180','-H','Accept: application/octet-stream',f'https://api.github.com/repos/ashmerra/wehavephones/releases/assets/{asset_id}','-o',str(part)],check=True)
    assert valid(part), 'Pinned upstream size/SHA256 mismatch: '+a['path']
    part.replace(p)
    print('Verified upstream asset:',a['path'],flush=True)
