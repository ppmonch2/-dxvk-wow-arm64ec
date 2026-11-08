"""Use a transparent custom pointer resolved by the root of the game area."""
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

app=Path(sys.argv[1]).resolve()
layout=app/'app/src/main/res/layout/xserver_display_activity.xml'
s=layout.read_text()
assert s.count('<FrameLayout\n')==s.count('</FrameLayout>')==1
layout.write_text(s.replace('<FrameLayout\n', '<com.wehavephones.widget.SessionPointerFrameLayout\n').replace('</FrameLayout>', '</com.wehavephones.widget.SessionPointerFrameLayout>'))
ET.parse(layout)
relative='app/src/main/java/com/wehavephones/widget/SessionPointerFrameLayout.java'
java=app/relative
assert not java.exists()
java.write_text(Path(__file__).with_name('SessionPointerFrameLayout.java').read_text())
subprocess.run(['git','-C',str(app),'add','--intent-to-add',relative],check=True)
subprocess.run(['git','-C',str(app),'diff','--check'],check=True)
changed=set(subprocess.check_output(['git','-C',str(app),'diff','--name-only'],text=True).splitlines())
assert changed=={relative,'app/src/main/res/layout/xserver_display_activity.xml'}, changed
print('Pointer v2: custom transparent icon from root resolver; layout and new class only')
