# DXVK 2.3.1 ARM64 — GPLAsync experiment

This branch changes pipeline compilation code using the version-matched
Ph42oN GPLAsync 2.3.1-1 patch, on upstream commit
037d0fa1ad093065b18dad968d5898cbcd143e0e. Native ARM64 (0xAA64), not ARM64EC.

The existing baseline bcec80c1e075 is retained in experiment/wow-custom-arm64-native.
Main remains untouched. Changes: explicit async opt-in/out, disabled separate GPLAsync
cache option, atomic shared compiler flag, and one-time async execution diagnostics.

The package includes a checksum-verified installer, original rollback pair,
play-async-on.bat and play-async-off.bat for the SAME compiled DLLs.
Compiled DLL import/export tables must match the proven original ARM64 libraries.
Windows CI tests install, restore, upgrade from baseline and failure handling.

[Instructions](TESTING-RU.md) · [Patch provenance](patches/PROVENANCE.md)

No tablet performance or stability improvement is claimed before runtime testing.
Async may omit draws while their pipelines are being compiled. Its primary target
is shader compilation stalls, not the steady-state 32–35 FPS limit.
