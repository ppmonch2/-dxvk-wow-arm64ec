@echo off
setlocal
set "DXVK_ASYNC=1"
set "WOW_DXVK_DEDUP=1"
set "WOW_DXVK_WORKERS=4"
set "WOW_DXVK_METRICS=1"
set "WOW_DXVK_PROFILE=balanced"
call "%~dp0play-custom.bat" %*
