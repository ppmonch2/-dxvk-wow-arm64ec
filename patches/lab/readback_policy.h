#pragma once
namespace dxvk::lab {
  class ReadbackBudget {
    bool used = false;
  public:
    bool take(bool enabled, bool hasCommands) {
      if (!enabled || !hasCommands || used) return false;
      used = true;
      return true;
    }
    void endFrame() { used = false; }
  };
}
