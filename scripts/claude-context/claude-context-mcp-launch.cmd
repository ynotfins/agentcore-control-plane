@echo off
REM AgentCore launcher: pull secrets from Windows User EVs at runtime.
REM Never store API keys in this file or in IDE MCP JSON.

setlocal EnableExtensions

for %%V in (OPENAI_API_KEY MILVUS_TOKEN MILVUS_ADDRESS OPENAI_BASE_URL EMBEDDING_PROVIDER EMBEDDING_MODEL) do (
  for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('%%V','User')"`) do set "%%V=%%A"
)

if not defined OPENAI_API_KEY (
  echo [claude-context] OPENAI_API_KEY is missing from Windows User environment. 1^>^&2
  exit /b 1
)
if not defined MILVUS_TOKEN (
  echo [claude-context] MILVUS_TOKEN is missing from Windows User environment. 1^>^&2
  exit /b 1
)

where claude-context-mcp.cmd >nul 2^>^&1
if errorlevel 1 goto npx_fallback

call claude-context-mcp.cmd
set "AgentCoreExitCode=%ERRORLEVEL%"
endlocal & exit /b %AgentCoreExitCode%

:npx_fallback
call npx.cmd --yes @zilliz/claude-context-mcp@0.1.15
set "AgentCoreExitCode=%ERRORLEVEL%"
endlocal & exit /b %AgentCoreExitCode%
