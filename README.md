# DXVK 2.3.1 — native ARM64 diagnostic build for WoW

This branch targets **native Windows ARM64 (PE machine 0xAA64)**, not ARM64EC.
The user's original WeHavePhones system32/dxgi.dll has machine 0xAA64 and SHA256
176f667e69a948d853082d1859a4d0b97bd84f607f01f159799e434fadba0471.
This establishes the architecture of that supplied DLL; the game EXE has not been inspected.

The previous ARM64EC experiment is retained in experiment/wow-custom-arm64ec-marker.
main is unchanged. Native ARM64 DLLs are a separate compatibility test.

Build uses upstream DXVK v2.3.1 at 037d0fa1ad093065b18dad968d5898cbcd143e0e
and LLVM-MinGW 20251104 with aarch64-w64-mingw32 compilers.
No performance patches or GPLAsync patches are added.

Runtime code prints WOW-CUSTOM-ARM64-NATIVE and the source commit ID in HUD and
separate d3d11/dxgi log calls. Both the public D3D11 entry path and internal
device creation path are marked. Build checks inspect the compiled DLLs.

See [TESTING-RU.md](TESTING-RU.md). Successful compilation is not a tablet runtime test.
