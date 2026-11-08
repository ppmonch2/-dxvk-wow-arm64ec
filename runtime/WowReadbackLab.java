package com.wehavephones.mobile;

import android.app.Activity;
import android.content.Context;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;
import com.wehavephones.R;
import com.wehavephones.XServerDisplayActivity;
import com.wehavephones.container.Container;
import com.wehavephones.core.EnvVars;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/** Only packaged into the P11 Lab experiment. No writes to another application's prefix. */
public final class WowReadbackLab {
    private static final String[] NAMES = {"d3d11.dll", "dxgi.dll"};
    private static final String[] CUSTOM = {
        "a85a0671b6ee6cbba583c840b7cccfda7e63b9da21100ab508062bd5a262eff9",
        "c37f3540f5c870e4b19bdc77a7d72e8f2c7ab8ddbc44da13eebaabdc89c7ac15"};
    private static final String[] STOCK = {
        "5e3cf0b8075e5eed7ef2eb635eb91875573dfc47d42f15dca3a6626db00d2c0d",
        "176f667e69a948d853082d1859a4d0b97bd84f607f01f159799e434fadba0471"};
    private static String stamp() { return new SimpleDateFormat("yyyyMMdd-HHmmss-SSS", Locale.US).format(new Date()); }
    private static boolean busy() {
        XServerDisplayActivity active = XServerDisplayActivity.getActiveInstance();
        return (active != null && active.isSessionActive()) || ProcessScanner.isWineSessionRunning();
    }
    private static int mode(Context c, Container container) {
        int value = c.getSharedPreferences("wow_readback_lab", Context.MODE_PRIVATE).getInt("mode_" + container.id, 0);
        return value >= 0 && value <= 2 ? value : 0;
    }
    private static File driveD(Container container) throws IOException {
        for (String[] drive : container.drivesIterator())
            if ("D".equalsIgnoreCase(drive[0])) return new File(drive[1]);
        throw new IOException("В контейнере не настроен диск D:");
    }
    private static File logsRoot(Container container) throws IOException {
        File root = new File(driveD(container), "WoW-RB-logs");
        if (!root.isDirectory() && !root.mkdirs()) throw new IOException("Нет доступа к " + root);
        return root;
    }
    public static void bind(Activity activity, View view) {
        Container container = WeHavePhonesContainers.resolve(activity);
        Spinner spinner = view.findViewById(R.id.SPReadbackLab);
        TextView hint = view.findViewById(R.id.TVReadbackLab);
        spinner.setOnItemSelectedListener(null);
        ArrayAdapter<String> adapter = new ArrayAdapter<>(activity, R.layout.wehavephones_spinner_item,
            new String[]{"Штатный DXVK (возврат)", "Тест A: ранняя отправка ВЫКЛ", "Тест B: ранняя отправка ВКЛ"});
        adapter.setDropDownViewResource(R.layout.wehavephones_spinner_dropdown_item);
        spinner.setAdapter(adapter);
        spinner.setEnabled(container != null);
        if (container != null) spinner.setSelection(mode(activity, container), false);
        hint.setText("Сначала закрой игру и контейнер. Выбери A или B, затем запусти игру напрямую. "
            + "DLL устанавливаются при старте контейнера; логи — D:\\WoW-RB-logs. Кэши не очищай.");
        spinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            public void onNothingSelected(AdapterView<?> p) {}
            public void onItemSelected(AdapterView<?> p, View v, int selected, long id) {
                if (container == null || selected == mode(activity, container)) return;
                if (busy()) {
                    Toast.makeText(activity, "Сначала полностью закрой контейнер", Toast.LENGTH_LONG).show();
                    spinner.setSelection(mode(activity, container), false);
                    return;
                }
                activity.getSharedPreferences("wow_readback_lab", Context.MODE_PRIVATE).edit()
                    .putInt("mode_" + container.id, selected).apply();
                Toast.makeText(activity, "Режим сохранён. Открой контейнер и запусти игру", Toast.LENGTH_LONG).show();
            }
        });
        view.findViewById(R.id.BTReadbackExport).setOnClickListener(v -> {
            if (container == null || busy()) {
                Toast.makeText(activity, "Сначала полностью закрой контейнер", Toast.LENGTH_LONG).show();
                return;
            }
            new Thread(() -> {
                String message;
                try { message = "ZIP сохранён: " + export(container).getAbsolutePath(); }
                catch (Exception e) { message = "Экспорт: " + e.getMessage(); }
                final String text = message;
                activity.runOnUiThread(() -> { hint.setText(text); Toast.makeText(activity, text, Toast.LENGTH_LONG).show(); });
            }, "wow-rb-export").start();
        });
    }
    /** Runs after stock wrapper extraction, before the Wine process is started. */
    public static void prepare(Context context, Container container, EnvVars env) throws Exception {
        if (container == null) return;
        if (ProcessScanner.isWineSessionRunning()) throw new IOException("Wine уже запущен: замена DLL отменена");
        int selected = mode(context, container);
        String label = selected == 0 ? "stock" : selected == 1 ? "off" : "on";
        byte[][] next = new byte[2][];
        File system32 = new File(container.getRootDir(), ".wine/drive_c/windows/system32");
        File backup = new File(container.getRootDir(), ".wine/wow-rb-backup");
        if (!system32.isDirectory()) throw new IOException("Нет system32 в тестовом контейнере");
        if (!backup.isDirectory() && !backup.mkdirs()) throw new IOException("Не создать резервную папку");
        for (int i = 0; i < 2; i++) {
            try (InputStream input = context.getAssets().open("wehavephones/readback/" + (selected == 0 ? "stock/" : "payload/") + NAMES[i])) {
                ByteArrayOutputStream output = new ByteArrayOutputStream();
                byte[] buffer = new byte[32768]; int n;
                while ((n = input.read(buffer)) != -1) output.write(buffer, 0, n);
                next[i] = output.toByteArray();
            }
            if (!ReadbackFiles.digest(next[i]).equals((selected == 0 ? STOCK : CUSTOM)[i])) throw new IOException("SHA-256: " + NAMES[i]);
        }
        // Prepare persistent log paths before changing either DLL.
        File root = logsRoot(container);
        File session = new File(root, "c" + container.id + "-" + stamp() + "-" + label);
        if (!session.mkdirs()) throw new IOException("Не создать папку журнала");
        File cache = new File(driveD(container), "WoW-DXVK-test-cache");
        if (!cache.isDirectory() && !cache.mkdirs()) throw new IOException("Не создать кэш");
        ReadbackFiles.install(system32, backup, next);
        env.put("WINEDEBUG", "-all");
        env.put("DXVK_ASYNC", selected == 0 ? "0" : "1");
        env.put("WOW_DXVK_DEDUP", "1"); env.put("WOW_DXVK_WORKERS", "4");
        env.put("WOW_DXVK_METRICS", selected == 0 ? "0" : "1");
        env.put("WOW_DXVK_WAITS", selected == 0 ? "0" : "1");
        env.put("WOW_DXVK_EARLY_READBACK", selected == 2 ? "1" : "0");
        env.put("DXVK_HUD", "version,fps,frametimes"); env.put("DXVK_LOG_LEVEL", "info");
        env.put("DXVK_STATE_CACHE_PATH", "D:\\WoW-DXVK-test-cache");
        env.put("DXVK_LOG_PATH", "D:\\WoW-RB-logs\\" + session.getName());
        String info = "wine=" + container.getWineVersion() + "\nmode=" + label + "\nDXVK_source=9f30f7325564360345225db5917bfc9daa4ffb50\n"
            + "d3d11=" + ReadbackFiles.digest(next[0]) + "\ndxgi=" + ReadbackFiles.digest(next[1]) + "\n";
        Files.write(new File(session, "RUN_INFO.txt").toPath(), info.getBytes(java.nio.charset.StandardCharsets.UTF_8));
    }
    private static File export(Container container) throws Exception {
        return ReadbackFiles.export(logsRoot(container), container.id, stamp());
    }
}
