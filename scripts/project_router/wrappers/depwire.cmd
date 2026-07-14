@echo off
setlocal
REM Project-scoped DepWire launcher via AgentCore project router child proxy.
set "SCRIPT_DIR=%~dp0"
set "LAUNCHER=%SCRIPT_DIR%..\child_launcher.py"
where python >nul 2>&1
if errorlevel 1 (
  echo [depwire.cmd] python not found on PATH 1>&2
  exit /b 1
)
python "%LAUNCHER%" --server depwire
exit /b %ERRORLEVEL%
