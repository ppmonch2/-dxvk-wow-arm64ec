package com.wehavephones.mobile;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.ZipFile;

public final class ReadbackFilesTest {
    static void check(boolean value) { if (!value) throw new AssertionError(); }
    static void put(File root, String name, String value) throws Exception {
        File f = new File(root, name); f.getParentFile().mkdirs(); Files.write(f.toPath(), value.getBytes("UTF-8"));
    }
    public static void main(String[] args) throws Exception {
        File root = Files.createTempDirectory("readback-lab-check").toFile();
        File dlls = new File(root, "system32"), backup = new File(root, "backup");
        put(dlls, "d3d11.dll", "unknown original d3d11"); put(dlls, "dxgi.dll", "unknown original dxgi");
        byte[][] next = {"new d3d11".getBytes("UTF-8"), "new dxgi".getBytes("UTF-8")};
        ReadbackFiles.install(dlls, backup, next);
        check(Arrays.equals(Files.readAllBytes(new File(dlls, "d3d11.dll").toPath()), next[0]));
        check(backup.listFiles().length == 2);
        ReadbackFiles.install(dlls, backup, next); // repeated startup must not lose original snapshots
        check(backup.listFiles().length == 4);
        ReadbackFiles.install(dlls, backup, next); check(backup.listFiles().length == 4);
        File missing = new File(root, "missing"); put(missing, "d3d11.dll", "keep me");
        try { ReadbackFiles.install(missing, backup, next); throw new AssertionError(); }
        catch (IOException expected) {}
        check(new String(Files.readAllBytes(new File(missing,"d3d11.dll").toPath()),"UTF-8").equals("keep me"));
        // Force the second staging write to fail. The first replaced DLL must roll back.
        File blocked = new File(dlls, "dxgi.dll.wow-rb-new"); blocked.mkdir();
        try { ReadbackFiles.install(dlls, backup, new byte[][]{"bad first".getBytes(),"bad second".getBytes()}); throw new AssertionError(); }
        catch (IOException expected) {}
        check(Arrays.equals(Files.readAllBytes(new File(dlls,"d3d11.dll").toPath()),next[0]));
        check(Arrays.equals(Files.readAllBytes(new File(dlls,"dxgi.dll").toPath()),next[1]));
        File logs = new File(root, "logs");
        put(logs, "c1-001-off/Wow-ARM64_d3d11.log", "A");
        put(logs, "c1-002-on/Wow-ARM64_d3d11.log", "B");
        put(logs, "c1-003-on/RUN_INFO.txt", "empty later desktop session");
        put(logs, "c2-999-on/Wow-ARM64_d3d11.log", "other container");
        try (ZipFile zip = new ZipFile(ReadbackFiles.export(logs, 1, "check"))) {
            check(zip.size() == 2);
            check(zip.getEntry("c1-001-off/Wow-ARM64_d3d11.log") != null);
            check(zip.getEntry("c1-002-on/Wow-ARM64_d3d11.log") != null);
        }
        try { ReadbackFiles.export(logs, 2, "missing-pair"); throw new AssertionError(); }
        catch (IOException expected) {}
        System.out.println("Readback file checks passed: backups, idempotence, missing pair, partial failure rollback, latest A/B export");
    }
}
