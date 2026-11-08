#pragma once
#include "../util/util_flush.h"

namespace dxvk::lab {
  // Adapted from upstream 80fb7e22/a1456344 for the DXVK 2.3.1 tracker.
  // Explicit/synchronization flushes are never filtered here.
  class TilerFlushPolicy {
    bool m_enabled;
    bool m_pendingStrong = false;
  public:
    explicit TilerFlushPolicy(bool enabled) : m_enabled(enabled) { }
    bool enabled() const { return m_enabled; }
    bool suppressWeak(GpuFlushType type) const {
      return m_enabled && type == GpuFlushType::ImplicitWeakHint;
    }
    void missed(GpuFlushType type, bool hasPendingCommands) {
      if (m_enabled && hasPendingCommands && type == GpuFlushType::ImplicitStrongHint)
        m_pendingStrong = true;
    }
    bool boundary(bool hasPendingCommands) const {
      return m_enabled && m_pendingStrong && hasPendingCommands;
    }
    void submitted() { m_pendingStrong = false; }
  };
}
