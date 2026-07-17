@echo off
setlocal
REM Project-scoped Serena launcher via AgentCore project router child proxy.
set "SCRIPT_DIR=%~dp0"
set "LAUNCHER=%SCRIPT_DIR%..\child_launcher.py"
where python >nul 2>&1
if errorlevel 1 (
  echo [serena.cmd] python not found on PATH 1>&2
  exit /b 1
)
python "%LAUNCHER%" --server serena
exit /b %ERRORLEVEL%
