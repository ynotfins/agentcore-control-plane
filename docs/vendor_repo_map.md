# Vendor Repo Map

Generated: 2026-06-24

## Purpose

This document maps the third-party Swarm and lossless-memory source repositories cloned under `D:\github\vendor`.

Rules for this layout:

- Vendor source lives only under `D:\github\vendor`.
- Runtime data does not live inside vendor clones.
- AgentCore-owned governance and integration docs live in `D:\github\agentcore-control-plane`.
- First-responder and house-fire data is private by default and must remain local-only unless a future approval explicitly allows a hosted path.

## Environment Variable Policy

AgentCore does not use `.env` files. All secrets and runtime credentials are stored in Windows Environment Variables. Documentation may list variable names only, never values.

## Source Roots

```text
D:\github\vendor\
  swarm\
    swarmclaw\
    swarmvault\
    swarmdock\
    swarmfeed\
    swarmrelay\
  memory\
    lossless-memory4agent\
    lossless-claw\
```

## Integration Summary

| Repo | Source path | Primary role | Install command | Runtime data path | Local-only capable | Hosted/cloud touchpoints | First-responder suitability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `swarmclaw` | `D:\github\vendor\swarm\swarmclaw` | Core multi-agent runtime and control plane | `npm i -g @swarmclawai/swarmclaw` or `npm run quickstart` from repo | `F:\AgentCore\agentmemory\swarmclaw` | Yes | Optional LLM/provider APIs, optional external connectors | Yes, when kept local with approval gates |
| `swarmvault` | `D:\github\vendor\swarm\swarmvault` | Local-first wiki, graph, and RAG vault | `npm install -g @swarmvaultai/cli` then `swarmvault quickstart` | `F:\AgentCore\agentmemory\swarmvault` | Yes | Optional cloud model providers only if enabled | Yes, preferred for local-only knowledge work |
| `swarmdock` | `D:\github\vendor\swarm\swarmdock` | Agent marketplace and escrow workflow | `npm i -g @swarmdock/cli` or local `pnpm` stack | No private incident runtime path approved; if self-hosted, isolate outside app repos | Partly; self-hosted dev stack exists but marketplace semantics are public-facing | Hosted MCP/API and wallet/payment flows | No for private incident payloads |
| `swarmfeed` | `D:\github\vendor\swarm\swarmfeed` | Public social network for agents | local `docker compose up -d`, `pnpm install`, `pnpm db:push`, `pnpm db:seed`, `pnpm dev` | No approved private runtime path | Dev stack can run locally, but the product is public by design | Public feed, API keys, hosted/public distribution | No |
| `swarmrelay` | `D:\github\vendor\swarm\swarmrelay` | Encrypted agent messaging | `pnpm install`, `docker-compose up -d`, `pnpm --filter @swarmrelay/api db:push`, `pnpm dev` | `F:\AgentCore\agentmemory\swarmrelay` | Yes | Optional hosted MCP endpoint; local stack preferred | Yes, preferred messaging path because it is E2E encrypted |
| `lossless-memory4agent` | `D:\github\vendor\memory\lossless-memory4agent` | Framework-agnostic DAG memory SDK | `npm install lossless-memory4agent` | `F:\AgentCore\agentmemory\lcm` | Yes | Only the summarizer callback you choose | Yes, if paired with local or approved summarizers |
| `lossless-claw` | `D:\github\vendor\memory\lossless-claw` | OpenClaw plugin for DAG-based long-term context | `openclaw plugins install @martian-engineering/lossless-claw@latest` | `F:\AgentCore\agentmemory\lcm` | Yes | Depends on the LLM provider configured in OpenClaw | Yes, if OpenClaw stays on approved local/provider routes |

## Repo Details

### `swarmclaw`

- Purpose: self-hosted AI agent runtime with swarms, schedules, durable memory, MCP tools, skills, and delegation.
- Install:
  - Global: `npm i -g @swarmclawai/swarmclaw`
  - Repo: `nvm use` then `npm run quickstart`
- Runtime path:
  - Standardized AgentCore path: `F:\AgentCore\agentmemory\swarmclaw`
  - Avoid the default app-data location for managed deployments when a controlled runtime path is available.
- Local-only:
  - Yes. Run locally on `http://localhost:3456`.
  - Docker is optional for sandbox/browser execution.
- Hosted/cloud touchpoints:
  - Optional LLM providers and optional external connectors.
- MCP/global-memory-gateway integration:
  - Native MCP server/client integration for tools.
  - SwarmClaw memory is not a replacement for governed cross-project memory.
  - Use `global-memory-gateway` for governed persistent memory writes; keep SwarmClaw session memory local to the runtime.
- First-responder stance:
  - Safe when configured local-first with approval gates enabled.
  - Do not attach public connectors or hosted endpoints for incident data until explicitly approved.

### `swarmvault`

- Purpose: local-first LLM Wiki, knowledge graph builder, and RAG vault for docs, code, notes, transcripts, and URLs.
- Install:
  - Global CLI: `npm install -g @swarmvaultai/cli`
  - First run: `swarmvault quickstart ./your-repo`
- Runtime path:
  - Standardized AgentCore path: `F:\AgentCore\agentmemory\swarmvault`
  - Expected internal structure: `raw/`, `wiki/`, `state/`, `agent/`
- Local-only:
  - Yes. The built-in heuristic provider works offline.
  - Ollama/local models are preferred if stronger extraction is needed without cloud routing.
- Hosted/cloud touchpoints:
  - Optional model-provider APIs only when deliberately configured.
- MCP/global-memory-gateway integration:
  - SwarmVault ships an MCP server for graph/query/context workflows.
  - SwarmVault artifacts remain local knowledge assets.
  - If a fact needs governed cross-project memory, summarize/redact it first and write through `global-memory-gateway`, not directly from raw vault artifacts.
- First-responder stance:
  - Preferred local knowledge substrate for private incident material.
  - Keep `heuristic` or local-model mode by default.

### `swarmdock`

- Purpose: marketplace for autonomous agents to register, discover tasks, bid, submit, and settle outcomes.
- Install:
  - CLI: `npm i -g @swarmdock/cli`
  - Local dev stack: `docker compose up -d`, `pnpm install`, `pnpm type-check`, `pnpm build`, `pnpm dev`
- Runtime path:
  - No approved AgentCore runtime path for private incident data.
  - If self-hosted for evaluation, isolate its Postgres/Redis/NATS/Meilisearch data from business app storage and from private-response systems.
- Local-only:
  - There is a self-hosted dev path, but the product's core marketplace function is external/public-facing.
- Hosted/cloud touchpoints:
  - Hosted MCP/API endpoint and Base-wallet signing flows.
- MCP/global-memory-gateway integration:
  - Available as an MCP endpoint for marketplace actions.
  - Do not feed marketplace task payloads into governed memory unless the content is already sanitized for public exposure.
- First-responder stance:
  - Not approved for incident or house-fire data.
  - Use only for non-sensitive/public commercial workloads after separate approval.

### `swarmfeed`

- Purpose: public social network for agents with posts, channels, reactions, and discovery.
- Install:
  - `docker compose up -d`
  - `pnpm install`
  - `pnpm db:push`
  - `pnpm db:seed`
  - `pnpm dev`
- Runtime path:
  - No approved private-data runtime path.
  - If evaluated locally, treat it as a sandbox only.
- Local-only:
  - A local dev stack exists, but the product semantics are public and observable.
- Hosted/cloud touchpoints:
  - Public feed/API behavior and API-key usage.
- MCP/global-memory-gateway integration:
  - MCP server exists for agent posting/feed actions.
  - Never forward private incident content into SwarmFeed or into governed memory as a side effect of social posting workflows.
- First-responder stance:
  - Not approved for private data under any default configuration.

### `swarmrelay`

- Purpose: end-to-end encrypted messaging platform for AI agents, including MCP access.
- Install:
  - `pnpm install`
  - `docker-compose up -d`
  - `pnpm --filter @swarmrelay/api db:push`
  - `pnpm dev`
- Runtime path:
  - Standardized AgentCore path: `F:\AgentCore\agentmemory\swarmrelay`
- Local-only:
  - Yes. Local API/web stack is the preferred mode for private coordination.
- Hosted/cloud touchpoints:
  - Optional hosted MCP endpoint exists, but local MCP is preferred for sensitive use.
- MCP/global-memory-gateway integration:
  - MCP package exists for local or hosted transport.
  - Relay messages may be summarized into governed memory only if explicitly intended, redacted, and policy-safe.
  - The encrypted message store itself remains outside `global-memory-gateway`.
- First-responder stance:
  - Approved as the default secure messaging candidate because the content is E2E encrypted.

### `lossless-memory4agent`

- Purpose: standalone DAG-based memory SDK that stores every message in SQLite and compresses context losslessly via hierarchical summaries.
- Install:
  - `npm install lossless-memory4agent`
- Runtime path:
  - Standardized AgentCore path: `F:\AgentCore\agentmemory\lcm`
  - Default upstream path is `~/.lossless-memory/lcm.db`; override into the AgentCore runtime root for managed deployments.
- Local-only:
  - Yes. The library itself is local and has no required cloud service.
- Hosted/cloud touchpoints:
  - Only whatever summarizer callback you intentionally wire in.
- MCP/global-memory-gateway integration:
  - No native MCP server in this fork.
  - Best used as a local memory component behind an AgentCore wrapper or adapter.
  - It must not bypass `global-memory-gateway` for governed cross-project persistence.
- First-responder stance:
  - Approved for local-only private memory when paired with local or separately approved summarization.

### `lossless-claw`

- Purpose: OpenClaw plugin that replaces sliding-window compaction with DAG-based long-term memory and recall tools.
- Install:
  - `openclaw plugins install @martian-engineering/lossless-claw@latest`
- Runtime path:
  - Standardized AgentCore path: `F:\AgentCore\agentmemory\lcm`
  - Upstream default is `~/.openclaw/lcm.db`; prefer an AgentCore-managed path for operational consistency if supported by config.
- Local-only:
  - Yes, assuming the owning OpenClaw runtime stays local.
- Hosted/cloud touchpoints:
  - Uses the provider configuration already present in OpenClaw for summarization.
- MCP/global-memory-gateway integration:
  - Exposes memory behavior through OpenClaw plugin tools such as `lcm_grep`, `lcm_describe`, and `lcm_expand`.
  - It is local session/context memory, not a governed cross-project memory store.
- First-responder stance:
  - Approved when OpenClaw and its model/provider routes are restricted to approved local or private infrastructure.

## Default Deployment Order

1. `swarmclaw`
2. `swarmvault`
3. `swarmrelay`
4. `lossless-memory4agent` or `lossless-claw` depending on runtime owner
5. `swarmdock` only after explicit approval
6. `swarmfeed` only for public-facing/non-sensitive workflows

## AgentCore Policy

- Keep private first-responder data in local-only systems: `swarmclaw`, `swarmvault`, `swarmrelay`, and local LCM.
- Treat `swarmdock`, `swarmfeed`, and any future `swarmrecall`/hosted service as blocked for private incident payloads until a separate approval changes the boundary.
- Use `global-memory-gateway` for governed memory, not direct writes from vendor runtimes.
