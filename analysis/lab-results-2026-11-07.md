# LAB runtime result: no reported improvement

User reports unchanged camera/movement stutter and unsatisfactory FPS.
The logs confirm build 5d1041de0774 in both modules, async=1, four compiler
workers, dedup=1, and execution of the async scheduling path.

81 reporting windows (~405 seconds) were supplied. 939 background tasks were
queued and completed; 23 duplicate High submissions were suppressed.

A 14-window span (~70 seconds) held queued_total=completed_total=938 and pending=0.
Across this span ~31.6% of Present-entry intervals exceeded 50 ms. Window p95 was
71–85 ms; mean interval ranged 28.1–34.0 ms. Mean CPU time inside D3D11 Present
was only 2.47–4.80 ms per window. These are per-window percentiles, not a session p95.

This demonstrates sustained stutter without new background compiler work.
It does not rule out synchronous compilation or establish CPU-vs-GPU limitation.
The unmeasured time includes game work, other D3D11 calls and the outer DXGI path.
The final ~5 FPS windows may represent background/focus behavior and are not
used to characterize normal in-world performance without further context.

The next trial adds CPU timing of Map, CS synchronization and resource waits,
plus an outer DXGI Present boundary and lock-acquisition timers. It does not
remove waits/barriers, and claims no acceleration. Timers are explicitly optional.
Automatic installation from bundled stock originals is retained.
