from pathlib import Path
import argparse, shutil

p=argparse.ArgumentParser();p.add_argument('source',type=Path);args=p.parse_args()
root=Path(__file__).resolve().parents[1]
for name in ['lab_stats.h','wow_metrics.h']:
    shutil.copyfile(root/'patches/lab'/name,args.source/'src/dxvk'/name)
def replace(path,before,after):
    f=args.source/path;s=f.read_text()
    if s.count(before)!=1:raise SystemExit(f'{path}: ambiguous/missing patch site')
    f.write_text(s.replace(before,after))
    print('LAB:',path)

replace('src/dxvk/dxvk_pipemanager.h','#include <mutex>','#include <mutex>\n#include "wow_metrics.h"')
replace('src/dxvk/dxvk_pipemanager.h',
    'PipelineEntry(DxvkGraphicsPipeline* p, const DxvkGraphicsPipelineStateInfo& s)\n      : pipelineLibrary(nullptr), graphicsPipeline(p), graphicsState(s) { }',
    'PipelineEntry(DxvkGraphicsPipeline* p, const DxvkGraphicsPipelineStateInfo& s, bool tracked = false)\n      : pipelineLibrary(nullptr), graphicsPipeline(p), graphicsState(s), labTracked(tracked) { }')
replace('src/dxvk/dxvk_pipemanager.h',
    '      DxvkGraphicsPipelineStateInfo graphicsState;',
    '      DxvkGraphicsPipelineStateInfo graphicsState;\n'
    '      lab::Clock::time_point labQueuedAt { };\n'
    '      bool labTracked = false;')
replace('src/dxvk/dxvk_pipemanager.h',
    '    dxvk::mutex                       m_lock;',
    '    dxvk::mutex                       m_lock;\n'
    '    bool m_labDedupe = false;\n'
    '    lab::PendingHighJobs<DxvkGraphicsPipeline, DxvkGraphicsPipelineStateInfo> m_labPending;')
replace('src/dxvk/dxvk_pipemanager.cpp',
    ': m_device(device) {\n\n  }',
    ': m_device(device) {\n    m_labDedupe = env::getEnvVar("WOW_DXVK_DEDUP") == "1";\n  }')
replace('src/dxvk/dxvk_pipemanager.cpp',
    '    m_buckets[uint32_t(priority)].queue.emplace(library);',
    '    m_buckets[uint32_t(priority)].queue.emplace(library);\n'
    '    if (lab::metricsEnabled()) {\n'
    '      m_buckets[uint32_t(priority)].queue.back().labQueuedAt = lab::Clock::now();\n'
    '      uint64_t depth = 0; for (const auto& bucket : m_buckets) depth += bucket.queue.size();\n'
    '      lab::noteQueue(depth);\n    }')
replace('src/dxvk/dxvk_pipemanager.cpp',
    '    pipeline->acquirePipeline();',
    '    // Only coalesce repeated high-priority async work. A queued low-priority\n'
    '    // optimization must never suppress a later high-priority request.\n'
    '    bool tracked = m_labDedupe && priority == DxvkPipelinePriority::High;\n'
    '    if (tracked && !m_labPending.insert(pipeline, state)) {\n'
    '      lab::noteDuplicate();\n      return;\n    }\n'
    '    pipeline->acquirePipeline();')
replace('src/dxvk/dxvk_pipemanager.cpp',
    '    m_buckets[uint32_t(priority)].queue.emplace(pipeline, state);',
    '    m_buckets[uint32_t(priority)].queue.emplace(pipeline, state, tracked);\n'
    '    if (lab::metricsEnabled()) {\n'
    '      m_buckets[uint32_t(priority)].queue.back().labQueuedAt = lab::Clock::now();\n'
    '      uint64_t depth = 0; for (const auto& bucket : m_buckets) depth += bucket.queue.size();\n'
    '      lab::noteQueue(depth);\n    }')
replace('src/dxvk/dxvk_pipemanager.cpp',
    '      // Number of workers that can process pipeline pipelines with normal',
    '      const auto requestedCap = env::getEnvVar("WOW_DXVK_WORKERS");\n'
    '      if (requestedCap == "2") workerCount = std::min(workerCount, 2u);\n'
    '      if (requestedCap == "4") workerCount = std::min(workerCount, 4u);\n'
    '      if (requestedCap == "8") workerCount = std::min(workerCount, 8u);\n'
    '      Logger::info(str::format("WOW_LAB workers=", workerCount,\n'
    '        " dedup=", m_labDedupe ? 1 : 0, " metrics=", lab::metricsEnabled() ? 1 : 0));\n\n'
    '      // Number of workers that can process pipeline pipelines with normal')
replace('src/dxvk/dxvk_pipemanager.cpp',
    '      if (entry.pipelineLibrary) {',
    '      auto labStarted = lab::metricsEnabled() ? lab::Clock::now() : lab::Clock::time_point();\n'
    '      if (entry.pipelineLibrary) {')
replace('src/dxvk/dxvk_pipemanager.cpp',
    '        entry.graphicsPipeline->releasePipeline();',
    '        if (entry.labTracked) {\n'
    '          std::unique_lock lock(m_lock);\n'
    '          m_labPending.erase(entry.graphicsPipeline, entry.graphicsState);\n'
    '        }\n'
    '        entry.graphicsPipeline->releasePipeline();')
replace('src/dxvk/dxvk_pipemanager.cpp',
    '      m_tasksCompleted += 1;',
    '      m_tasksCompleted += 1;\n      lab::noteWorker(entry.labQueuedAt, labStarted);')
replace('src/d3d11/d3d11_swapchain.h',
    '#include "d3d11_texture.h"',
    '#include "d3d11_texture.h"\n#include "../dxvk/wow_metrics.h"')
replace('src/d3d11/d3d11_swapchain.h',
    '    uint64_t                m_frameId      = DXGI_MAX_SWAP_CHAIN_BUFFERS;',
    '    lab::FrameMetrics m_labFrames;\n'
    '    uint64_t                m_frameId      = DXGI_MAX_SWAP_CHAIN_BUFFERS;')
replace('src/d3d11/d3d11_swapchain.cpp',
    '    if (std::exchange(m_dirty, false))',
    '    auto labFrame = m_labFrames.measure();\n'
    '    if (std::exchange(m_dirty, false))')
replace('src/util/log/log.cpp',
    'if (message.find("WOW-CUSTOM-ARM64-WAIT") != std::string::npos)',
    'if (message.find("WOW-CUSTOM-ARM64-WAIT") != std::string::npos\n'
    '           || message.find("WOW_METRICS") != std::string::npos\n'
    '           || message.find("WOW_LAB") != std::string::npos)')
