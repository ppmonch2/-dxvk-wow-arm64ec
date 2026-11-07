#include "../patches/lab/lab_stats.h"
#include <atomic>
#include <cassert>
#include <cstring>
#include <limits>
#include <mutex>
#include <thread>
#include <vector>

struct State {
  std::array<uint32_t, 8> words {};
  bool operator == (const State& other) const { return words == other.words; }
};
int main() {
  dxvk::lab::FrameHistogram h;
  assert(h.percentile(95) == 0);
  for (double ms : {10., 20., 30., 40., 100., 200.}) h.add(ms);
  assert(h.count == 6 && h.percentile(50) == 30 && h.percentile(95) == 200);
  assert(h.over50 == 2 && h.over100 == 1 && h.maxMs == 200);
  h.add(-1); h.add(std::numeric_limits<double>::infinity());
  h.add(std::numeric_limits<double>::quiet_NaN());
  assert(h.count == 6);
  h.add(5000); assert(h.overflow == 1 && h.percentile(99) == h.Ceiling && h.maxMs == 5000);
  dxvk::lab::FrameHistogram fractional; fractional.add(16.1); fractional.add(16.9);
  assert(fractional.percentile(95) == 17);

  dxvk::lab::PendingHighJobs<int, State> pending;
  int a = 1, b = 2; State s, t; t.words[3] = 1;
  assert(pending.insert(&a,s)); assert(!pending.insert(&a,s));
  assert(pending.insert(&a,t)); assert(pending.insert(&b,s));
  pending.erase(&a,s); assert(pending.insert(&a,s));
  pending.erase(&a,s); pending.erase(&a,t); pending.erase(&b,s);
  assert(pending.size() == 0);

  std::mutex lock; std::atomic<unsigned> successes {0};
  std::atomic<bool> go {false}; std::vector<std::thread> threads;
  for (unsigned i=0;i<8;i++) threads.emplace_back([&] {
    while (!go.load()) std::this_thread::yield();
    std::lock_guard guard(lock);
    if (pending.insert(&a,s)) successes++;
  });
  go = true;
  for (auto& thread:threads) thread.join();
  assert(successes == 1 && pending.size() == 1);
  pending.erase(&a,s); assert(pending.insert(&a,s));
}
