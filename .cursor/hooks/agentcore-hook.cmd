@echo off
setlocal EnableExtensions
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "DISPATCHER=%~dp0..\..\scripts\agentcore_cursor\hook_dispatcher.py"
if not exist "%DISPATCHER%" (
  echo {"error":"missing_dispatcher"}
  exit /b 2
)
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 "%DISPATCHER%" %*
) else (
  python "%DISPATCHER%" %*
)
exit /b %ERRORLEVEL%
