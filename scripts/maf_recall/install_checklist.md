# MAF Recall Realignment — Install Checklist

Ordered checklist. Check items only with evidence. Do not reorder without an ADR.

## 0. Preconditions
- [ ] Read architecture.md and memory_contract.md
- [ ] Confirm repo D:/github/agentcore-control-plane
- [ ] Secrets = Windows User-scope env only (no .env)
- [ ] Operator profile = high-assistance vibe coder with long natural-language prompts

## 1. Documentation archive on E:
- [ ] Cold/archive under E:/LocalApps/Backups
- [ ] E: is not hot runtime for Bifrost, PG18, Recall, or Docker VHDX

## 2. WSL resource envelope (48 / 16 / 16)
- [ ] Target about 48 GB RAM / 16 processors / 16 GB swap in .wslconfig
- [ ] wsl --shutdown then restart Docker Desktop
- [ ] Record wsl -l -v evidence in audit JSON

## 3. Docker VHDX on F: (not C: or D:)
- [ ] Docker Desktop WSL data under F:/Docker/wsl
- [ ] Verify engine data not on C: or D:
- [ ] Run scripts/maf_recall/docker_tune.ps1
- [ ] App binds on I:/LocalApps

## 4. IDE enrollment (common MCP only)
- [ ] inventory_ide_mcp.ps1
- [ ] enroll_gateway_clients.ps1 for agentcore-gateway http://127.0.0.1:8080/mcp only
- [ ] Auth via BIFROST_MCP_VIRTUAL_KEY (never print)
- [ ] No raw Recall MCP/keys, no :65432 SQL, no OpenRouter MCP, no undocumented extra MCPs

## 4.5 Mandatory helper tools for non-trivial work
- [ ] Sequential Thinking available and treated as required for multi-step tasks
- [ ] Agent memory recovery path available (`startup_context`, `retrieve_context`, handoff flow)
- [ ] Serena or project-local semantic equivalent available before cross-file edits
- [ ] Depwire / Depra-class dependency graph path available for structural edits
- [ ] Tentra available when Milestone or architecture evidence requires it

## 5. Project enrollment default-deny
- [ ] contracts/agentcore-project-enrollment.json exact match before memory R/W

## 6. Devin Outposts
- [ ] Bind I:/LocalApps/Devin/outpost-worker
- [ ] Build scripts/maf_recall/devin_outpost/Dockerfile
- [ ] No docker.sock; no F:/H: production mounts
- [ ] Token from User-scope env

## 6.5 OpenHands Docker-first runtime
- [ ] OpenHands container `openhands-local-8003` running on `127.0.0.1:8003->8000`
- [ ] `http://127.0.0.1:8003/ready` returns 200
- [ ] State bind is `I:/LocalApps/OpenHands/state`
- [ ] Project bind is `D:/OpenHandsProjects`
- [ ] No `F:/` or `H:/` production mounts
- [ ] Compose/startup assets materialized under `I:/LocalApps/OpenHands` when host write scope permits

## 7. MAF SDK pin 1.15.0 later
- [ ] Pin agent-framework==1.15.0 when activated
- [ ] No :8080 bind unless MAF_HOST_BIND=1
- [ ] No new MAF Postgres on F:
- [ ] MAF host preserves long rolling context through gateway memory instead of inventing a second store

## 8. Foundry Local (4070 SUPER)
- [ ] Local inference on 4070 SUPER only
- [ ] Not Foundry cloud memory; not SwarmRecall replacement

## 9. Freeze AgentCore feature work
- [ ] Keep Bifrost until MAF/Recall adapter behind :8080
- [ ] Never wipe F: or H:

## 10. Post-build audit
- [ ] post_build_audit.md + audits/MAF_RECALL_REALIGNMENT_AUDIT_2026-08-26.json
- [ ] docs/handoffs/MAF_RECALL_REALIGNMENT_STATUS_2026-08-26.md
- [ ] Confirm the system helps a vibe coder complete tasks with minimal babysitting and minimal prompt repetition
