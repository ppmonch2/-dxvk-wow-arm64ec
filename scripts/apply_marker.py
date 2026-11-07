#!/usr/bin/env python3
"""Fail-closed diagnostic-only patch for upstream DXVK v2.3.1."""
from pathlib import Path
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("--build-id", required=True)
args = parser.parse_args()
if not args.build_id.isalnum():
    raise SystemExit("Build ID must be alphanumeric")
marker = "WOW-CUSTOM-ARM64EC"
build = args.build_id[:12]

def replace(path, before, after):
    target = args.source / path
    source = target.read_text()
    if source.count(before) != 1:
        raise SystemExit(f"{path}: expected exactly one patch site")
    target.write_text(source.replace(before, after))
    print(f"Patched {path}")

replace("src/dxvk/hud/dxvk_hud_item.cpp",
        '"DXVK " DXVK_VERSION);',
        f'"DXVK " DXVK_VERSION " | {marker} [{build}]");')
replace("src/dxvk/dxvk_instance.cpp",
        'Logger::info(str::format("DXVK: ", DXVK_VERSION));',
        'Logger::info(str::format("DXVK: ", DXVK_VERSION));\n'
        f'    Logger::info("{marker} build={build} DXVK instance initialized");')
replace("src/d3d11/d3d11_main.cpp",
        '    InitReturnPtr(ppDevice);\n    InitReturnPtr(ppSwapChain);',
        f'    Logger::info("{marker} build={build} module=d3d11.dll D3D11InternalCreateDeviceAndSwapChain");\n'
        '    InitReturnPtr(ppDevice);\n    InitReturnPtr(ppSwapChain);')
replace("src/dxgi/dxgi_main.cpp",
        '  HRESULT createDxgiFactory(UINT Flags, REFIID riid, void **ppFactory) {',
        '  HRESULT createDxgiFactory(UINT Flags, REFIID riid, void **ppFactory) {\n'
        f'    Logger::info("{marker} build={build} module=dxgi.dll createDxgiFactory");')
