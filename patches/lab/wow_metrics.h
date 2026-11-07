#pragma once
#include "lab_stats.h"
#include "dxvk_include.h"
#include <atomic>
#include <chrono>
#include <mutex>

namespace dxvk::lab {
  using Clock = std::chrono::steady_clock;
  inline bool metricsEnabled() {
    static const bool value = env::getEnvVar("WOW_DXVK_METRICS") == "1";
    return value;
  }
  struct WorkerCounters {
    std::atomic<uint64_t> queued {0}, completed {0}, duplicates {0};
    std::atomic<uint64_t> waitUs {0}, workerUs {0}, queuePeak {0};
  };
  inline WorkerCounters counters;
  inline void noteQueue(uint64_t depth) {
    if (!metricsEnabled()) return;
    counters.queued.fetch_add(1, std::memory_order_relaxed);
    auto old = counters.queuePeak.load(std::memory_order_relaxed);
    while (old < depth && !counters.queuePeak.compare_exchange_weak(old, depth,
             std::memory_order_relaxed, std::memory_order_relaxed)) { }
  }
  inline void noteDuplicate() {
    if (metricsEnabled()) counters.duplicates.fetch_add(1, std::memory_order_relaxed);
  }
  inline void noteWorker(Clock::time_point queued, Clock::time_point started) {
    if (!metricsEnabled()) return;
    auto finished = Clock::now();
    counters.waitUs.fetch_add(std::chrono::duration_cast<std::chrono::microseconds>(started - queued).count(), std::memory_order_relaxed);
    counters.workerUs.fetch_add(std::chrono::duration_cast<std::chrono::microseconds>(finished - started).count(), std::memory_order_relaxed);
    counters.completed.fetch_add(1, std::memory_order_relaxed);
  }

  // CPU Present entry intervals and CPU duration of Present calls.
  // These are NOT GPU render times or physical display scan-out times.
  class FrameMetrics {
    bool enabled = metricsEnabled();
    dxvk::mutex mutex;
    Clock::time_point lastStart { }, windowStart { };
    FrameHistogram intervals, presentCalls;
    void record(Clock::time_point start, Clock::time_point end) {
      std::lock_guard lock(mutex);
      if (windowStart == Clock::time_point()) windowStart = start;
      if (lastStart != Clock::time_point() && start > lastStart)
        intervals.add(std::chrono::duration<double, std::milli>(start - lastStart).count());
      if (start > lastStart) lastStart = start;
      presentCalls.add(std::chrono::duration<double, std::milli>(end - start).count());
      if (end - windowStart < std::chrono::seconds(5)) return;
      uint64_t queued = counters.queued.load(std::memory_order_relaxed);
      uint64_t completed = counters.completed.load(std::memory_order_relaxed);
      Logger::info(str::format("WOW_METRICS intervals=", intervals.count,
        " mean_ms=", intervals.mean(), " p95_ms=", intervals.percentile(95),
        " p99_ms=", intervals.percentile(99), " worst_ms=", intervals.maxMs,
        " over50=", intervals.over50, " over100=", intervals.over100,
        " overflow=", intervals.overflow, " present_mean_ms=", presentCalls.mean(),
        " present_max_ms=", presentCalls.maxMs, " queued_total=", queued,
        " completed_total=", completed, " pending=", queued > completed ? queued - completed : 0,
        " dedup_total=", counters.duplicates.load(std::memory_order_relaxed),
        " queue_peak_total=", counters.queuePeak.load(std::memory_order_relaxed),
        " queue_wait_us_total=", counters.waitUs.load(std::memory_order_relaxed),
        " worker_us_total=", counters.workerUs.load(std::memory_order_relaxed)));
      intervals = FrameHistogram(); presentCalls = FrameHistogram(); windowStart = end;
    }
  public:
    class Scope {
      FrameMetrics* owner;
      Clock::time_point start;
    public:
      explicit Scope(FrameMetrics* p) : owner(p), start(p ? Clock::now() : Clock::time_point()) { }
      Scope(const Scope&) = delete;
      Scope& operator = (const Scope&) = delete;
      ~Scope() { if (owner) owner->record(start, Clock::now()); }
    };
    Scope measure() { return Scope(enabled ? this : nullptr); }
  };
}
