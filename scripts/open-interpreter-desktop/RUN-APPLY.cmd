@echo off
pwsh -NoProfile -ExecutionPolicy Bypass -File "D:\launchers\open-interpreter\Apply-OpenInterpreter-Config.ps1"
exit /b %ERRORLEVEL%
