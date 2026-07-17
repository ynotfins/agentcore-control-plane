@echo off
setlocal
REM Project-scoped Context Fabric launcher via AgentCore project router child proxy.
set "SCRIPT_DIR=%~dp0"
set "LAUNCHER=%SCRIPT_DIR%..\child_launcher.py"
where python >nul 2>&1
if errorlevel 1 (
  echo [context-fabric.cmd] python not found on PATH 1>&2
  exit /b 1
)
python "%LAUNCHER%" --server context-fabric
exit /b %ERRORLEVEL%
