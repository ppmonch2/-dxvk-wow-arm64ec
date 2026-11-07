# DXVK 2.3.1 ARM64 LAB

Native ARM64 test build with compatible GPLAsync, optional high-priority pipeline
job coalescing, optional compiler worker caps, and five-second CPU Present/worker
summaries. Main and earlier diagnostic/async branches remain unchanged.

[Trial instructions and measurement limits](TESTING-RU.md)

All behavior changes have explicit switches. Profiles isolate async, coalescing
and a cap of four compiler workers. Metrics are optional and never write per frame.
High-priority keys include both pipeline identity and the entire pipeline state;
low/normal work is intentionally not coalesced. Completed keys are removed under
the existing queue lock, so future requests can retry normally.

CI tests histogram math, distinct pipeline/state identity and concurrent duplicate
submission to the pending-key registry. It compiles ARM64 DLLs, audits imports and
exports, and tests deployment/rollback on Windows, including both earlier builds.
This does not execute the graphics code on a GPU or establish tablet performance.

[Patch origin](patches/PROVENANCE.md). No APK, driver, FEX or working container changes.
