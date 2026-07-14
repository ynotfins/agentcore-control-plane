# OpenMemory Guide

## Overview

`D:\github\agentcore-control-plane` is the AgentCore-owned control repository for governance, renderers, schemas, validators, operational scripts, and storage/integration policy. It is not a runtime-data repository.

## Architecture

- Source roots:
  - `D:\github\agentcore-control-plane`
  - `D:\github\vendor\swarm`
  - `D:\github\vendor\memory`
- Runtime root:
  - `F:\AgentCore`
- Backup root:
  - `E:\AgentCoreBackups`
- Governed non-Swarm IDE memory:
  - `agentcore-gateway` at `http://127.0.0.1:8080/mcp`
  - stable `agentcore-memory` identity behind Bifrost (health/status now; fuller memory platform later)

## Environment Variable Policy

AgentCore does not use `.env` files. All secrets and runtime credentials are stored in Windows Environment Variables. Documentation may list variable names only, never values.

## User Defined Namespaces

- [Leave blank - user populates]

## Components

### Control Plane Repo

- Location: `D:\github\agentcore-control-plane`
- Purpose: MCP governance, renderer generation, docs, schemas, validation, and operational policy

### Vendor Swarm Sources

- Location: `D:\github\vendor\swarm`
- Purpose: isolated upstream source clones for `swarmclaw`, `swarmvault`, `swarmdock`, `swarmfeed`, and `swarmrelay`

### Vendor Memory Sources

- Location: `D:\github\vendor\memory`
- Purpose: isolated upstream source clones for `lossless-memory4agent` and `lossless-claw`

### Runtime Memory Zone

- Location: `F:\AgentCore\agentmemory`
- Purpose: local runtime state for `swarmvault`, `lcm`, `swarmclaw`, and `swarmrelay`

### Backup Zone

- Location: `E:\AgentCoreBackups`
- Purpose: cold backups for PostgreSQL, local memory systems, vault exports, and logs

## Patterns

- Keep vendor source, runtime state, and backups physically separated by root path.
- Keep private first-responder data local-only by default.
- Use `agentcore-gateway` + `agentcore-memory` for governed non-Swarm IDE memory; do not bypass it with local memory runtimes.
- Read project facts and static facts before planning or making architectural decisions.
- If an AgentCore environment variable is missing, stop and report the variable name instead of creating a local fallback.
- Do not place runtime DBs, dumps, `raw/`, `wiki/`, or incident data in the control-plane repo.
