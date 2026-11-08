package com.wehavephones.widget;

import android.content.Context;
import android.graphics.Bitmap;
import android.util.AttributeSet;
import android.util.Log;
import android.view.InputDevice;
import android.view.MotionEvent;
import android.view.PointerIcon;
import android.widget.FrameLayout;
import android.widget.Toast;

/** Session-only host pointer replacement; X11/game cursor is rendered separately. */
public final class SessionPointerFrameLayout extends FrameLayout {
    private final PointerIcon transparentPointer;
    private boolean mouseResolutionReported;

    public SessionPointerFrameLayout(Context context) {
        this(context, null);
    }

    public SessionPointerFrameLayout(Context context, AttributeSet attrs) {
        this(context, attrs, 0);
    }

    public SessionPointerFrameLayout(Context context, AttributeSet attrs, int defStyleAttr) {
        super(context, attrs, defStyleAttr);
        Bitmap pixels = Bitmap.createBitmap(32, 32, Bitmap.Config.ARGB_8888);
        pixels.eraseColor(android.graphics.Color.TRANSPARENT);
        transparentPointer = PointerIcon.create(pixels, 0, 0);
    }

    @Override
    public PointerIcon onResolvePointerIcon(MotionEvent event, int pointerIndex) {
        if (event.isFromSource(InputDevice.SOURCE_MOUSE)
                || event.getToolType(pointerIndex) == MotionEvent.TOOL_TYPE_MOUSE) {
            if (!mouseResolutionReported) {
                mouseResolutionReported = true;
                Log.i("WHP_POINTER", "v2: session resolved a transparent custom mouse icon");
                post(() -> Toast.makeText(getContext(), "Mouse fix v2: transparent pointer",
                        Toast.LENGTH_SHORT).show());
            }
            // Resolve here, before child overlays can supply a different pointer.
            // TYPE_CUSTOM takes Android's custom-icon path, unlike TYPE_NULL.
            return transparentPointer;
        }
        return super.onResolvePointerIcon(event, pointerIndex);
    }
}
