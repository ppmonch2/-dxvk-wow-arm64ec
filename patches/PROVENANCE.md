# GPLAsync provenance

- Source: https://gitlab.com/Ph42oN/dxvk-gplasync
- Source repository commit: 04e50ed2c4dee43e64d30119b2c5b26a23e2b6a4
- File: patches/dxvk-gplasync-2.3.1-1.patch
- Patch author: Ph42oN, based on Sporif/dxvk-async.
- Patch SHA256: 7d82eaa170e16d26ed653738bb14fcff91b26d3782298299bb55254946d71e72
- Base DXVK v2.3.1: 037d0fa1ad093065b18dad968d5898cbcd143e0e

The source patch is retained unchanged. Local adjustments are in apply_async.py:
async explicitly selected via DXVK_ASYNC=1/0 (default off), GPLAsync-cache disabled,
shared m_async flag made atomic, diagnostic options and first-job logging added,
and diagnostic log records flushed. The combined applied diff is shipped.

When enabled, async can skip draws while compatible pipelines are compiling.
This may reduce compilation stalls but can cause temporary visual omissions.
This is a test build, not a claim of improved mean FPS or proven game compatibility.
