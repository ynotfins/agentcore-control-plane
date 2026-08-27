# Foundry Local Notes (4070 SUPER)

## Purpose
Local GPU inference on NVIDIA GeForce RTX 4070 SUPER. Not cloud memory. Not SwarmRecall. Not PG checkpointer.

## Probe status
- foundry on PATH: False
- GPU: NVIDIA GeForce RTX 4070 SUPER / driver 595.79 / VRAM 12282 MiB
- OPENROUTER_API_KEY present: True (value never printed)

## Operator checklist
1. Install Foundry Local when ready; keep weights on approved hot path.
2. Route tools through agentcore-gateway only.
3. Do not wipe AgentCore or Swarm hot drives for space without a separate plan.
