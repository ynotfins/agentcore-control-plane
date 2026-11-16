# OmniRoute Ops

Commands (PowerShell 7, hidden/background terminals only):
- `omniroute health`, `omniroute health components --alerts-only`, `omniroute status`
- `omniroute quota`, `omniroute cost`, `omniroute usage`
- `omniroute simulate --combo <combo> "<prompt>"` (dry run, no provider call)
- `omniroute combo list`, `omniroute models`

Rules:
- Server is the scheduled task `AgentCore-OmniRoute` (+ watchdog). Never run a second
  `omniroute serve`, never enable `omniroute autostart` (it would start a duplicate server).
- Recommend combo changes; app
