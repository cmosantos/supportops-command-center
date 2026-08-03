@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\update-supportops.ps1" -ProjectPath "%~dp0"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo SupportOps update ended with error code %EXIT_CODE%.
    pause
)
exit /b %EXIT_CODE%
