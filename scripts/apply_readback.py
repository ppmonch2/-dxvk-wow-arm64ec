from pathlib import Path
import argparse,shutil
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[1]
shutil.copyfile(root/'patches/lab/readback_policy.h',a.source/'src/dxvk/readback_policy.h')
def replace(path,before,after):
    f=a.source/path;s=f.read_text()
    if s.count(before)!=1:raise SystemExit(f'{path}: ambiguous/missing readback site')
    f.write_text(s.replace(before,after));print('READBACK:',path)

replace('src/d3d11/d3d11_context.h',
        '    void CopyBuffer(',
        '    void NotifyReadback(ID3D11Resource* resource);\n\n    void CopyBuffer(')
replace('src/d3d11/d3d11_context.cpp',
'''        srcExtent);
    }
  }


  template<typename ContextType>
  void STDMETHODCALLTYPE D3D11CommonContext<ContextType>::CopyResource''',
'''        srcExtent);
    }
    NotifyReadback(pDstResource);
  }


  template<typename ContextType>
  void STDMETHODCALLTYPE D3D11CommonContext<ContextType>::CopyResource''')
replace('src/d3d11/d3d11_context.cpp',
'''          srcTexture->MipLevelExtent(i));
      }
    }
  }''',
'''          srcTexture->MipLevelExtent(i));
      }
    }
    NotifyReadback(pDstResource);
  }''')
replace('src/d3d11/d3d11_context.cpp',
'''    if (buf->HasSequenceNumber())
      GetTypedContext()->TrackBufferSequenceNumber(buf);''',
'''    if (buf->HasSequenceNumber())
      GetTypedContext()->TrackBufferSequenceNumber(buf);
    NotifyReadback(pDstBuffer);''')
replace('src/d3d11/d3d11_context.cpp',
'''  template<typename ContextType>
  void D3D11CommonContext<ContextType>::CopyBuffer(''',
'''  template<typename ContextType>
  void D3D11CommonContext<ContextType>::NotifyReadback(ID3D11Resource* resource) {
    D3D11_RESOURCE_DIMENSION dim;
    resource->GetType(&dim);
    bool eligible = false;
    if (dim == D3D11_RESOURCE_DIMENSION_BUFFER) {
      const auto* desc = static_cast<D3D11Buffer*>(resource)->Desc();
      eligible = desc->Usage == D3D11_USAGE_STAGING && (desc->CPUAccessFlags & D3D11_CPU_ACCESS_READ);
    } else {
      const auto* desc = GetCommonTexture(resource)->Desc();
      eligible = desc->Usage == D3D11_USAGE_STAGING && (desc->CPUAccessFlags & D3D11_CPU_ACCESS_READ);
    }
    if (eligible) GetTypedContext()->NotifyReadback();
  }

  template<typename ContextType>
  void D3D11CommonContext<ContextType>::CopyBuffer(''')
replace('src/d3d11/d3d11_context_def.h',
        '    uint64_t GetCurrentChunkId() const;',
        '    uint64_t GetCurrentChunkId() const;\n'
        '    // Deferred contexts record commands only; never submit while recording.\n'
        '    void NotifyReadback() { }')
replace('src/d3d11/d3d11_context_imm.h',
        '#pragma once', '#pragma once\n#include "../dxvk/readback_policy.h"')
replace('src/d3d11/d3d11_context_imm.h',
        '    VkDeviceSize            m_maxImplicitDiscardSize = 0ull;',
        '    bool m_labEarlyReadback = env::getEnvVar("WOW_DXVK_EARLY_READBACK") == "1";\n'
        '    lab::ReadbackBudget m_labReadbackBudget;\n'
        '    VkDeviceSize            m_maxImplicitDiscardSize = 0ull;')
replace('src/d3d11/d3d11_context_imm.h',
        '    void EndFrame();',
        '    void EndFrame();\n    void NotifyReadback();')
replace('src/d3d11/d3d11_context_imm.cpp',
        '  void D3D11ImmediateContext::EndFrame() {\n    D3D10DeviceLock lock = LockContext();',
        '  void D3D11ImmediateContext::EndFrame() {\n    D3D10DeviceLock lock = LockContext();\n'
        '    m_labReadbackBudget.endFrame();')
replace('src/d3d11/d3d11_context_imm.cpp',
        '  bool D3D11ImmediateContext::WaitForResource(',
'''  void D3D11ImmediateContext::NotifyReadback() {
    // Called under the existing immediate-context lock after the entire copy API.
    if (lab::metricsEnabled()) lab::readbackEligible.fetch_add(1, std::memory_order_relaxed);
    if (!m_labReadbackBudget.take(m_labEarlyReadback, GetPendingCsChunks() != 0)) return;
    // Dispatch earlier; keep all later Map/resource waits and barriers intact.
    ExecuteFlush(GpuFlushType::ImplicitStrongHint, nullptr, false);
    if (lab::metricsEnabled()) lab::readbackSubmits.fetch_add(1, std::memory_order_relaxed);
    static std::atomic<bool> logged {false};
    if (!logged.exchange(true, std::memory_order_relaxed))
      Logger::info("WOW-CUSTOM-ARM64-RB early_readback_submit max_per_frame=1");
  }

  bool D3D11ImmediateContext::WaitForResource(''')
replace('src/d3d11/d3d11_context_imm.cpp',
        '    m_videoContext(this, Device) {',
        '    m_videoContext(this, Device) {\n'
        '    Logger::info(str::format("WOW_READBACK enabled=", m_labEarlyReadback ? 1 : 0, " max_per_frame=1"));')
replace('src/d3d11/d3d11_context_imm.cpp',
'''    pResource->GetType(&resourceDim);

    HRESULT hr;''',
'''    pResource->GetType(&resourceDim);
    if (lab::waitsEnabled()) {
      if (MapType == D3D11_MAP_READ) lab::mapRead.fetch_add(1, std::memory_order_relaxed);
      if (MapType == D3D11_MAP_WRITE) lab::mapWrite.fetch_add(1, std::memory_order_relaxed);
      if (MapType == D3D11_MAP_READ_WRITE) lab::mapReadWrite.fetch_add(1, std::memory_order_relaxed);
      unsigned bit = 1u << ((unsigned(MapType) & 7u) * 4u + (unsigned(resourceDim) & 3u));
      if (!(lab::mapSeen.fetch_or(bit, std::memory_order_relaxed) & bit)) {
        if (resourceDim == D3D11_RESOURCE_DIMENSION_BUFFER) {
          const auto* desc = static_cast<D3D11Buffer*>(pResource)->Desc();
          Logger::info(str::format("WOW_READBACK_MAP type=", uint32_t(MapType), " dim=", uint32_t(resourceDim),
            " usage=", uint32_t(desc->Usage), " cpuFlags=", desc->CPUAccessFlags, " bytes=", desc->ByteWidth));
        } else {
          const auto* desc = GetCommonTexture(pResource)->Desc();
          Logger::info(str::format("WOW_READBACK_MAP type=", uint32_t(MapType), " dim=", uint32_t(resourceDim),
            " usage=", uint32_t(desc->Usage), " cpuFlags=", desc->CPUAccessFlags,
            " width=", desc->Width, " height=", desc->Height, " format=", uint32_t(desc->Format)));
        }
      }
    }

    HRESULT hr;''')
replace('src/util/log/log.cpp',
        '|| message.find("WOW_WAIT") != std::string::npos',
        '|| message.find("WOW_WAIT") != std::string::npos\n'
        '           || message.find("WOW_READBACK") != std::string::npos')
