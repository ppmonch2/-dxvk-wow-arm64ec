@echo off
setlocal
if "%DXVK_ASYNC%"=="1" goto selected
if "%DXVK_ASYNC%"=="0" goto selected
echo Use play-async-on.bat or play-async-off.bat
goto failed
:selected
if not defined WOW_DXVK_PROFILE set "WOW_DXVK_PROFILE=manual"
if not exist "D:\WoW-DXVK-test-cache" mkdir "D:\WoW-DXVK-test-cache"
set "DXVK_STATE_CACHE_PATH=D:\WoW-DXVK-test-cache"
set "WOW_EXE=D:\Wow test\World of Warcraft\_forever_\Wow-ARM64.exe"
if not "%~1"=="" set "WOW_EXE=%~1"
if not exist "%WOW_EXE%" goto missing
"%~dp0dxvk-test.exe" install
if errorlevel 1 goto failed
set "DXVK_HUD=version,api,fps,frametimes,compiler"
set "DXVK_LOG_LEVEL=info"
set "DXVK_LOG_PATH=%~dp0logs\%WOW_DXVK_PROFILE%"
if not exist "%DXVK_LOG_PATH%" mkdir "%DXVK_LOG_PATH%"
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
