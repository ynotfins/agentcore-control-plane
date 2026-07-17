# UNIVERSAL_GATEWAY_VERIFICATION — CHAOSCENTRAL

**Generated:** 2026-07-03
**Purpose:** Verify or reject the planning assumption: *"OpenClaw exposes a universal OpenAI-compatible gateway at `localhost:3000/v1` and `/mcp` that can transparently run every IDE through Lossless Claw."*
**Verdict:** **REJECTED.** See §1.

---

## 1. Verdict (Executive)

**The assumption is REJECTED on every measurable dimension.**

| Dimension | Assumption | Reality | Verdict |
|-----------|------------|---------|---------|
| Gateway host | OpenClaw | OpenClaw is one of several agents | REJECTED |
| Port | `localhost:3000` | OpenClaw gateway binds to **`18789`** (per `gateway.cmd`) | REJECTED |
| API surface | OpenAI-compatible `/v1` | OpenClaw exposes its own control UI API, **not** an OpenAI-compatible `/v1/chat/completions` or `/v1/embeddings` endpoint | REJECTED |
| MCP surface | HTTP `/mcp` | All MCP servers in OpenClaw config are **stdio**, not HTTP | REJECTED |
| Routing every IDE through Lossless Claw | "transparent" | Lossless Claw is a local file-based plane (`lcm.sqlite`); not an HTTP service; cannot route traffic | REJECTED |
| Single point of orchestration | Yes | The actual canonical entry point is the **SwarmRecall MCP** via governed wrappers, not OpenClaw | REJECTED |

The architecture described in the assumption does not exist on CHAOSCENTRAL. Building plans on top of it would produce an instant failure: every IDE would receive "connection refused" or "endpoint not implemented" the first time it tried to talk to `127.0.0.1:3000`. **The assumption must be discarded before any architecture is proposed.**

---

## 2. Evidence: What OpenClaw Actually Exposes

### 2.1 OpenClaw config (`C:\Users\ynotf\.openclaw\openclaw.json`)

- `gateway.mode = "local"`
- `gateway.bind = "loopback"`
- Inline token `[REDACTED]`
- MCP servers: all `type = "stdio"` (no HTTP MCP servers defined)
- `controlUi` allowedOrigins: tied to port **18789**

### 2.2 OpenClaw launcher (`C:\Users\ynotf\.openclaw\gateway.cmd`)

- Sets `OPENCLAW_GATEWAY_PORT=18789`
- The **18789** port is the OpenClaw control UI gateway, not an OpenAI-compatible proxy.

### 2.3 OpenClaw process state at audit

- OpenClaw CLI processes (`openclaw` 2026.6.10) not actively running the gateway at audit time.
- ClawX sub-product is running (5 processes), but ClawX is a separate OpenClaw sub-product, not the gateway itself.
- **No listener on `127.0.0.1:18789` at audit moment.**

### 2.4 No `/v1/chat/completions` or `/v1/embeddings`

The OpenClaw config and process tree contain no OpenAI-compatible endpoint definitions. There is no `completion`, `chat`, `embedding`, or `audio` route in the OpenClaw API surface that could be reached by an IDE proxying through it.

### 2.5 No `/mcp` HTTP endpoint

MCP servers in OpenClaw are launched as stdio subprocesses. There is no `/mcp` HTTP endpoint in OpenClaw. There are also no HTTP MCP servers in the IDE contracts — every MCP server in the contract uses stdio transport.

---

## 3. Evidence: Listener Scan at Audit Moment

| Endpoint | Listener? | Process? |
|----------|-----------|----------|
| `127.0.0.1:3000` (the assumed universal gateway) | **No** | No |
| `127.0.0.1:18789` (OpenClaw control UI) | **No** | OpenClaw gateway not running at audit |
| `127.0.0.1:3300` (SwarmRecall API) | **No** | API process not running |
| `127.0.0.1:55432` (PostgreSQL) | **No** | Postgres cold |
| `127.0.0.1:7700` (Meilisearch) | (loopback assumed — single meilisearch process running) | **Yes** |
| `127.0.0.1:11434` (Ollama) | **No** | Ollama installed, not listening |
| `127.0.0.1:27124` (Obsidian REST) | **No** | Obsidian not in MCP mode |

**The single live memory-related listener at audit is Meilisearch.** Everything else is cold and depends on Task Scheduler cold-start tasks to come up at user logon.

---

## 4. Evidence: What the Architecture Documents Actually Say

### 4.1 `master-mcp-server-config.json` (v2026-06-26, `normal_memory_rule`)

> *"normal durable memory now routes through native SwarmRecall (global-memory-gateway retired from the baseline)."*
> *"swarmrecall_mcp_launch: governed wrapper ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp (local-only; strips Upstash/Firebase; credentials from Windows env)"*
> *"swarmvault_mcp_launch: governed wrapper ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp (local-first file vault at F:\AgentCore\agentmemory\swarmvault)"*

This contract is the source authority for "what is the canonical durable memory path." It does **not** mention OpenClaw, `localhost:3000`, OpenAI-compatible APIs, or Lossless Claw as the entry point.

### 4.2 `database-plan.md` §2 (Non-Goals)

- "No LCM/lossless active backend. LCM is a future source-system type only."
- "Normal IDE agents do not write independently to both `agent_core` and `swarmrecall`."

LCM is explicitly **not** the active backend. Routing every IDE through LCM is the opposite of the design intent.

### 4.3 `SYSTEM_HANDOVER_BLUEPRINT.md`

- "Default IDE posture: do not expose direct `SwarmRecall` MCP broadly in v1; keep it as a backend runtime/admin surface."
- "SwarmVault, SwarmRecall, and LCM may provide local retrieval/context paths, but global persistent memory writes must still use `global-memory-gateway` unless the caller is a trusted ingest/admin runner." — *Note: this sentence predates the v2026-06-26 retirement of `global-memory-gateway`; in the current source-of-truth, SwarmRecall is the canonical write surface, with projector-managed fan-out to SwarmVault.*

### 4.4 `memory_system.md` Policy

> *"QMD/LCM-style local memory remains separate and must not bypass the gateway for global memory writes."*

LCM is local retrieval/context, not a routing gateway.

### 4.5 `agentcore-control-plane` HEAD commit (2026-07-01)

> *"Native-first memory: retire global-memory-gateway from baseline"*

The most recent source commit explicitly retires `global-memory-gateway`. OpenClaw as a universal gateway predates and contradicts this design pivot.

---

## 5. Evidence: What the IDEs Actually Need

Per `master-mcp-server-config.json` and the per-IDE renderer fragments, every IDE needs:

- A stdio **MCP** for SwarmRecall (launched via `Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp`).
- A stdio **MCP** for SwarmVault (launched via `Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp`).
- The IDE's own native LLM API (Codex → OpenAI/Anthropic-compatible, Cursor → `https://api.cursor.com`, Claude Code → Anthropic API, Open Interpreter → OpenRouter, MiniMax → `https://agent.minimax.io/mavis/api/v1/llm/v1`).
- For long-form notes, a stdio MCP wrapping Obsidian's local REST API.

None of these are HTTP services on `127.0.0.1:3000`. None route through OpenClaw. None route through Lossless Claw. The IDEs talk to their native LLM APIs directly, and to memory backends through stdio MCP wrappers.

---

## 6. What "Lossless Claw" Actually Is

`C:\Users\ynotf\.openclaw\lossless-claw\`:

- `config.foundation.json` (468 bytes) — local config
- `lcm.sqlite` (4.6 MB) — local SQLite store
- `files\` — local file-based store

Lossless Claw is **a local file-based memory plane**, not an HTTP service. It cannot accept TCP connections. It cannot proxy OpenAI-compatible requests. It cannot route IDE traffic. Its role in the design is local retrieval/context for OpenClaw sessions, not as a gateway.

The "Lossless Claw Gateway" surface referenced in `qmd.foundation.json` is part of the OpenClaw *internal* memory surface, not an externally reachable HTTP gateway.

---

## 7. Why the Assumption Is Plausible (and Wrong)

The assumption conflates four real artifacts:

1. **OpenClaw does have a gateway** — at port 18789, for its own control UI, not for OpenAI-compatible traffic.
2. **OpenClaw does have a Lossless Claw plane** — local file-based memory for OpenClaw sessions.
3. **OpenClaw does have MCP servers** — all stdio, not HTTP.
4. **The architecture does have a governed memory layer** — via SwarmRecall MCP, not via OpenClaw.

A reader who has heard "OpenClaw has a gateway" and "Lossless Claw has memory" might reasonably conclude "OpenClaw + Lossless Claw = universal memory gateway." That conclusion is incorrect: the four pieces belong to four different planes with four different governance rules, and OpenClaw is **one agent among many**, not the central router.

---

## 8. Implications for the Architecture

Any architecture that depends on:

- An OpenAI-compatible endpoint at `127.0.0.1:3000` — **FAILS at startup.**
- An MCP HTTP endpoint at `127.0.0.1:3000/mcp` — **FAILS at startup.**
- Routing all IDEs through OpenClaw's gateway — **contradicts the source contract (v2026-06-26) and the most recent commit.**
- Lossless Claw as a remote HTTP gateway — **impossible; LCM is local files.**

The architecture must instead use:

- **Per-IDE stdio MCP** for SwarmRecall + SwarmVault.
- **Per-IDE native LLM API** (no proxy).
- **Per-IDE Obsidian MCP** for long-form notes where applicable.
- **Task Scheduler cold-start** to bring PostgreSQL + Meilisearch + SwarmRecall API online at user logon.
- **No single router.** Each IDE retains its own native LLM endpoint; the *memory* is shared via MCP, not via an OpenAI-compatible proxy.

---

## 9. Conclusion

The "universal gateway at `localhost:3000`" assumption is **rejected on every measurable dimension**. The architecture must be redesigned around the real surfaces: per-IDE stdio MCP for SwarmRecall/SwarmVault, native LLM APIs per IDE, Task-Scheduler cold-start, and a future unified memory catalog that lets agents discover where to look without needing a single routing gateway. The next deliverable lays out the drive placement plan for those real surfaces.