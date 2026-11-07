from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('source',type=Path);args=p.parse_args()
def replace(path,before,after):
    f=args.source/path;s=f.read_text()
    if s.count(before)!=1:raise SystemExit(f'{path}: ambiguous/missing WAIT site')
    f.write_text(s.replace(before,after));print('WAIT:',path)

replace('src/d3d11/d3d11_context_imm.cpp',
        '#include "d3d11_cmdlist.h"',
        '#include "d3d11_cmdlist.h"\n#include "../dxvk/wow_metrics.h"')
replace('src/d3d11/d3d11_context_imm.cpp',
'''          D3D11_MAPPED_SUBRESOURCE*   pMappedResource) {
    D3D10DeviceLock lock = LockContext();''',
'''          D3D11_MAPPED_SUBRESOURCE*   pMappedResource) {
    lab::TimedWait labMap(lab::WaitKind::Map);
    D3D10DeviceLock lock = LockContext();''')
replace('src/d3d11/d3d11_context_imm.cpp',
        '    m_csThread.synchronize(SequenceNumber);',
        '    lab::TimedWait labCs(lab::WaitKind::Cs, SequenceNumber > m_csThread.lastSequenceNumber());\n'
        '    m_csThread.synchronize(SequenceNumber);')
replace('src/d3d11/d3d11_context_imm.cpp',
        '        m_device->waitForResource(Resource, access);',
        '        lab::TimedWait labResource(lab::WaitKind::Resource);\n'
        '        m_device->waitForResource(Resource, access);')
replace('src/d3d11/d3d11_context_imm.cpp',
        '  void D3D11ImmediateContext::SynchronizeDevice() {\n    m_device->waitForIdle();',
        '  void D3D11ImmediateContext::SynchronizeDevice() {\n'
        '    lab::TimedWait labIdle(lab::WaitKind::Idle);\n    m_device->waitForIdle();')
replace('src/d3d11/d3d11_context_imm.cpp',
        '    HRESULT hr = query->GetData(pData, GetDataFlags);',
        '    HRESULT hr = query->GetData(pData, GetDataFlags);\n'
        '    if (lab::waitsEnabled()) {\n'
        '      lab::queryCalls.fetch_add(1, std::memory_order_relaxed);\n'
        '      if (hr == S_FALSE) lab::queryNotReady.fetch_add(1, std::memory_order_relaxed);\n'
        '    }')
replace('src/dxgi/dxgi_swapchain.h',
        '#include "dxgi_interfaces.h"',
        '#include "dxgi_interfaces.h"\n#include "../dxvk/wow_metrics.h"')
replace('src/dxgi/dxgi_swapchain.h',
        '    UINT                            m_presentId;',
        '    lab::FrameMetrics m_labOuter { "WOW_DXGI_METRICS" };\n'
        '    UINT                            m_presentId;')
replace('src/dxgi/dxgi_swapchain.cpp',
        '    auto options = m_factory->GetOptions();',
        '    auto labOuter = m_labOuter.measure(!(PresentFlags & DXGI_PRESENT_TEST));\n'
        '    auto options = m_factory->GetOptions();')
replace('src/dxgi/dxgi_swapchain.cpp',
        '    std::lock_guard<dxvk::recursive_mutex> lockWin(m_lockWindow);\n    HRESULT hr = S_OK;',
        '    lab::TimedWait labWindow(lab::WaitKind::Window);\n'
        '    std::lock_guard<dxvk::recursive_mutex> lockWin(m_lockWindow);\n'
        '    labWindow.stop();\n    HRESULT hr = S_OK;')
replace('src/dxgi/dxgi_swapchain.cpp',
        '      std::lock_guard<dxvk::mutex> lockBuf(m_lockBuffer);\n      hr = m_presenter->Present',
        '      lab::TimedWait labBuffer(lab::WaitKind::Buffer);\n'
        '      std::lock_guard<dxvk::mutex> lockBuf(m_lockBuffer);\n'
        '      labBuffer.stop();\n      hr = m_presenter->Present')
replace('src/dxvk/dxvk_instance.cpp',
        '#include "dxvk_instance.h"',
        '#include "dxvk_instance.h"\n#include "wow_metrics.h"')
replace('src/dxvk/dxvk_instance.cpp',
        '    m_options = DxvkOptions(m_config);',
        '    m_options = DxvkOptions(m_config);\n'
        '    Logger::info(str::format("WOW_WAIT enabled=", lab::waitsEnabled() ? 1 : 0, " CPU_TIMINGS_ONLY"));')
replace('src/util/log/log.cpp',
        '|| message.find("WOW_LAB") != std::string::npos)',
        '|| message.find("WOW_LAB") != std::string::npos\n'
        '           || message.find("WOW_WAIT") != std::string::npos\n'
        '           || message.find("WOW_DXGI_METRICS") != std::string::npos)')
