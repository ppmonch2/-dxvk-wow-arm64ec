#!/usr/bin/env python3
"""Apply the version-matched GPLAsync patch and small opt-in/diagnostic fixes."""
from pathlib import Path
import argparse
import hashlib
import subprocess

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--build-id', required=True)
args = p.parse_args()
assert args.build_id.isalnum()
build = args.build_id[:12]
patch = Path(__file__).resolve().parents[1]/'patches/dxvk-gplasync-2.3.1-1.patch'
assert hashlib.sha256(patch.read_bytes()).hexdigest() == '7d82eaa170e16d26ed653738bb14fcff91b26d3782298299bb55254946d71e72'
subprocess.run(['git','apply','--check',str(patch)],cwd=args.source,check=True)
subprocess.run(['git','apply',str(patch)],cwd=args.source,check=True)

def replace(path, before, after):
    f=args.source/path
    text=f.read_text()
    if text.count(before) != 1:
        raise SystemExit(f'{path}: expected exactly one patch site')
    f.write_text(text.replace(before,after))
    print(f'Async adjustment: {path}')

# The original patch enables async implicitly. Keep this experimental behavior opt-in
# and support an exact on/off comparison using the SAME DLL pair.
replace('src/dxvk/dxvk_options.cpp',
'''    if (env::getEnvVar("DXVK_GPLASYNCCACHE") == "1")
      gplAsyncCache = true;
    else
      gplAsyncCache = config.getOption<bool>("dxvk.gplAsyncCache", false);
    
    if (env::getEnvVar("DXVK_ASYNC") == "0")
      enableAsync = false;
    else
      enableAsync = config.getOption<bool>("dxvk.enableAsync", true);''',
'''    // Keep the separate GPLAsync-cache experiment disabled in this trial.
    gplAsyncCache = false;
    const std::string asyncEnv = env::getEnvVar("DXVK_ASYNC");
    if (asyncEnv == "1")
      enableAsync = true;
    else if (asyncEnv == "0")
      enableAsync = false;
    else
      enableAsync = config.getOption<bool>("dxvk.enableAsync", false);''')

# This flag is touched by the rendering path and pipeline compiler workers.
# Use an atomic rather than importing the plain-bool data race from the patch.
replace('src/dxvk/dxvk_graphics.h','#include <mutex>','#include <mutex>\n#include <atomic>')
replace('src/dxvk/dxvk_graphics.h',
        'bool                                          m_async = false;',
        'std::atomic<bool>                             m_async { false };')

replace('src/dxvk/dxvk_graphics.cpp',
        '        m_async = true;',
        '        m_async = true;\n'
        '        static std::atomic<bool> loggedAsync { false };\n'
        '        if (!loggedAsync.exchange(true, std::memory_order_relaxed))\n'
        f'          Logger::info("WOW-CUSTOM-ARM64-ASYNC build={build} async_pipeline_scheduled");')

replace('src/dxvk/dxvk_instance.cpp',
        '    m_options = DxvkOptions(m_config);',
        '    m_options = DxvkOptions(m_config);\n'
        f'    Logger::info(str::format("WOW-CUSTOM-ARM64-ASYNC build={build} async=",\n'
        '      m_options.enableAsync ? 1 : 0, " gplAsyncCache=", m_options.gplAsyncCache ? 1 : 0));')

# Diagnostic files must retain the final lines even if the process terminates.
# Flush the few diagnostic markers only; do not flush the per-frame logging path.
replace('src/util/log/log.cpp',
        '        if (m_fileStream)\n          m_fileStream << adjusted;',
        '        if (m_fileStream) {\n'
        '          m_fileStream << adjusted;\n'
        '          if (message.find("WOW-CUSTOM-ARM64-ASYNC") != std::string::npos)\n'
        '            m_fileStream.flush();\n'
        '        }')

# Remove only the added whitespace-only lines from the third-party patch.
replace('src/dxvk/dxvk_graphics.cpp',
        'm_fastPipelines.insert({ key, handle });\n    \n    m_async = false;',
        'm_fastPipelines.insert({ key, handle });\n\n    m_async = false;')
replace('src/dxvk/dxvk_options.cpp',
        'false);\n    \n    // Keep the separate GPLAsync-cache',
        'false);\n\n    // Keep the separate GPLAsync-cache')
