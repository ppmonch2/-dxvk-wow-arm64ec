#!/usr/bin/env python3
"""Stage a built Wine 11 layer into an isolated WeHavePhones debug application."""
import copy
import hashlib
import json
import pathlib
import shutil
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(app, layer, wcp):
    gradle = app / 'app/build.gradle'
    text = gradle.read_text()
    assert text.count("applicationIdSuffix '.dev'") == 1
    text = text.replace("applicationIdSuffix '.dev'", "applicationIdSuffix '.p11lab'")
    text = text.replace("versionNameSuffix '-dev'", "versionNameSuffix '-p11lab'")
    gradle.write_text(text)
    for p in (app / 'app/src/wehavephonesDebug/res').glob('values*/strings.xml'):
        text = p.read_text().replace('WeHavePhones Dev', 'WeHavePhones P11 Lab')
        if p.parent.name == 'values':
            text = text.replace('</resources>',
                    '    <string name="wehavephones_first_run_intro">Prepare a test container for direct '
                    'WoW Forever launch. Battle.net is not required.</string>\n</resources>')
        p.write_text(text)
    # Forever is launched directly. The stock onboarding hides container tools
    # until Battle.net is installed; this lab is ready once its container is prepared.
    state = app / 'app/src/wehavephones/java/com/wehavephones/mobile/InitialSetupState.java'
    text = state.read_text()
    old = 'complete = completedBefore || (systemReady && hasContainer && battleNetInstalled);'
    assert text.count(old) == 1
    state.write_text(text.replace(old, 'complete = completedBefore || containerPrepared;'))
    assets = app / 'app/src/wehavephones/assets'
    manifest = assets / 'wehavephones/wehavephones-runtime-profiles.json'
    data = json.loads(manifest.read_text())
    profile = copy.deepcopy(data['profiles']['p10-ge34'])
    profile.update(description='EXPERIMENT: GE-Proton 11.0-9 ARM64EC. Native WoW copyable syscalls '
                   '(TEB+0x2f8), same 100 ms exit grace as Proton 10, Android file ownership fix. '
                   'Direct Forever launch only; tablet performance is not yet tested.',
                   wineVersion='proton-11.0-9-arm64ec')
    dest = assets / 'wehavephones/wine' / wcp.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(wcp, dest)
    profile['layer'] = dict(name=profile['wineVersion'], archive=wcp.name,
                            sizeLabel=f'{wcp.stat().st_size // (1024*1024)} MB', url='',
                            sha256=sha(wcp), asset='wehavephones/wine/' + wcp.name)
    profile['ntdll'] = []
    for suffix, source in [('dll', 'aarch64-windows/ntdll.dll'), ('so', 'aarch64-unix/ntdll.so')]:
        relative = 'ntdll/ntdll-wow-p11.' + suffix
        target = assets / 'wehavephones' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(layer / 'lib/wine' / source, target)
        profile['ntdll'].append(dict(asset=relative, sha256=sha(target),
                                   target='opt/{wineVersion}/lib/wine/' + source))
        if suffix == 'dll':
            profile['ntdll'].append(dict(asset=relative, sha256=sha(target),
                              target='container:.wine/drive_c/windows/system32/ntdll.dll'))
    profile['files'] = [f for f in profile['files'] if not f['asset'].startswith('server/')]
    server = assets / 'wehavephones/server/wineserver-wow-p11'
    server.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(layer / 'bin/wineserver', server)
    profile['files'].append(dict(asset='server/wineserver-wow-p11', target='opt/{wineVersion}/bin/wineserver',
                                 sha256=sha(server), executable=True))
    # One pinned runtime in this separate application: profile re-application keeps P11.
    data.update(mode='single', defaultProfile='p11-ge9-wow-lab', singleStageProfile='p11-ge9-wow-lab',
                profiles={'p11-ge9-wow-lab': profile})
    manifest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    # The upstream driver checker names the stock P10 profile explicitly.
    # Keep its full driver hash/revision checks, selecting this lab profile.
    checker = app / 'scripts/verify-wehavephones-turnip.py'
    text = checker.read_text()
    assert text.count('profiles["p10-ge34"]') == 1
    checker.write_text(text.replace('p10-ge34', 'p11-ge9-wow-lab'))
    # Refuse any accidental Wine 10 ntdll/server target in the final manifest.
    assert '10.0-34' not in manifest.read_text()
    print('Prepared com.wehavephones.p11lab; runtime and ntdll/server SHA-256 pinned')


if __name__ == '__main__':
    main(*(pathlib.Path(s).resolve() for s in sys.argv[1:]))
