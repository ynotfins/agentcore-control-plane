# Devin Outpost Worker (isolated)

Third runtime namespace for Devin — not merged into AgentCore (F:) or Swarm (H:) ownership.

## Bind layout

Host path: I:/LocalApps/Devin/outpost-worker
Container path: /workspace
Purpose: Worker workspace / durable local state

## Hard rules

1. **No docker.sock** — do not mount the Docker socket into the Outpost worker.
2. **No F: or H: production mounts** — do not bind AgentCore or Swarm hot roots by default.
3. **Token from User-scope env** — pass token from Windows User environment at docker run time. Never commit tokens or bake them into the image.
4. **Gateway enrollment only** — use agentcore-gateway at http://127.0.0.1:8080/mcp; do not add raw Recall MCP into Devin configs.

## Build

docker build -t agentcore-devin-outpost:local -f scripts/maf_recall/devin_outpost/Dockerfile scripts/maf_recall/devin_outpost

## Run sketch (operator fills env name; value never echoed)

Ensure directory I:/LocalApps/Devin/outpost-worker exists, then:

docker run -it -v I:/LocalApps/Devin/outpost-worker:/workspace -e DEVIN_API_TOKEN agentcore-devin-outpost:local

Optional: pass Docker auto-remove-on-exit flag if desired. Do not mount F:/ or H:/.
