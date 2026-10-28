# Start OpenHands Runtime

OpenHands is the Docker-first Agent Canvas runtime for this workstation.

Verified live target:

- URL: `http://127.0.0.1:8003/canvas/`
- Readiness: `http://127.0.0.1:8003/ready`
- Container: `openhands-local-8003`
- Image: `ghcr.io/openhands/agent-canvas:1.13.0`
- State bind: `I:\LocalApps\OpenHands\state`
- Project bind: `D:\OpenHandsProjects`
- LLM: OpenRouter only via `OPENROUTER_API_KEY` User env
  - Primary `LLM_MODEL`: `openrouter/z-ai/glm-5.3` (OpenRouter id `z-ai/glm-5.3`)
  - Secondary (SDK/settings profile): `openrouter/deepseek/deepseek-v4.1-flash` (OpenRouter id `deepseek/deepseek-v4.1-flash`)
  - `LLM_BASE_URL`: `https://openrouter.ai/api/v1`
- Media (image/video): **not** routed through OpenHands — ClawTeam `KIE_API_KEY` + ComfyUI only

Rules:

- Publish on localhost only: `127.0.0.1:8003->8000`.
- Do not mount `F:` production AgentCore/LangGraph paths.
- Do not mount `H:` Swarm paths.
- Do not write secrets to `.env` files.
- Use Windows User environment variables for provider keys.

Start from this repo template:

```powershell
Set-Location D:\github\agentcore-control-plane\scripts\maf_recall\openhands
.\Start-OpenHands.ps1
```

If the host-path copy is allowed later, mirror this folder to `I:\LocalApps\OpenHands`.

Final host sync command:

```powershell
Set-Location D:\github\agentcore-control-plane\scripts\maf_recall\openhands
.\Finalize-OpenHandsHost.ps1
```

The finalizer copies these startup assets to `I:\LocalApps\OpenHands`, ensures
`I:\LocalApps\OpenHands\state` and `D:\OpenHandsProjects` exist, starts or reuses
`openhands-local-8003`, removes only the stale created container named `openhands-local`,
and verifies `http://127.0.0.1:8003/ready`.
