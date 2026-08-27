# MAF host spike

## Pin

- requirements.txt pins **agent-framework==1.15.0**
- Treat activation as **later** — after common MCP and Recall adapter path are stable behind Bifrost :8080

## What this is

- A minimal documented spike (host.py) showing how a MAF SDK host should bind behind agentcore-gateway
- Recall context provider placeholder: http://127.0.0.1:3300 (semantic), reached in production via agentcore-memory
- Provider preference is now: **Azure Foundry first**, **OpenRouter fallback second**
- A route-plan guard: keep `http://127.0.0.1:8080/mcp` as the IDE contract, keep Bifrost live, and add MAF policy/middleware behind the gateway only after a separate activation gate.

## What this is not

- Not a second MCP aggregator
- Not a new Postgres on F:
- Not postgres://localhost:5432/agent_memory
- Not a default listener on :8080
- Not direct IDE-to-IDE communication

## Activation gate

The current completion state is **planned and verified**, not hot-swapped. Bifrost remains
the live `:8080` MCP server. A future MAF/Recall activation must prove all of the following
before it replaces or sits in front of any live gateway path:

1. Existing IDEs still use the same `agentcore-gateway` URL.
2. Recall access remains server-side through the governed adapter, never raw IDE SQL or Recall keys.
3. LangGraph checkpoints stay on PG18 `:55433`.
4. SwarmClaw stays independent on `H:` and `:3456`.
5. Azure Foundry `deepseek-v4-pro` remains a provider lane, not a memory plane.

## Run

cd D:/github/agentcore-control-plane/scripts/maf_recall/maf_host
python host.py

With the current workstation cloud lane, `host.py` prefers:

- `AZURE_AI_PROJECT_ENDPOINT` / `FOUNDRY_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME=deepseek-v4-pro`

If Azure Foundry is not configured, it falls back to:

- `OPENROUTER_API_KEY`
- optional `OPENROUTER_MODEL` (default: `deepseek/deepseek-v4-pro`)

To exercise the debug bind guard:

set MAF_HOST_BIND=1
set MAF_HOST_PORT=8091
python host.py

Setting MAF_HOST_PORT=8080 must refuse.
