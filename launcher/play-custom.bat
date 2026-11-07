@echo off
setlocal
set "WOW_EXE=D:\Wow test\World of Warcraft\_forever_\Wow-ARM64.exe"
if not "%~1"=="" set "WOW_EXE=%~1"
if not exist "%WOW_EXE%" goto missing
"%~dp0dxvk-test.exe" install
if errorlevel 1 goto failed
set "DXVK_HUD=version,api,fps,frametimes,compiler"
set "DXVK_LOG_LEVEL=info"
set "DXVK_LOG_PATH=%~dp0logs"
if not exist "%~dp0logs" mkdir "%~dp0logs"
for %%I in ("%WOW_EXE%") do cd /d "%%~dpI"
start "" /wait "%WOW_EXE%" -d3d11
exit /b 0
:missing
echo Game not found: "%WOW_EXE%"
echo Pass the full game EXE path as the first argument.
:failed
echo Game was not started. Read the error above.
pause
exit /b 1
