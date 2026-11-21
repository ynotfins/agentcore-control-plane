@echo off
REM AgentCore Cursor hook wrapper — preserve stdin bytes into Python.
REM Do not write banners to stdout. Diagnostics belong in the Python dispatcher (stderr/log).
setlocal EnableExtensions
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "PYTHONUNBUFFERED=1"
set "DISPATCHER=%~dp0..\..\scripts\agentcore_cursor\hook_dispatcher.py"
if not exist "%DISPATCHER%" (
  echo {"error":"missing_dispatcher"}
  exit /b 2
)
REM Prefer python.exe over the py launcher — py.exe has broken stdin inheritance in some Cursor hook hosts.
where python >nul 2>&1
if errorlevel 1 (
  where py >nul 2>&1
  if errorlevel 1 (
    echo {"error":"missing_python"}
    exit /b 2
  )
  py -3 -u "%DISPATCHER%" %*
  exit /b %ERRORLEVEL%
)
python -u "%DISPATCHER%" %*
exit /b %ERRORLEVEL%
