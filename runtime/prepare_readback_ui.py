#!/usr/bin/env python3
"""Integrate the verified RB binary pair and persistent A/B controls in P11 Lab."""
import hashlib
import json
import pathlib
import shutil
import sys


def replace(path, before, after):
    text = path.read_text()
    assert text.count(before) == 1, str(path)
    path.write_text(text.replace(before, after))


def main(app, rb):
    main_java = app / 'app/src/main/java/com/wehavephones'
    helper = main_java / 'mobile/WowReadbackLab.java'
    helper.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pathlib.Path(__file__).with_name('WowReadbackLab.java'), helper)
    shutil.copyfile(pathlib.Path(__file__).with_name('ReadbackFiles.java'), helper.with_name('ReadbackFiles.java'))
    replace(main_java / 'XServerDisplayActivity.java',
            '        guestProgramLauncherComponent.setEnvVars(envVars);',
            '''        try {
            com.wehavephones.mobile.WowReadbackLab.prepare(this, container, envVars);
        } catch (Exception e) {
            Log.e(TAG_GUEST_DEBUG, "Readback lab preparation failed", e);
            runOnUiThread(() -> {
                android.widget.Toast.makeText(this, "DXVK: " + e.getMessage(), android.widget.Toast.LENGTH_LONG).show();
                finish();
            });
            return;
        }
        guestProgramLauncherComponent.setEnvVars(envVars);''')
    java = app / 'app/src/wehavephones/java/com/wehavephones/mobile/SetupFragment.java'
    replace(java, '        refreshContainers();\n        importHandler.post(refreshImport);',
            '        refreshContainers();\n        WowReadbackLab.bind(activity, getView());\n        importHandler.post(refreshImport);')
    replace(java, '                WeHavePhonesContainers.remember(activity, container);',
            '                WeHavePhonesContainers.remember(activity, container);\n                WowReadbackLab.bind(activity, getView());')
    xml = app / 'app/src/wehavephones/res/layout/fragment_wehavephones_setup.xml'
    anchor = '            android:textSize="26sp" />'
    replace(xml, anchor, anchor + '''
        <LinearLayout
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:orientation="vertical" android:padding="12dp"
            android:background="@drawable/wehavephones_card_background">
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="DXVK: проверка плавности" android:textSize="18sp"
                android:textColor="@color/wehavephones_text_title" />
            <Spinner android:id="@+id/SPReadbackLab" android:layout_width="match_parent"
                android:layout_height="48dp" android:background="@drawable/wehavephones_dropdown" />
            <TextView android:id="@+id/TVReadbackLab" style="@style/WeHavePhonesHint"
                android:layout_width="match_parent" android:layout_height="wrap_content" />
            <Button android:id="@+id/BTReadbackExport" style="@style/WeHavePhonesButtonOutline"
                android:layout_width="wrap_content" android:layout_height="wrap_content"
                android:text="Сохранить результаты A + B в ZIP" />
        </LinearLayout>''')
    replace(app / 'app/build.gradle', "versionNameSuffix '-p11lab'", "versionNameSuffix '-p11lab-rb'")
    base = app / 'app/src/wehavephones/assets/wehavephones/readback'
    hashes = {}
    for folder in ('stock', 'payload'):
        for name in ('d3d11.dll', 'dxgi.dll'):
            source = rb / folder / name
            target = base / folder / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            hashes[folder + '/' + name] = hashlib.sha256(target.read_bytes()).hexdigest()
    (base / 'SHA256.json').write_text(json.dumps(hashes, indent=2))
    custom = json.loads((rb / 'SHA256-PAYLOAD.json').read_text())
    for name, digest in custom.items():
        assert hashes['payload/' + name] == digest
        assert digest in helper.read_text()
    shutil.copyfile(rb / 'LICENSE-DXVK', base / 'LICENSE-DXVK')
    # Preserve the complete DXVK patch and build provenance alongside the APK.
    print('Prepared readback A/B UI, per-container modes, startup DLL verification and persistent logs')


if __name__ == '__main__':
    main(*(pathlib.Path(s).resolve() for s in sys.argv[1:]))
