@echo off
setlocal
set "DXVK_ASYNC=1"
set "WOW_DXVK_DEDUP=0"
set "WOW_DXVK_WORKERS=auto"
set "WOW_DXVK_METRICS=1"
set "WOW_DXVK_PROFILE=async"
call "%~dp0play-custom.bat" %*
