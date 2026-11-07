# WAIT runtime observations

Both modules confirm a0080307388c, async=1 and optional CPU wait probes enabled.
23 paired windows are aligned by at_us; the last paired timestamps differ by ~0.13 ms.

Between d3d11 windows 10 and 22 (60.350811 seconds):
- Map calls increased by 533; cumulative Map duration increased by 26.247596 s.
- Resource waits increased by 533 and 25.722391 s: mean 48.2596 ms per call.
- CS synchronization time increased by only 0.522329 s.
- Background compiler tasks increased by 93 and were completed at the final snapshot.
- Query GetData calls increased by 69669, including 61389 S_FALSE results.

The observed maximum single resource wait was 95.478 ms. DXGI window+buffer lock
acquisition totals over the entire run were 47+48 microseconds. The earlier
speculation about outer Present locks is not supported by these measurements.

This identifies resource synchronization as a substantial measured wait. The
old probes did not identify MapType, resource size or usage, so those are added
alongside an opt-in early staging-readback submission experiment. It may help
only if eligible copies precede Map by enough useful CPU work; a GPU-bound or
immediate read-after-copy path may not improve. No wait/barrier is removed.
