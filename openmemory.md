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
- Governed cross-project memory:
  - `global-memory-gateway` backed by local PostgreSQL/pgvector

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
- Use `global-memory-gateway` for governed persistent memory; do not bypass it with local memory runtimes.
- Do not place runtime DBs, dumps, `raw/`, `wiki/`, or incident data in the control-plane repo.
