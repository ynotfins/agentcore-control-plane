@echo off
setlocal
REM Project-scoped Tentra launcher via AgentCore project router child proxy.
set "SCRIPT_DIR=%~dp0"
set "LAUNCHER=%SCRIPT_DIR%..\child_launcher.py"
where python >nul 2>&1
if errorlevel 1 (
  echo [tentra.cmd] python not found on PATH 1>&2
  exit /b 1
)
python "%LAUNCHER%" --server tentra
exit /b %ERRORLEVEL%
