@echo off
setlocal
set "DXVK_ASYNC=1"
set "WOW_DXVK_DEDUP=1"
set "WOW_DXVK_WORKERS=auto"
set "WOW_DXVK_METRICS=1"
set "WOW_DXVK_PROFILE=dedup"
call "%~dp0play-custom.bat" %*
