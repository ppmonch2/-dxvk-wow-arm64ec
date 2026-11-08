"""Hide Android's mouse pointer only on the session views; preserve X11 cursor."""
from pathlib import Path
import subprocess
import sys

app=Path(sys.argv[1]).resolve()
p=app/'app/src/main/java/com/wehavephones/XServerDisplayActivity.java'
s=p.read_text()
before='''        rootView.addView(inputControlsView);
'''
after=before+'''
        // Android's host pointer duplicates the cursor rendered by X11/WoW.
        // Apply to these session instances only: drawers, dialogs and editors
        // retain their normal Android pointer behaviour.
        final android.view.PointerIcon hiddenAndroidPointer = android.view.PointerIcon.getSystemIcon(
                this, android.view.PointerIcon.TYPE_NULL);
        rootView.setPointerIcon(hiddenAndroidPointer);
        xServerView.setPointerIcon(hiddenAndroidPointer);
        touchpadView.setPointerIcon(hiddenAndroidPointer);
        inputControlsView.setPointerIcon(hiddenAndroidPointer);
'''
assert s.count(before)==1, 'Unexpected session UI layout'
p.write_text(s.replace(before,after))
subprocess.run(['git','-C',str(app),'diff','--check'],check=True)
print('Patched four session view instances; GLRenderer and input handling unchanged')
