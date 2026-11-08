#include "dxvk/tiler_flush_policy.h"
#include <cassert>
#include <iostream>
using dxvk::GpuFlushType;
using dxvk::lab::TilerFlushPolicy;
int main() {
  TilerFlushPolicy off(false), on(true);
  for (auto type : {GpuFlushType::ExplicitFlush, GpuFlushType::ImplicitSynchronization,
                   GpuFlushType::ImplicitStrongHint, GpuFlushType::ImplicitWeakHint}) {
    assert(!off.suppressWeak(type));
    assert(on.suppressWeak(type) == (type == GpuFlushType::ImplicitWeakHint));
    off.missed(type, true);
    assert(!off.boundary(true));
  }
  // Weak hints alone must not create forced boundary submissions.
  on.missed(GpuFlushType::ImplicitWeakHint, true);
  assert(!on.boundary(true));
  on.missed(GpuFlushType::ImplicitStrongHint, false);
  assert(!on.boundary(true));
  on.missed(GpuFlushType::ImplicitStrongHint, true);
  assert(!on.boundary(false));
  assert(on.boundary(true));
  // State remains pending until ExecuteFlush really submits commands.
  assert(on.boundary(true));
  on.submitted();
  assert(!on.boundary(true));
  on.missed(GpuFlushType::ImplicitStrongHint, true);
  on.submitted(); // Also clears on mandatory Map, explicit Flush or Present.
  assert(!on.boundary(true));
  std::cout << "Tiler policy: off mode, mandatory sync, pending strong hints and submission reset PASS\n";
}
