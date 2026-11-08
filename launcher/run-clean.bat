@echo off
setlocal
set "CLEAN_VERSION=%~1"
set "HELPER=%~dp0dxvk-test.exe"
if "%CLEAN_VERSION%"=="231" set "HELPER=%~dp0control-231\dxvk-test.exe"
if not "%CLEAN_VERSION%"=="231" if not "%CLEAN_VERSION%"=="271" goto failed
set "WOW_EXE=D:\Wow test\World of Warcraft\_forever_\Wow-ARM64.exe"
if not "%~2"=="" set "WOW_EXE=%~2"
if not exist "%WOW_EXE%" goto missing
"%HELPER%" install
if errorlevel 1 goto failed
set "WINEDEBUG=-all"
set "WINEDLLOVERRIDES=d3d11,dxgi=n,b"
set "DXVK_ASYNC="
set "DXVK_GPLASYNCCACHE="
set "DXVK_CONFIG="
set "DXVK_CONFIG_FILE=%~dp0clean-defaults.conf"
set "DXVK_HUD=version,devinfo,api,fps,frametimes,compiler"
set "DXVK_LOG_LEVEL=info"
set "DXVK_LOG_PATH=%~dp0logs\clean-%CLEAN_VERSION%"
set "DXVK_STATE_CACHE_PATH=%~dp0cache\%CLEAN_VERSION%"
if not exist "%DXVK_LOG_PATH%" mkdir "%DXVK_LOG_PATH%"
if not exist "%DXVK_STATE_CACHE_PATH%" mkdir "%DXVK_STATE_CACHE_PATH%"
if not exist "%DXVK_LOG_PATH%" goto failed
for %%I in ("%WOW_EXE%") do cd /d "%%~dpI"
start "" /wait "%WOW_EXE%" -d3d11
exit /b 0
:missing
echo Game not found: "%WOW_EXE%"
echo Pass the full EXE path as the first argument to play-231.bat or play-271.bat.
:failed
echo Game was not started. Read the error above.
pause
exit /b 1
