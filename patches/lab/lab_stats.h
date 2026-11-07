#pragma once
#include <array>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <functional>
#include <unordered_set>

namespace dxvk::lab {
  // One millisecond bins. Percentiles are upper bounds within a bin; values
  // above Ceiling are counted separately and maxMs retains their exact value.
  class FrameHistogram {
  public:
    static constexpr uint32_t Ceiling = 4095;
    uint64_t count = 0, over50 = 0, over100 = 0, overflow = 0;
    double sumMs = 0, maxMs = 0;
    void add(double ms) {
      if (!std::isfinite(ms) || ms < 0) return;
      count++; sumMs += ms; maxMs = std::max(maxMs, ms);
      over50 += ms > 50; over100 += ms > 100; overflow += ms > Ceiling;
      auto bin = uint32_t(std::min<double>(std::ceil(ms), Ceiling));
      bins[bin]++;
    }
    double mean() const { return count ? sumMs / double(count) : 0; }
    uint32_t percentile(uint32_t percent) const {
      if (!count) return 0;
      auto goal = (count * std::min(percent, 100u) + 99) / 100;
      uint64_t n = 0;
      for (uint32_t i = 0; i <= Ceiling; i++) {
        n += bins[i];
        if (n >= goal) return i;
      }
      return Ceiling;
    }
  private:
    std::array<uint32_t, Ceiling + 1> bins { };
  };

  // Caller holds the existing worker-queue mutex for insert/erase/size.
  // DXVK pipeline states already compare their whole byte representation.
  template<typename Pipeline, typename State>
  class PendingHighJobs {
    struct Key {
      Pipeline* pipeline;
      State state;
      bool operator == (const Key& other) const {
        return pipeline == other.pipeline && state == other.state;
      }
    };
    struct Hash {
      size_t operator () (const Key& key) const {
        size_t h = std::hash<const void*>()(key.pipeline);
        const auto* bytes = reinterpret_cast<const unsigned char*>(&key.state);
        for (size_t i = 0; i < sizeof(State); i++)
          h = (h ^ bytes[i]) * size_t(1099511628211ull);
        return h;
      }
    };
    std::unordered_set<Key, Hash> entries;
  public:
    bool insert(Pipeline* pipeline, const State& state) {
      return entries.insert(Key { pipeline, state }).second;
    }
    void erase(Pipeline* pipeline, const State& state) {
      entries.erase(Key { pipeline, state });
    }
    size_t size() const { return entries.size(); }
  };
}
