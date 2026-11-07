#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tlhelp32.h>
#include <wincrypt.h>
#include <stdio.h>
#include <wchar.h>
#include <string.h>

static const wchar_t *names[2] = {L"d3d11.dll", L"dxgi.dll"};
static const char *custom[2] = {
  "3e38c0c6eda66eb98beaeb807b52908a884e736aeb9a5a274297154ce60032bf",
  "0fad624223a1d9feaa7dc412d2866238c5bc1fadb40f178b05f205a64c4b5e05"};
static const char *stock[2] = {
  "5e3cf0b8075e5eed7ef2eb635eb91875573dfc47d42f15dca3a6626db00d2c0d",
  "176f667e69a948d853082d1859a4d0b97bd84f607f01f159799e434fadba0471"};

static int path(wchar_t *out, const wchar_t *dir, const wchar_t *name) {
  return swprintf(out, MAX_PATH, L"%ls\\%ls", dir, name) > 0;
}

static int hash_file(const wchar_t *file, char out[65]) {
  HCRYPTPROV prov = 0; HCRYPTHASH hash = 0;
  HANDLE h = INVALID_HANDLE_VALUE; BYTE buf[16384], digest[32];
  DWORD got, size = sizeof(digest); int ok = 0;
  if (!CryptAcquireContextW(&prov, NULL, NULL, PROV_RSA_AES, CRYPT_VERIFYCONTEXT)) goto end;
  if (!CryptCreateHash(prov, CALG_SHA_256, 0, 0, &hash)) goto end;
  h = CreateFileW(file, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
  if (h == INVALID_HANDLE_VALUE) goto end;
  for (;;) {
    if (!ReadFile(h, buf, sizeof(buf), &got, NULL)) goto end;
    if (!got) break;
    if (!CryptHashData(hash, buf, got, 0)) goto end;
  }
  if (!CryptGetHashParam(hash, HP_HASHVAL, digest, &size, 0)) goto end;
  for (DWORD i = 0; i < size; i++) sprintf(out + 2 * i, "%02x", digest[i]);
  out[64] = 0; ok = 1;
end:
  if (h != INVALID_HANDLE_VALUE) CloseHandle(h);
  if (hash) CryptDestroyHash(hash);
  if (prov) CryptReleaseContext(prov, 0);
  return ok;
}

static int matches(const wchar_t *file, const char *expected) {
  char actual[65]; return hash_file(file, actual) && !strcmp(actual, expected);
}

static int game_running(void) {
  PROCESSENTRY32W p; p.dwSize = sizeof(p);
  HANDLE h = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
  if (h == INVALID_HANDLE_VALUE) return 1;
  int found = 0;
  if (!Process32FirstW(h, &p)) { CloseHandle(h); return 1; }
  do {
    if (!_wcsnicmp(p.szExeFile, L"Wow", 3)) { found = 1; break; }
  } while (Process32NextW(h, &p));
  CloseHandle(h); return found;
}

int wmain(int argc, wchar_t **argv) {
  wchar_t base[MAX_PATH], target[MAX_PATH], backup[MAX_PATH], temp[MAX_PATH];
  wchar_t src[2][MAX_PATH], dst[2][MAX_PATH], old[2][MAX_PATH], snap[2][MAX_PATH];
  char previous[2][65];
  if (argc != 2 || (wcscmp(argv[1], L"install") && wcscmp(argv[1], L"restore") && wcscmp(argv[1], L"status"))) {
    puts("Usage: dxvk-test.exe install | restore | status"); return 2;
  }
  if (!GetModuleFileNameW(NULL, base, MAX_PATH)) return 2;
  wchar_t *slash = wcsrchr(base, L'\\'); if (!slash) return 2; *slash = 0;
  if (!GetSystemDirectoryW(target, MAX_PATH)) return 2;
  wcscpy(backup, L"C:\\DXVK-backup");
#ifdef TESTING
  /* Compiled ONLY into the unpublished Windows smoke-test executable. */
  if (!GetEnvironmentVariableW(L"WOW_DXVK_TEST_TARGET", target, MAX_PATH) ||
      !GetEnvironmentVariableW(L"WOW_DXVK_TEST_BACKUP", backup, MAX_PATH)) return 2;
#endif
  path(temp, base, L"rollback");
  int status = !wcscmp(argv[1], L"status");
  int restore = !wcscmp(argv[1], L"restore");
  for (int i = 0; i < 2; i++) {
    wchar_t folder[MAX_PATH]; path(folder, base, L"payload");
    path(src[i], folder, names[i]); path(dst[i], target, names[i]);
    path(old[i], backup, names[i]); path(snap[i], temp, names[i]);
    if (status) {
      char sum[65];
      if (!hash_file(dst[i], sum)) { wprintf(L"Cannot read %ls\n", dst[i]); return 1; }
      printf("%s %s\n", i ? "dxgi.dll" : "d3d11.dll", sum);
    }
  }
  if (status) return 0;
  if (game_running()) { puts("Close WoW and addon apps before replacing DLLs."); return 1; }
  for (int i = 0; i < 2; i++) {
    if (!matches(old[i], stock[i])) {
      puts("Verified stock backups required in C:\\DXVK-backup. See START-RU.md; TEST container only."); return 1;
    }
    if (!restore && !matches(src[i], custom[i])) {
      puts("Payload checksum mismatch. Use the verified bcec80c1e075 DLL pair."); return 1;
    }
    if (!hash_file(dst[i], previous[i]) ||
        (strcmp(previous[i], stock[i]) && strcmp(previous[i], custom[i]))) {
      puts("Unknown target DLL. Refusing to overwrite another build."); return 1;
    }
  }
  if (!CreateDirectoryW(temp, NULL) && GetLastError() != ERROR_ALREADY_EXISTS) return 1;
  for (int i = 0; i < 2; i++) {
    if (!CopyFileW(dst[i], snap[i], FALSE) || !matches(snap[i], previous[i])) {
      puts("Cannot snapshot both current DLLs. No changes made."); return 1;
    }
  }
  int changed = 0;
  for (int i = 0; i < 2; i++) {
    const wchar_t *source = restore ? old[i] : src[i];
    const char *expected = restore ? stock[i] : custom[i];
    changed = i + 1;
    if (!CopyFileW(source, dst[i], FALSE)) goto rollback;
    if (!matches(dst[i], expected)) goto rollback;
  }
  puts(restore ? "Stock DLL pair restored and verified." : "Custom ARM64 pair bcec80c1e075 installed and verified.");
  return 0;
rollback:
  printf("Install failed (Windows error %lu). Rolling back changed files.\n", GetLastError());
  for (int i = 0; i < changed; i++) {
    if (!matches(dst[i], previous[i]) &&
        (!CopyFileW(snap[i], dst[i], FALSE) || !matches(dst[i], previous[i])))
      wprintf(L"ROLLBACK FAILED: restore %ls manually from %ls\n", dst[i], snap[i]);
  }
  return 1;
}
