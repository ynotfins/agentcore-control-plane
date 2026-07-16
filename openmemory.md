# OpenMemory Guide

## Overview

`D:\github\agentcore-control-plane` is the AgentCore-owned control repository for governance, renderers, schemas, validators, operational scripts, and storage/integration policy. It is not a runtime-data repository.

## Architecture

- Source roots:
  - `D:\github\agentcore-control-plane`
  - `D:\github\vendor\swarm`
  - `D:\github\vendor\memory`
- Runtime roots:
  - `F:\PostgreSQL18` (canonical PostgreSQL 18 data/service tier for `agent_core` and `cognee_core`)
  - `F:\AgentCore` (preserved PG16 rollback/legacy evidence and Swarm-owned runtime state)
  - `H:\AgentRuntime` (live Bifrost gateway + Tentra data — never format H:)
- Archive/backup root:
  - `E:\AgentCoreArchive` (canonical; live E: also carries `E:\AgentCore-Backups`)
- Governed non-Swarm IDE memory:
  - `agentcore-gateway` at `http://127.0.0.1:8080/mcp`
  - stable `agentcore-memory` identity behind Bifrost with the completed M4/M5 compact retrieval surface

## Environment Variable Policy

AgentCore does not use `.env` files. All secrets and runtime credentials are stored in Windows Environment Variables. Documentation may list variable names only, never values.

## User Defined Namespaces

- [Leave blank - user populates]

## Components

### Control Plane Repo

- Location: `D:\github\agentcore-control-plane`
- Purpose: MCP governance, renderer generation, docs, schemas, validation, and operational policy

### AgentCore Bifrost Gateway Runtime

- Location: `H:\AgentRuntime\bifrost`
- Endpoint: `http://127.0.0.1:8080/mcp`
- Startup owner: Windows Scheduled Task `\AgentCore\AgentCore-Bifrost-Gateway`
- Launcher: `ops\bifrost\Launch-AgentCoreBifrostGateway.ps1` keeps `bifrost-http.exe` in the foreground so Task Scheduler can restart it.

### Vendor Swarm Sources

- Location: `D:\github\vendor\swarm`
- Purpose: isolated upstream source clones for `swarmclaw`, `swarmvault`, `swarmdock`, `swarmfeed`, and `swarmrelay`

### Vendor Memory Sources

- Location: `D:\github\vendor\memory`
- Purpose: isolated upstream source clones for `lossless-memory4agent` and `lossless-claw`

### Runtime Memory Zone (Swarm ecosystem only)

- Location: `F:\AgentCore\agentmemory`
- Purpose: local runtime state for `swarmvault`, `lcm`, `swarmclaw`, and `swarmrelay` — **Swarm ecosystem components, not part of the non-Swarm AgentCore memory architecture**

### Backup Zone

- Location: `E:\AgentCoreArchive`
- Purpose: cold backups for PostgreSQL, local memory systems, vault exports, and logs

## Patterns

- Keep vendor source, runtime state, and backups physically separated by root path.
- Keep private first-responder data local-only by default.
- Use `agentcore-gateway` + `agentcore-memory` for governed non-Swarm IDE memory; do not bypass it with local memory runtimes.
- Treat PostgreSQL 18 at `127.0.0.1:55433` as canonical for AgentCore; classify `127.0.0.1:55432` as PG16 rollback/legacy evidence or Swarm-owned only.
- Read project facts and static facts before planning or making architectural decisions.
- If an AgentCore environment variable is missing, stop and report the variable name instead of creating a local fallback.
- Do not place runtime DBs, dumps, `raw/`, `wiki/`, or incident data in the control-plane repo.
