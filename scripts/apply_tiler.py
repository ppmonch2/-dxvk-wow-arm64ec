from pathlib import Path
import argparse, shutil
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[1]
shutil.copyfile(root/'patches/lab/tiler_flush_policy.h', a.source/'src/dxvk/tiler_flush_policy.h')
def replace(path, before, after):
    f=a.source/path;s=f.read_text()
    if s.count(before)!=1:raise SystemExit(f'{path}: missing/ambiguous TILER site')
    f.write_text(s.replace(before,after));print('TILER:',path)

replace('src/d3d11/d3d11_context_imm.h', '#include "../dxvk/readback_policy.h"',
        '#include "../dxvk/readback_policy.h"\n#include "../dxvk/tiler_flush_policy.h"')
replace('src/d3d11/d3d11_context_imm.h', '    lab::ReadbackBudget m_labReadbackBudget;',
'''    lab::ReadbackBudget m_labReadbackBudget;
    lab::TilerFlushPolicy m_labTiler { env::getEnvVar("WOW_DXVK_TILER_FLUSH") == "1" };
    uint64_t m_labWeakSuppressed = 0, m_labBoundaryFlushes = 0;
    uint64_t m_labContextFlushes = 0, m_labFrames = 0;''')
replace('src/d3d11/d3d11_context_imm.h', '    void NotifyReadback();',
        '    void NotifyReadback();\n    void NotifyRenderPassBoundary();')
replace('src/d3d11/d3d11_context_imm.cpp',
'''    Logger::info(str::format("WOW_READBACK enabled=", m_labEarlyReadback ? 1 : 0, " max_per_frame=1"));''',
'''    // Keep the independent early-readback experiment off in this comparison.
    m_labEarlyReadback = false;
    Logger::info(str::format("WOW_READBACK enabled=", 0, " max_per_frame=1"));
    Logger::info(str::format("WOW_TILER enabled=", m_labTiler.enabled() ? 1 : 0,
      " driver_id=", uint32_t(m_device->adapter()->devicePropertiesExt().vk12.driverID),
      " vendor_id=", m_device->adapter()->deviceProperties().vendorID,
      " early_readback=0 explicit_and_map_waits=preserved"));''')
replace('src/d3d11/d3d11_context_imm.cpp', '    m_labReadbackBudget.endFrame();',
'''    m_labReadbackBudget.endFrame();
    if (++m_labFrames % 300 == 0 && lab::metricsEnabled())
      Logger::info(str::format("WOW_TILER_STATS frames=", m_labFrames,
        " context_flushes_total=", m_labContextFlushes,
        " weak_suppressed_total=", m_labWeakSuppressed,
        " boundary_flushes_total=", m_labBoundaryFlushes));''')
replace('src/d3d11/d3d11_context_imm.cpp',
'''    uint64_t chunkId = GetCurrentSequenceNumber();
    uint64_t submissionId = m_submissionFence->value();

    if (m_flushTracker.considerFlush(FlushType, chunkId, submissionId))
      ExecuteFlush(FlushType, nullptr, false);''',
'''    // On tilers, avoid optional mid-pass submissions. Mandatory sync and
    // explicit flush paths still follow the original tracker/ExecuteFlush.
    if (m_labTiler.suppressWeak(FlushType)) {
      ++m_labWeakSuppressed;
      return;
    }
    uint64_t chunkId = GetCurrentSequenceNumber();
    uint64_t submissionId = m_submissionFence->value();
    if (m_flushTracker.considerFlush(FlushType, chunkId, submissionId))
      ExecuteFlush(FlushType, nullptr, false);
    else
      m_labTiler.missed(FlushType, GetPendingCsChunks() != 0);''')
replace('src/d3d11/d3d11_context_imm.cpp', '  void D3D11ImmediateContext::ExecuteFlush(',
'''  void D3D11ImmediateContext::NotifyRenderPassBoundary() {
    if (!m_labTiler.enabled()) {
      // Identical to DXVK 2.3.1 when the experiment is off.
      ConsiderFlush(GpuFlushType::ImplicitWeakHint);
    } else if (m_labTiler.boundary(GetPendingCsChunks() != 0)) {
      // Complete a previously deferred strong submission hint at a boundary.
      ++m_labBoundaryFlushes;
      ExecuteFlush(GpuFlushType::ImplicitStrongHint, nullptr, false);
      if (m_labBoundaryFlushes == 1)
        Logger::info("WOW_TILER boundary_submit_executed");
    }
  }

  void D3D11ImmediateContext::ExecuteFlush(''')
replace('src/d3d11/d3d11_context_imm.cpp',
'''    // Signal the submission fence and flush the command list
    uint64_t submissionId = ++m_submissionId;''',
'''    m_labTiler.submitted();
    ++m_labContextFlushes;
    // Signal the submission fence and flush the command list
    uint64_t submissionId = ++m_submissionId;''')
replace('src/d3d11/d3d11_context.cpp',
'''        // Doing this makes it less likely to flush during render passes
        GetTypedContext()->ConsiderFlush(GpuFlushType::ImplicitWeakHint);''',
'''        GetTypedContext()->NotifyRenderPassBoundary();''')
replace('src/util/log/log.cpp', '|| message.find("WOW_READBACK") != std::string::npos',
        '|| message.find("WOW_READBACK") != std::string::npos\n'
        '           || message.find("WOW_TILER") != std::string::npos')
