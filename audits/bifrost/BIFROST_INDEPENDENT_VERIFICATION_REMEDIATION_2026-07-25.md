# Bifrost ChatGPT Profile Persistence, Security, and Output-Schema Final Acceptance

**Date:** 2026-07-26  
**Canonical Repository:** `D:\github\agentcore-control-plane`  
**Bifrost Gateway Version:** `bifrost-http.exe` v2.0.0-prerelease1 (`H:\AgentRuntime\bifrost\bin\bifrost-http.exe`)  
**Status:** `BIFROST_CHATGPT_PROFILE_PASS_WITH_OUTPUTSCHEMA_LIMITATION`  

---

## 1. Executive Summary

This audit records the final independent verification and remediation of the Bifrost/ChatGPT MCP surface.
The dedicated Windows User-scope environment variable `BIFROST_MCP_VK_CHATGPT` was verified as present (length: 42 characters) and never exposed or modified.

A source-controlled, narrow capability profile for ChatGPT was established in `contracts/bifrost-upstream-mcp-registry.json` and rendered into `renderers/bifrost/config.json` and `H:\AgentRuntime\bifrost\config.json`.
The compatibility proxy (`C:\Users\ynotf\.config\tunnel-client\agentcore-mcp-compat-proxy.cjs`) was updated to enforce `BIFROST_MCP_VK_CHATGPT` as its sole upstream authorization header and strict 403 path filtering.

Two complete restart cycles of the dependency stack (1. Bifrost Gateway → 2. AgentCore ChatGPT Compatibility Proxy → 3. OpenAI Tunnel Client) were executed, proving full restart persistence.
An outputSchema layer-by-layer evaluation across 4 layers was performed, identifying a known Bifrost v2.0.0-prerelease1 passthrough limitation.

---

## 2. Root Cause of Prior Disappearing Dashboard Key & Ownership Model

### Root Cause
Previously, a ChatGPT virtual key was created directly in the Bifrost web dashboard/database (`data/config.db`). Because Bifrost operates with `source_of_truth: "config.json"`, any profile or key present in `config.db` that is absent from `config.json` is pruned or overwritten whenever configuration reconciliation occurs or when `renderers/bifrost/config.json` is copied to `H:\AgentRuntime\bifrost\config.json` on restart.

### Ownership Model
- **Source Authority:** `D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json` and `renderers/bifrost/config.json`.
- **Secret Value Authority:** Dedicated Windows User-scope environment variable `BIFROST_MCP_VK_CHATGPT` (and User-scope `BIFROST_MCP_AUTHORIZATION = Bearer <BIFROST_MCP_VK_CHATGPT>`). Never committed to Git or printed in logs.
- **Runtime Authority:** `H:\AgentRuntime\bifrost\config.json`, which references `"value": "env.BIFROST_MCP_VK_CHATGPT"`.
- **Reconciliation Invariant:** Source renderer, runtime config, Bifrost database, and dashboard agree semantically on all 6 virtual key profiles (`builder`, `reviewer`, `database-validator`, `docs-knowledge`, `operator`, `chatgpt`).

---

## 3. Normalized ChatGPT Profile & Permission Boundaries

The ChatGPT virtual key profile (`vk-agentcore-chatgpt`) is strictly limited to 21 explicit tools across 5 upstream servers without any wildcard (`*`) permissions:

### Allowed Surface (21 Explicit Tools):
1. **`agentcore_memory` (9 tools):**
   - `memory_status`
   - `startup_context`
   - `retrieve_context`
   - `expand_source`
   - `docs_search`
   - `session_open`
   - `append_event`
   - `build_handoff`
   - `session_close`
   *(Explicitly excluded: `propose_fact`)*

2. **`agentcore_project_router` (3 tools):**
   - `project_list`
   - `project_status`
   - `project_activate`
   *(Explicitly excluded: `project_clear`)*

3. **`skills_hub` (3 tools):**
   - `search_skills`
   - `get_skill_detail`
   - `list_installed_skills`
   *(Explicitly excluded: `install_skill`)*

4. **`arabold_docs` (5 tools):**
   - `search_docs`
   - `fetch_url`
   - `list_libraries`
   - `find_version`
   - `get_job_info`

5. **`sequential_thinking` (1 tool):**
   - `sequentialthinking`

### Explicitly Excluded Systems & Capabilities:
- `project_clear`
- `propose_fact`
- `filesystem` (read/write/edit/directory)
- `shell execution`
- `Playwright` browser automation
- `Serena` semantic code intelligence
- `Depwire` dependency graph
- `Tentra` architecture indexer
- `cursor-agent-mcp` cloud agent bridge
- `Context Fabric` drift capture
- `OpenRouter` generation
- `skills_hub-install_skill`
- `database administration`
- `Bifrost administration`
- `Firebase`
- `Google Sheets`
- `Swarm` ecosystem
- Every wildcard pattern (`*`)

Confirmation prompts remain enabled for all allowed write operations.

---

## 4. Compatibility Proxy & Tunnel Client Enforcement

### Compatibility Proxy (`C:\Users\ynotf\.config\tunnel-client\agentcore-mcp-compat-proxy.cjs`)
- **Listen Address:** `127.0.0.1:18081`
- **Target Address:** `http://127.0.0.1:8080` (Bifrost Gateway)
- **Path Allowlist:** `/mcp`, `/.well-known/oauth-protected-resource*`, `/.well-known/oauth-authorization-server`, `/.well-known/openid-configuration`, `/healthz`, `/readyz`
- **Denied Paths (403 Forbidden):** `/`, `/api/*`, `/workspace/*`, `/v1/*`, `/logs*`, `/dashboard*`, `/ui/*`, `/internal/*`
- **Authorization Enforcement:** Proxy explicitly sets `clean.authorization = "Bearer " + process.env.BIFROST_MCP_VK_CHATGPT` on every request forwarded to Bifrost.
- **No Fallback:** Proxy does not fall back to `BIFROST_MCP_VIRTUAL_KEY`, `builder`, `operator`, or any other key.

### Tunnel Client (`C:\Users\ynotf\.config\tunnel-client\agentcore-gateway.yaml`)
- **Listen/Health Address:** `127.0.0.1:18080`
- **Tunnel ID:** `tunnel_6a639990937c81918bd92f9a9cbcefe9`
- **Command:** `tunnel-client.exe run --config C:\Users\ynotf\.config\tunnel-client\agentcore-gateway.yaml`
- **Status:** Connected and active (`🟢 tunnel-client started`).

---

## 5. Restart Persistence Proof

Two complete stop/start cycles of the dependency stack were executed using `scripts/bifrost/restart_and_verify.py`.

### Dependency Start Sequence:
1. Bifrost Gateway (`\AgentCore\AgentCore-Bifrost-Gateway`)
2. AgentCore ChatGPT Compatibility Proxy (`node agentcore-mcp-compat-proxy.cjs`)
3. OpenAI Tunnel Client (`tunnel-client.exe run ...`)

### Results Across Both Cycles:
- **Bifrost Health (8080/health):** 200 OK (`{"components":{"db_pings":"ok"},"status":"ok"}`)
- **Proxy Health (18081/healthz):** 200 OK (`ok`)
- **Profile Config Check:** PASS (`vk-agentcore-chatgpt` present with 5 clients in runtime `config.json`)
- **Direct MCP Auth & Filtering (8080):** PASS (21 tools returned, 0 missing, 0 extra)
- **Proxy MCP Auth & Filtering (18081):** PASS (21 tools returned, 0 missing, 0 extra)
- **Proxy Path Security Enforcement:** PASS (7/7 prohibited paths returned 403 Forbidden)
- **Environment Inheritance:** PASS (`BIFROST_MCP_VK_CHATGPT` present in process env)
- **No Fallback / Leak:** PASS (Zero builder/operator tools exposed; tool count strictly 21)

---

## 6. Output-Schema Layer-by-Layer Report

| Layer | Surface / Endpoint | inputSchema | outputSchema | structuredContent | annotations | Status / Notes |
|---|---|---|---|---|---|---|
| **Layer A** | Native AgentCore stdio (via adapter) | Present (14/14) | Present (14/14) | Returned | Present (14/14) | Complete (injected by `mcp_output_schema_adapter.py`) |
| **Layer B** | Bifrost Builder Profile (8080/mcp) | Present (14/14) | Absent (0/14) | Returned | Present (14/14) | `outputSchema` stripped by Bifrost v2.0.0-prerelease1 |
| **Layer C** | Bifrost ChatGPT Profile Proxy (18081/mcp) | Present (12/12) | Absent (0/12) | Returned | Present (12/12) | `outputSchema` stripped by Bifrost v2.0.0-prerelease1; 2 excluded tools absent |
| **Layer D** | ChatGPT Custom-App Action Snapshot | Present | Absent | Returned | Present | Matches Layer C surface |

### Classification & Finding:
`outputSchema` exists at Layer A (native stdio with normalizer) but is stripped at Layer B and Layer C by the Bifrost v2.0.0-prerelease1 gateway passthrough implementation.
This is classified as a **Bifrost v2.0.0-prerelease1 passthrough limitation**. Upstream AgentCore tools are NOT defective, correct annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) are preserved, and schemas are not fabricated in the proxy.

---

## 7. Full Regression Suite Results

| Test / Audit | Result | Notes |
|---|---|---|
| Bifrost Contract Validators | **PASS** | `validate_contracts.py` & `test_contracts.py` (124 checks) |
| Source / Runtime / DB Parity | **PASS** | `renderers/bifrost/config.json` & `H:\AgentRuntime\bifrost\config.json` aligned |
| Actual ChatGPT-Key Auth | **PASS** | Direct (8080) and Proxy (18081) JSON-RPC MCP initialize & tools/list |
| Proxy Path Security | **PASS** | 7/7 prohibited paths returned 403 Forbidden |
| 10 AgentCore Memory Tools | **PASS** | 9 exposed in ChatGPT profile (`propose_fact` excluded) |
| 4 Project Router Tools | **PASS** | 3 exposed in ChatGPT profile (`project_clear` excluded) |
| Cursor Stage B Suite | **PASS** | 26/26 comprehensive checks passed (`test_stage_b_suite.py`) |
| LangGraph E2E Fixture | **PASS** | 17/17 checks passed (`scripts.agentcore_workflow.tests.fixture_e2e`) |
| Swarm Exclusion Boundary | **PASS** | 0 Swarm entries in Cursor mcp.json or ChatGPT profile |
| Cursor MCP Entry Count | **PASS** | Exactly 1 entry (`agentcore-gateway` in `C:\Users\ynotf\.cursor\mcp.json`) |
| Secret & Junk Scan | **CLEAN** | No secret literals committed; `.env` files absent |

---

## 8. Backup & Rollback Evidence

- **Timestamped Backup:** `E:\AgentCore-Backups\agentcore-control-plane\bifrost-chatgpt-final-20260725-233205`
- **Manifest:** `MANIFEST.sha256` verified containing source renderer, runtime config, SQLite config.db, compatibility proxy, tunnel-client config, and scheduled task XML.
- **Rollback Procedure:**
  1. Restore `renderers/bifrost/config.json` and `H:\AgentRuntime\bifrost\config.json` from backup.
  2. Restore `C:\Users\ynotf\.config\tunnel-client\agentcore-mcp-compat-proxy.cjs` from backup.
  3. Run `ops/bifrost/Stop-AgentCoreBifrostGateway.ps1` and `ops/bifrost/Start-AgentCoreBifrostGateway.ps1`.

---

## 9. Files Changed

- `contracts/bifrost-upstream-mcp-registry.json` — added `chatgpt` profile and server capability mappings.
- `scripts/bifrost/render_bifrost_config.py` — added `BIFROST_MCP_VK_CHATGPT` secret handling and explicit `chatgpt` profile tool mapping.
- `renderers/bifrost/config.json` — rendered source config containing `vk-agentcore-chatgpt`.
- `renderers/bifrost/config.sanitized.json` — rendered sanitized sidecar containing `vk-agentcore-chatgpt`.
- `H:\AgentRuntime\bifrost\config.json` — rendered live runtime config containing `vk-agentcore-chatgpt`.
- `C:\Users\ynotf\.config\tunnel-client\agentcore-mcp-compat-proxy.cjs` — updated to strictly enforce `BIFROST_MCP_VK_CHATGPT` and syntax error fixed.
- `scripts/bifrost/update_compat_proxy.py` — tool script to update compat proxy.
- `scripts/bifrost/verify_chatgpt_profile.py` — verification test suite for ChatGPT profile and tool filtering.
- `scripts/bifrost/restart_and_verify.py` — 2-cycle restart persistence orchestrator.
- `scripts/bifrost/test_layers_output_schema.py` — layer-by-layer outputSchema evaluation script.
- `audits/bifrost/BIFROST_INDEPENDENT_VERIFICATION_REMEDIATION_2026-07-25.md` — this audit report.

---

## 10. Final Result Code

```
BIFROST_CHATGPT_PROFILE_PASS_WITH_OUTPUTSCHEMA_LIMITATION
```
