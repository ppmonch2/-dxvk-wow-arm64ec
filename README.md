# DXVK WoW ARM64EC — baseline build scaffold

This is a **build workflow**, not a compiled or optimized DXVK package.

- Target: DXVK upstream v2.3.1, ARM64EC.
- Important: upstream v2.3.1 **does not contain the GPLAsync patches** used by the current WeHavePhones binary. The output is therefore NOT a drop-in replacement.
- Purpose: establish a reproducible baseline compiler/toolchain before integrating a version-compatible GPLAsync patch and any game-specific change.
- Use GitHub Actions → Actions → DXVK ARM64EC baseline build → Run workflow in your own repository.
- Build has NOT been executed or validated here because network access to GitHub is unavailable from the build environment.
- Do NOT install resulting DLLs into your working WeHavePhones container yet.
