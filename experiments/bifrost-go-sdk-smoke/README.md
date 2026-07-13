# Bifrost Go SDK Smoke (experiment)

Isolated proof-of-concept for **in-process Bifrost model routing** via the Go SDK.

## Purpose

Validate that AgentCore can:

1. Implement the Bifrost `Account` interface against a pinned `bifrost/core` release
2. Route a low-cost OpenAI chat completion through the SDK
3. Shut down cleanly

## This is NOT the MCP Gateway

Bifrost’s outward MCP `/mcp` gateway is provided by the **Bifrost Gateway** HTTP deployment.

This program:

- embeds **only** the Go SDK (`github.com/maximhq/bifrost/core`)
- does **not** expose `/mcp`
- does **not** aggregate workstation MCP servers
- must not be described as the workstation MCP aggregator

The main AgentCore Bifrost Gateway task remains separate and untouched by this experiment.

## Bifrost module version

| Item | Value |
|------|-------|
| Module | `github.com/maximhq/bifrost/core` |
| Version | **v1.7.0** (pinned; `proxy.golang.org` `@latest` as of 2026-07-07) |
| Upstream tag | `core/v1.7.0` |
| Commit | `acd73be3e15879210e1838ef8be8304ef78f83ce` |

Do not use an unpinned branch or pseudoversion for this experiment.

### API notes vs older quickstart snippets

For v1.7.0 specifically:

- `GetKeysForProvider(ctx context.Context, …)` — not `*context.Context`
- `Key.Value` is `schemas.SecretVar` — use `*schemas.NewSecretVar("env.OPENAI_API_KEY")`
- Concurrency field is `Concurrency` (not `MaxConcurrency`)

## Required environment variables

| Name | Required | Notes |
|------|----------|-------|
| `OPENAI_API_KEY` | yes | Windows User env var is fine; process must see a non-empty value |

Never commit the key, write a `.env`, or print the value.

## Build

```powershell
$env:Path = "C:\Program Files\Go\bin;" + $env:Path
cd D:\github\agentcore-control-plane\experiments\bifrost-go-sdk-smoke
go build -o bifrost-go-sdk-smoke.exe .
```

## Unit tests

```powershell
go test ./...
```

Unit tests do **not** call OpenAI.

## Live smoke test

```powershell
# Ensure the process sees the User-scoped key name OPENAI_API_KEY (do not print the value)
if (-not $env:OPENAI_API_KEY) {
  $loaded = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'User')
  if ([string]::IsNullOrWhiteSpace($loaded)) { throw 'OPENAI_API_KEY missing' }
  Set-Item -Path Env:OPENAI_API_KEY -Value $loaded
}
go run .
# or
go test -tags=live -count=1 -run TestLiveSmoke ./...
```

Expected output (sanitized; content not printed):

```text
status=ok provider=openai model=gpt-4o-mini latency_ms=… prompt_tokens=… completion_tokens=… total_tokens=… content_chars=… request_id=smoke-… stream_chunks=0
status=ok provider=openai model=gpt-4o-mini latency_ms=… … stream_chunks=N mode=stream
status=shutdown ok=true
status=complete note="Go SDK model-routing smoke only; not the Bifrost MCP Gateway"
```

Provider/model: **OpenAI / gpt-4o-mini**

## Troubleshooting

| Symptom | Check |
|---------|-------|
| `OPENAI_API_KEY is not set or empty` | Refresh process env from User scope; confirm non-empty without printing |
| `go` not found | Add `C:\Program Files\Go\bin` to PATH for the shell |
| Init / provider errors | Confirm module is still `v1.7.0`; re-run `go mod verify` |
| Deadline exceeded | Network path to OpenAI; timeout is 45s request context / 60s provider default |

## Cleanup

```powershell
Remove-Item .\bifrost-go-sdk-smoke.exe -ErrorAction SilentlyContinue
# Optional: delete this experiment folder only if the operator retires it
```

## Relationship to AgentCore Bifrost Gateway

| Surface | Role |
|---------|------|
| This experiment | In-process SDK learning / smoke evidence |
| Bifrost Gateway deployment | HTTP + MCP outward gateway (production path) |

Do not promote this package into production automatically.

## Retry / fallback policy (POC)

- `MaxRetries=2` for transient network/5xx with the **single** OpenAI key
- No fallback providers (no other credentials configured)
- No MCP clients / tools enabled — retries cannot duplicate tool side effects

## Docs index

Listed under AgentCore `DOC_AUTHORITY.md` as an **experiment** (not production authority).
