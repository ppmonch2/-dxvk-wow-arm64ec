package com.wehavephones.mobile;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;

/** Filesystem operations shared by the Android installer and host checks. */
public final class ReadbackFiles {
    private static final String[] NAMES = {"d3d11.dll", "dxgi.dll"};
    static String digest(byte[] bytes) throws Exception {
        byte[] sum = MessageDigest.getInstance("SHA-256").digest(bytes);
        StringBuilder b = new StringBuilder();
        for (byte x : sum) b.append(String.format(Locale.US, "%02x", x & 255));
        return b.toString();
    }
    static void install(File system32, File backup, byte[][] next) throws Exception {
        if (next.length != 2 || next[0] == null || next[1] == null) throw new IOException("Incomplete DLL pair");
        if (!backup.isDirectory() && !backup.mkdirs()) throw new IOException("Cannot create backup");
        byte[][] previous = new byte[2][];
        for (int i = 0; i < 2; i++) {
            File target = new File(system32, NAMES[i]);
            if (!target.isFile()) throw new IOException("Missing original " + target);
            previous[i] = Files.readAllBytes(target.toPath());
            File saved = new File(backup, digest(previous[i]) + "-" + NAMES[i]);
            if (!saved.exists()) Files.write(saved.toPath(), previous[i]);
        }
        try {
            for (int i = 0; i < 2; i++) {
                File target = new File(system32, NAMES[i]);
                if (Arrays.equals(previous[i], next[i])) continue;
                File staged = new File(system32, NAMES[i] + ".wow-rb-new");
                Files.write(staged.toPath(), next[i]);
                Files.move(staged.toPath(), target.toPath(), StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            }
            for (int i = 0; i < 2; i++)
                if (!Arrays.equals(next[i], Files.readAllBytes(new File(system32, NAMES[i]).toPath()))) throw new IOException("DLL read-back mismatch");
        } catch (Exception e) {
            for (int i = 0; i < 2; i++) Files.write(new File(system32, NAMES[i]).toPath(), previous[i]);
            throw e;
        }
    }
    static File export(File root, int id, String stamp) throws Exception {
        File[] dirs = root.listFiles(f -> f.isDirectory() && f.getName().startsWith("c" + id + "-"));
        if (dirs == null) throw new IOException("Журналы не найдены");
        Arrays.sort(dirs, Comparator.comparing(File::getName).reversed());
        File off = null, on = null;
        for (File dir : dirs) {
            File[] logs = dir.listFiles(f -> f.getName().endsWith("_d3d11.log") && f.length() > 0);
            if (logs == null || logs.length == 0) continue;
            if (off == null && dir.getName().endsWith("-off")) off = dir;
            if (on == null && dir.getName().endsWith("-on")) on = dir;
        }
        if (off == null || on == null) throw new IOException("Нужны журналы игры и для теста A, и для теста B");
        File result = new File(root, "results-c" + id + "-" + stamp + ".zip");
        long bytes = 0;
        try (ZipOutputStream zip = new ZipOutputStream(new FileOutputStream(result))) {
            for (File dir : new File[]{off, on}) {
                File[] files = dir.listFiles(f -> f.isFile() && (f.getName().endsWith(".log") || f.getName().equals("RUN_INFO.txt")));
                if (files == null) continue;
                for (File file : files) {
                    zip.putNextEntry(new ZipEntry(dir.getName() + "/" + file.getName()));
                    try (InputStream input = new FileInputStream(file)) {
                        byte[] buffer = new byte[32768]; int n;
                        while ((n = input.read(buffer)) != -1) {
                            bytes += n;
                            if (bytes > 100L*1024*1024) throw new IOException("Журналы больше 100 МБ");
                            zip.write(buffer, 0, n);
                        }
                    }
                    zip.closeEntry();
                }
            }
        } catch (Exception e) { result.delete(); throw e; }
        return result;
    }
}
