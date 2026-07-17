# Biggest friction points

## Friction point 1 — Current security blockers

The system has serious local-service exposure: Qdrant, RDP, and Portainer are LAN-exposed, and Claude Desktop has a plaintext Obsidian key finding. These are the first things to fix before full autonomy.

## Friction point 2 — Docker hot data is on C:

n8n Postgres and Qdrant write through Docker’s C: VHDX. This competes with OS/IDE load and complicates direct backup. F: is nearly empty and purpose-built for this workload.

## Friction point 3 — MCP write scope is too broad

The filesystem MCP currently overlaps with user home, Obsidian, F: AgentCore, and archive paths. This should be split into narrow read-only and swarm-write profiles.

## Friction point 4 — Obsidian has duplicate write paths

The active vault is on D:, but Claude Desktop references a Dropbox duplicate. That creates a corruption/sync-conflict risk unless D: is canonical and Dropbox is read-only.

## Friction point 5 — Restore validation is not clean

`NightlyRestoreTest` and `DailyDriftCheck` have non-zero/check results in the docs/manifest. That does not necessarily mean the runtime is broken, but it means the backup/restore loop cannot be considered proven yet.

## Friction point 6 — Missing physical details

PSU, cooler, case airflow, M.2 slot labels, lane sharing, and drive health are unknown. That blocks confident hardware upgrades.

## Friction point 7 — Toolchain version conflicts

Multiple Python versions are installed, Java PATH and `JAVA_HOME` differ, Gradle/Maven are not in PATH, and Cursor CLI is not in PATH. Autonomous agents must use explicit paths and per-project venvs.

***

# 18. Upgrades that make the biggest difference

## Tier 0 — Safety upgrades

1. **Restrict Qdrant to loopback.**
Change Docker port binding from `0.0.0.0:6333/6334` to `127.0.0.1:6333/6334`.
2. **Rotate the Claude Desktop Obsidian key.**
Replace plaintext key with environment-variable reference.
3. **Restrict RDP and Portainer.**
Use firewall rules, strong auth, and loopback-only exposure unless remote access is intentionally required.
4. **Narrow filesystem MCP roots.**
Remove broad `C:\Users\ynotf`, `D:\Obsidian`, and `F:\AgentCore` write scope from default autonomous operation.
5. **Create a dedicated low-privilege runner profile.**
Run autonomous builds under a Windows account that cannot write system/config/secrets paths.

## Tier 1 — Performance and reliability upgrades

1. **Move Docker DB/vector volumes from C: VHDX to F: bind mounts.**
2. **Create `D:\AgentSwarm` run/worktree/artifact structure.**
3. **Use git worktrees for A/B branches.**
4. **Add a Memory Write Broker with Postgres advisory locking.**
5. **Make graph state reference-based, not transcript-heavy.**
6. **Use deterministic scoring from tests/scans/coverage/perf, not LLM-only scoring.**
7. **Fix NightlyRestoreTest and DailyDriftCheck.**
8. **Add Docker volume backup coverage.**

## Tier 2 — Agent-quality upgrades

1. **Convert the 23-agent design into 6 runtime hubs.**
2. **Use local Ollama for summarization/log clustering only.**
3. **Use frontier models for architecture, security review, hard debugging, and final judge.**
4. **Add prompt-injection tests for issues, docs, webpages, and logs.**
5. **Add PR templates with test evidence, diff summary, rollback plan, and memory update proposal.**
6. **Pin MCP/tool versions where possible.**
7. **Add per-agent allowlists: tools, paths, ports, env var names, cost limits.**

## Tier 3 — Hardware/software cleanup

1. **Move `D:\HF_Cache` and `D:\models` to E: if they are mostly cold/read-only.**
2. **Install missing build tools only when repo needs them: Gradle/Maven, ripgrep, jq, fd, uv, ruff, pytest, pnpm tooling, etc.**
3. **Physically inspect M.2/PCIe/PSU/cooling before any hardware purchase.**
4. **Optional later: add a dedicated 2–4 TB Gen4 NVMe for Docker/WSL only, after inspection.**
**----------------------------------------------------------------------------------------------------------------------------------------**
CHAOSCENTRAL — Workflow Engineering, Software Selection, and Bottleneck Reference
5. Machine: `CHAOSCENTRAL`  
6. Purpose: One-file reference for engineering an autonomous software-development workflow, choosing the best workflow software, and finding bottlenecks before they become failures.  
7. Generated for: Tony / ChaosCentral autonomous developer-team design  
8. Generated on: 2026-06-28  
9. Evidence baseline: `Output-Specs.zip`, `Output (2).zip`, `ChaosCentral-Current-Build.zip`, `23 Agent Team.md`, root ChaosCentral source-of-truth docs, and current official framework/security docs.  
10. Secrets policy: This file must never contain secret values. Environment variable names are allowed; values are always `[REDACTED]`.
11. ---
12. 0. Read-this-first design thesis
13. `CHAOSCENTRAL` is not just a coding PC. It is a high-end local autonomous software factory with a dedicated hot memory/vector tier, multiple AI IDEs, local RAG infrastructure, a canonical AgentCore memory plane, and enough CPU/RAM to run aggressive local orchestration. The machine should not be treated like a normal developer laptop and should not run a 23-agent swarm as 23 independent heavy model loops.
14. The best workflow for this exact PC is:
15. ```text
16. D: isolated code worktrees, repos, build artifacts, workflow run evidence
17. F: API-only hot memory/vector/database tier through AgentCore, pgvector, SwarmRecall, SwarmVault, Meilisearch, Qdrant after remediation
18. E: cold archive, model/cache offload, Codex memory exports after directory creation
19. G: backup target only
20. C: OS, apps, IDE configs, Docker Desktop runtime only; stop adding hot data here
21. ```
22. The best autonomous developer-team topology is:
23. ```text
24. Human / Issue / Cursor prompt / GitHub issue
25.         │
26.         ▼
27. [1] Intake + Policy Hub
28.         │
29.         ▼
30. [2] Context / Architecture / RAG Hub
31.         │
32.         ├──────────────┬──────────────┐
33.         ▼              ▼              ▼
34. [3] Main Builder   [4] A/B Builder   read-only memory/RAG layer
35.         │              │
36.         └──────┬───────┘
37.                ▼
38. [5] Verification + Critic Hub
39.                │
40.                ▼
41. [6] Governance / PR / Memory-Broker Hub
42.                │
43.                ├── PR only, no direct main merge
44.                ├── deterministic checks before LLM judgment
45.                ├── memory write through single broker only
46.                └── docs update through one vault/document writer only
47. ```
48. The current 23-agent design is useful as a role taxonomy, but it should be executed as six runtime hubs with strict locks, not as 23 free-running agents. This avoids context bloat, critic loops, branch collisions, memory inconsistency, and uncontrolled tool access.
49. ---
50. 0.1 Highest-leverage decisions
51. Decision	Recommendation	Reason
52. Primary orchestrator	LangGraph	Best fit for long-running, stateful, branchy workflows with persistence, failure recovery, human review, memory, and traceability.
53. Tool/agent SDK inside hubs	OpenAI Agents SDK where useful	Good fit when application code owns tool execution, approvals, state, guardrails, MCP, and observability.
54. Primary local IDE	Cursor	Already installed, primary workspace, live MCP config, familiar human/operator surface.
55. Parallel local code execution	Git worktrees under `D:\AgentSwarm\runs\<run_id>\`	Prevents main/A-B branches from corrupting the same working tree.
56. Cloud comparator	GitHub Copilot cloud agent / Codex cloud where available	Good external PR-generation comparator; keep separate from local memory plane.
57. Local memory system	AgentCore PostgreSQL :55432 + SwarmRecall + SwarmVault	Already local, persistent, and placed on F: hot NVMe.
58. Vector DB	pgvector as canonical memory vector layer; Qdrant after loopback + F: migration	Reduces system complexity while keeping Qdrant available for high-performance vector workloads.
59. Local model use	Ollama for low-risk summarization and log clustering only	RTX 4070 SUPER has 12 GB VRAM; do not use local 30B model as final judge/security architect.
60. Merge policy	PR-only, protected main	Agents can branch, test, and create PRs, but should not directly merge/deploy.
61. Memory writes	Single Memory Write Broker	Prevents 23-agent write races into `agent_core`, SwarmRecall, SwarmVault, or Obsidian.
62. Obsidian writes	One writer, REST-only, no filesystem writes to active vault	Active Obsidian + Syncthing + duplicate tooling can corrupt notes.
63. Docker DB placement	Migrate n8n Postgres + Qdrant volumes from C: VHDX to F: bind mounts	Major I/O, backup, and capacity improvement.
64. ---
65. 0.2 Immediate blockers before full autonomy
66. These are the items that can cause real damage or false confidence if ignored:
67. Plaintext Obsidian API key in Claude Desktop config. Rotate it and replace with environment-variable access.
68. Qdrant `6333/6334` bound to `0.0.0.0`. Bind to `127.0.0.1`; use API key if any non-local access remains.
69. RDP `3389` and Portainer `9443/8005` bound to `0.0.0.0`. Restrict with firewall rules and strong authentication.
70. Filesystem MCP has broad roots, including user home, Obsidian, F: AgentCore, and archive paths. Split into read-only and narrow write profiles.
71. Current raw 23-agent Git examples use one working directory and fixed branch names. Replace with per-run git worktrees.
72. Direct memory writes by many agents will race. Route all writes through one broker.
73. Docker hot data is still on C: Docker VHDX. Move n8n and Qdrant volumes to F: bind mounts.
74. `PostgresRuntime`, `SwarmRecallApi`, and `SwarmRecallMeilisearch` scheduled tasks show anomalous last result values despite listeners being up. Investigate task actions before relying on scheduled-task restarts.
75. Many repos are dirty. Autonomous agents must refuse write operations in dirty repos unless the run explicitly records the baseline diff and owner approval.
76. Ollama was not listening at the latest scan. Any workflow expecting local model inference must verify `127.0.0.1:11434` before routing tasks there.
77. ---
78. 0.3 Source authority and conflict resolution
79. When facts conflict, use this order:
80. AgentCore authority: `D:\github\agentcore-control-plane` for AgentCore policy, runtime contracts, DB/memory governance.
81. Latest ecosystem evidence: `Output (2).zip` / `SYSTEM_ECOSYSTEM_REFRESH.md` / `system-ecosystem-20260627-194037.json` for live ports, tasks, versions, containers.
82. Latest physical/spec evidence: `Output-Specs.zip` / `chaoscentral-hardware-software.md` for case, PSU, airflow, M.2 occupancy, physical topology.
83. ChaosCentral root docs: stable source-of-truth files in `D:\ChaosCentral-Current-Build`.
84. 23 Agent Team.md: conceptual design and prototype; useful, but some code/path assumptions are not PC-optimized and must be corrected.
85. `ChaosCentral-Current-Build` is an evidence and planning workhorse. It should not become a second AgentCore control plane.
86. ---
87. 
88. 0.4 How to use this file
89. For fast workflow engineering, read these sections first:
90. Need	Go to
91. One-page machine model	`0`, `0.1`, `0.2`, `QUICK-START MACHINE IDENTITY CARD`
92. Exact hardware limits	`PART 1`, `PART 12`, `PART 14`
93. Storage and path placement	`1.3`, `1.4`, `PART 11`, `PART 19`
94. Software/tool choice	`PART 2`, `PART 17`
95. Databases/vector/RAG	`PART 3`, `PART 20`
96. MCP/tool risk	`PART 4`, `PART 19`
97. Ports/security exposure	`PART 5`, `PART 9`, `18.1`
98. Automation and service health	`PART 6`, `22.1`, `22.3`
99. Backup/DR gaps	`PART 10`, `23.1`, `23.2`
100. Autonomous workflow design	`PART 13`, `PART 16`, `PART 20`, `PART 21`
101. Bottleneck hunting	`PART 18`
102. Upgrade roadmap	`PART 23`
103. For agents: read sections `0`, `0.1`, `0.2`, `0.3`, `16`, `19`, `20`, `21`, and the relevant subsystem section before taking action.
104. ---
105. PART 1–15 — COMPLETE MACHINE BASELINE
106. QUICK-START MACHINE IDENTITY CARD
107. Field	Value
108. Hostname	`CHAOSCENTRAL`
109. OS	Windows 11 Pro 10.0.26200 (installed 2026-01-17)
110. CPU	Intel Core i9-14900KF — 24 cores / 32 threads, LGA1700
111. RAM	128 GB DDR5 — 4× 32 GB Team Group UD5-6000 @ 4200 MT/s — all slots full
112. GPU	NVIDIA RTX 4070 SUPER — 12 GB GDDR6X — vertically mounted via PCIe riser
113. Motherboard	ASUS Z790 GAMING WIFI7 Rev 1.xx — BIOS 1805 (2024-10-29)
114. Case	NZXT Y70 Silver Wolf
115. PSU	Corsair RM1000 — 1000 W, 80+ Gold — ~600 W headroom
116. Fans	7 case fans, left-to-right airflow
117. Tailscale IP	`100.111.111.124`
118. LAN IP	`192.168.1.156`
119. Time zone	Eastern (UTC-05:00)
120. GPU live stats	12 GB total / ~2.7 GB used / 9.3 GB free — 44°C — 25 W / 220 W — 7–25% utilization
121. ---
122. PART 1 — HARDWARE TOPOLOGY
123. 1.1 Motherboard and PCIe
124. Field	Value
125. Board	ASUS Z790 GAMING WIFI7 Rev 1.xx
126. Chipset	Intel Z790
127. Socket	LGA1700
128. BIOS	AMI 1805, 2024-10-29
129. M.2 slots present	M.2_1, M.2_2, M.2_3 (confirmed on board)
130. M.2 slots occupied	3 / 3 — ALL OCCUPIED (confirmed by physical inspection 2026-06-27)
131. Free M.2 slots	NONE
132. M.2 slot-to-drive mapping	NOT RECORDED during inspection — requires follow-up
133. GPU mount	Vertical (floor) mount via PCIe riser, ~6 in. from board
134. GPU slot label	NOT RECORDED
135. PCIe riser generation	NOT RECORDED
136. Other PCIe slots	NOT RECORDED
137. SATA ports/cables	NOT RECORDED
138. Expansion rule: No new M.2 NVMe can be added without removing an existing drive. Options are drive replacement, PCIe NVMe expansion card (free PCIe slot required, unconfirmed), or USB NVMe enclosure (not suitable for databases).
139. 1.2 Storage Devices
140. Drive	Model	Interface	Size	Drive letter	Volume label	Role
141. Internal NVMe	T-FORCE TM8FFW002T	PCIe NVMe	1.91 TB	C:	—	OS + user profile + Docker VHDX
142. Internal NVMe	T-FORCE TM8FFW002T	PCIe NVMe	1.91 TB	D:	New Volume	Dev workspaces + vaults + MCP
143. Internal NVMe	Samsung 990 PRO 4TB (heatsink)	PCIe Gen4	3.64 TB	F:	Agent_Vector_4TB	Hot DB + vectors
144. External USB	PRO X Avolusion	USB bridge	5.59 TB	E:	Agent_Core_6TB	Cold archive
145. External USB HDD	Seagate BUP BK	USB HDD	3.64 TB	G:	Seagate Backup Plus	External backup
146. 1.3 Storage Capacity (live, 2026-06-27)
147. Letter	Total	Free	Used%	Status
148. C:	1.91 TB	629 GB	67%	Watch — approaching 80% threshold
149. D:	1.91 TB	893 GB	53%	OK
150. E:	5.59 TB	5.59 TB	<1%	Vast free space — underused
151. F:	3.64 TB	3.72 TB	<1%	Vast free space — DB tier
152. G:	3.64 TB	2.17 TB	42%	OK — backup target
153. C: warning threshold: 80% = ~1.53 TB used (currently at 1.28 TB — ~250 GB until warning)  
154. Docker VHDX on C:: `docker_data.vhdx` = 14.08 GB, growing with every container build
155. 1.4 Drive Role Map (complete workload → path → drive)
156. Workload	Path	Drive
157. Windows OS	`C:\Windows\`	C:
158. 
159. User profile / app data	`C:\Users\ynotf\`	C:
160. Cursor install	`...\AppData\Local\Programs\cursor\`	C:
161. Cursor MCP config	`C:\Users\ynotf\.cursor\mcp.json`	C:
162. Cursor global storage	`...\Cursor\User\globalStorage\` (~13 GB)	C:
163. VS Code install + config	`...\Microsoft VS Code\` + `...\Code\User\`	C:
164. Android Studio + SDK	`C:\Program Files\Android\...` + `...\Android\Sdk\`	C:
165. ClawX binary	`C:\Program Files\ClawX\`	C:
166. OpenClaw config	`C:\Users\ynotf\.openclaw\`	C:
167. Codex home	`C:\Users\ynotf\.codex\`	C:
168. Codex skills	`C:\Users\ynotf\.agents\skills\`	C:
169. Ollama binary	`...\Programs\Ollama\ollama.exe`	C:
170. Open Interpreter	`...\Programs\Open Interpreter\`	C:
171. MiniMax Code	`...\Programs\MiniMax Code\`	C:
172. Docker Desktop	`C:\Program Files\Docker\`	C:
173. Docker WSL VHDX	`...\Docker\wsl\disk\docker_data.vhdx` (14 GB, growing)	C: ⚠ MIGRATE
174. n8n Postgres volume	Docker vol `local-agent-stack_postgres_data`	C: via VHDX ⚠
175. Qdrant Docker volume	Docker vol `agentops_qdrant_storage`	C: via VHDX ⚠
176. ChaosCentral SOT docs	`D:\ChaosCentral-Current-Build\`	D:
177. Primary dev monorepo	`D:\Autonomy\` (~98 GB)	D:
178. Codex managed workspace	`D:\Codex_Managed\` (~1.1 GB) + Python venv	D:
179. AgentOps infra / Qdrant compose	`D:\AgentOps\`	D:
180. MCP control plane	`D:\MCP-Control-Plane\`	D:
181. GitHub repos	`D:\github\`, `D:\github_2\`	D:
182. Obsidian active vault	`D:\Obsidian\Dungeon Vault\`	D:
183. Obsidian secondary vault	`D:\Obsidian\Obsidian Vault\`	D:
184. Global projects vault	`D:\Projects-Global\`	D:
185. HF model cache	`D:\HF_Cache\`	D: ⚠ should move to E:
186. LLM models	`D:\models\`	D: ⚠ should move to E:
187. Autonomy backups	`D:\Autonomy\Backups\`	D: ⚠ should move to G:/E:
188. SENSITIVE — human only	`D:\Autonomy\secrets-backups\`	D:
189. Agent Postgres DB (native)	`F:\AgentCore\database_cluster\`	F: — DO NOT MOVE
190. Postgres runtime binaries	`F:\AgentCore\postgres_runtime_engine\pgsql\bin\`	F:
191. AgentCore memory workspace	`F:\AgentCore\agentmemory\`	F:
192. SwarmRecall data	`F:\AgentCore\agentmemory\swarmrecall\`	F:
193. SwarmVault	`F:\AgentCore\agentmemory\swarmvault\`	F:
194. Projection state	`F:\AgentCore\agentmemory\projection-state\`	F:
195. Qdrant native dir	`F:\VectorDB\qdrant\`	F:
196. Chroma native dir	`F:\VectorDB\chroma\`	F:
197. LanceDB native dir	`F:\VectorDB\lancedb\`	F:
198. pgvector artifacts	`F:\VectorDB\pgvector\`	F:
199. Agent core archive	`E:\AgentCoreArchive\`	E:
200. Codex memory exports	`E:\CodexMemory\` — DOES NOT EXIST (env var set but path absent)	E:
201. Backup target	`G:\`	G:
202. 1.5 Paths That Must Not Be Moved
203. Path	Reason
204. `C:\Users\ynotf\.cursor\mcp.json`	Live Cursor MCP runtime — hardcoded by IDE
205. `D:\Codex_Managed\.venv\Scripts\python.exe`	Hardcoded in `mcp.json` global-memory-gateway command
206. `F:\AgentCore\database_cluster\`	Live Postgres data dir — stop `\AgentCore\PostgresRuntime` first
207. `F:\AgentCore\postgres_runtime_engine\`	Postgres binary referenced by scheduled task
208. `D:\Obsidian\Dungeon Vault\`	Active Obsidian vault — single writer policy
209. `D:\Autonomy\secrets-backups\`	Sensitive — no agent access
210. ---
211. PART 2 — SOFTWARE TOOLCHAIN (live, 2026-06-27)
212. 2.1 Core Runtimes
213. Tool	Version	Path
214. PowerShell	7.5.5	`C:\Program Files\PowerShell\7\pwsh.exe`
215. Node.js	v24.16.0	`C:\Program Files\nodejs\node.exe`
216. npm	11.13.0	nodejs dir
217. pnpm	11.7.0	Corepack shim
218. yarn	1.22.22	Corepack shim
219. Python 3.13 (default)	3.13.14	`...\Python313\python.exe`
220. Python 3.11 (legacy uvx path; not Serena default)	3.11.9	`...\Python311\Scripts\uvx.exe`
221. Python 3.12	3.12	MSIX
222. Python 3.10	3.10.11	winget
223. pip	26.1.2	Python 3.13 Scripts
224. uv	0.11.21	WinGet package
225. uvx	0.11.21	WinGet package
226. Java (PATH)	OpenJDK 21.0.11 LTS	Eclipse Adoptium JDK 21
227. JAVA_HOME	JDK 17.0.16	`...\jdk-17.0.16.8-hotspot\`
228. Git	2.51.1	`C:\Program Files\Git\cmd\git.exe`
229. GitHub CLI	2.93.0	`C:\Program Files\GitHub CLI\gh.exe`
230. Docker CLI	29.5.2	`C:\Program Files\Docker\...`
231. Docker Compose	v5.1.4 (plugin)	`docker compose`
232. WSL	2.6.1.0	`C:\Windows\system32\wsl.exe`
233. winget	v1.29.280	—
234. ripgrep (rg)	15.1.0-cursor5	Cursor bundled
235. Not found in PATH: gradle, mvn, rustc, cargo, go, fd, jq
236. 2.2 IDEs and Agent Runtimes
237. 
238. Application	Version	Install path	Config
239. Cursor	1.126.0	`...\Programs\cursor\_\Cursor.exe`	`~/.cursor/mcp.json`
240. VS Code	1.126.0	`...\Microsoft VS Code\`	`AppData/Roaming/Code/User/`
241. Android Studio	2025.3	`C:\Program Files\Android\Android Studio\`	`AppData/Google/AndroidStudio*/`
242. OpenAI Codex	26.623.4041.0	WindowsApps MSIX	`C:\Users\ynotf\.codex\`
243. ClawX / OpenClaw	0.4.12	`C:\Program Files\ClawX\`	`~/.openclaw/openclaw.json`
244. MiniMax Code	—	`...\MiniMax Code\`	`~/.minimax/mcp/mcp.json`
245. Mavis	—	detected	`~/.mavis/mcp/mcp.json`
246. ChatGPT Desktop	1.2026.133.0	MSIX	—
247. Ollama	0.24.0	`...\Programs\Ollama\`	env vars
248. Open Interpreter	—	`...\Open Interpreter\`	`:5177`
249. Obsidian	1.12.7	`C:\Program Files\Obsidian\`	`AppData/Roaming/obsidian/`
250. Standard Notes	3.201.2	`@standardnotesinner-desktop`	`AppData/Roaming/@standardnotes/`
251. 2.3 Python Virtual Environments
252. venv	Path	Used by
253. Memory gateway	`D:\Codex_Managed\.venv\`	global-memory-gateway MCP — hardcoded path
254. Others	NOT exhaustively scanned	Per-project
255. ---
256. PART 3 — DATABASE AND VECTOR RUNTIME
257. 3.1 Active Services (all verified listening, 2026-06-27)
258. Service	Type	Port	Bind	Drive	Status
259. agent_core	PostgreSQL (native)	55432	127.0.0.1	F: Samsung 990 PRO	✅ Running
260. SwarmRecall API	Node.js API	3300	127.0.0.1	F:	✅ Running
261. Meilisearch	Full-text search	7700	127.0.0.1	UNKNOWN	✅ Running
262. n8n Postgres	PostgreSQL 18 (Docker)	5432	127.0.0.1	C: VHDX	✅ Running
263. Qdrant	Vector DB (Docker)	6333 / 6334	0.0.0.0	C: VHDX	✅ Running — LAN EXPOSED
264. n8n	Workflow automation	5678	127.0.0.1	C: VHDX	✅ Running
265. Ollama	LLM runtime	11434	127.0.0.1	—	⚠ Not listening at scan time
266. 3.2 agent_core PostgreSQL (primary)
267. Field	Value
268. Binary	`F:\AgentCore\postgres_runtime_engine\pgsql\bin\postgres.exe`
269. Config	`F:\AgentCore\database_cluster\postgresql.conf`
270. Port	55432
271. listen_addresses	localhost
272. max_connections	100
273. Database	`agent_core`
274. Roles	`agent_read` (RO), `agent_ingest` (RW), `agent_admin`
275. Env vars	`AGENT_CORE_PGHOST`, `AGENT_CORE_PGPORT`, `AGENT_CORE_PGDATABASE`, `AGENT_CORE_PGUSER`, `AGENT_CORE_AGENT_INGEST_PASSWORD` [REDACTED], `AGENT_CORE_AGENT_READ_PASSWORD` [REDACTED]
276. Scheduler	`\AgentCore\PostgresRuntime` scheduled task
277. Connection template	`postgresql://agent_read:[REDACTED]@127.0.0.1:55432/agent_core?sslmode=disable`
278. 3.3 Docker Stack Databases
279. DB	Container	Port	Volume	Data on
280. n8n Postgres 18	`local-agent-stack-postgres-1`	127.0.0.1:5432	`local-agent-stack_postgres_data`	C: VHDX
281. Qdrant	`agentops-qdrant`	0.0.0.0:6333-6334	`agentops_qdrant_storage`	C: VHDX
282. Portainer	`portainer`	0.0.0.0:9443, 8005	`portainer_data`	C: VHDX
283. n8n	`local-agent-stack-n8n-1`	127.0.0.1:5678	`local-agent-stack_n8n_data`	C: VHDX
284. Stopped containers (legacy): devcontainer-mariadb-1, devcontainer-redis-* (×3), devcontainer-frappe-1
285. 3.4 Native Vector Storage (F:)
286. Engine	Path	Status
287. Qdrant	`F:\VectorDB\qdrant\`	Directory exists
288. Chroma	`F:\VectorDB\chroma\`	Directory exists
289. LanceDB	`F:\VectorDB\lancedb\`	Directory exists
290. pgvector	`F:\VectorDB\pgvector\`	Directory exists
291. 3.5 Docker Compose Files
292. Stack	Compose file	Services
293. local-agent-stack	`D:\Autonomy\local-agent-stack\docker-compose.yml`	postgres, n8n, pgadmin (profile)
294. infra (AgentOps)	`D:\AgentOps\infra\docker-compose.yml`	qdrant, portainer
295. 3.6 Safe Connection Templates
296. ```
297. # Agent memory (primary — use this for AI agent connections)
298. postgresql://agent_read:[REDACTED]@127.0.0.1:55432/agent_core?sslmode=disable
299. postgresql://agent_ingest:[REDACTED]@127.0.0.1:55432/agent_core?sslmode=disable
300. 
301. # n8n automation DB (not for agents — n8n internal only)
302. postgresql://n8n:[REDACTED]@127.0.0.1:5432/n8n?sslmode=disable
303. 
304. # Qdrant vector DB
305. http://127.0.0.1:6333
306. # Header: api-key: [REDACTED] (if QDRANT_API_KEY set)
307. 
308. # Meilisearch (SwarmRecall)
309. http://127.0.0.1:7700
310. # Header: Authorization: Bearer [REDACTED]
311. 
312. # Ollama (when running)
313. http://127.0.0.1:11434/api/generate
314. ```
315. ---
316. PART 4 — MCP AND AGENT INTEGRATION MAP
317. 4.1 Config Files
318. Owner	Config path	Exists	Servers
319. Cursor (live)	`C:\Users\ynotf\.cursor\mcp.json`	✅	arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking, serena
320. OpenClaw / ClawX	`C:\Users\ynotf\.openclaw\openclaw.json`	✅	Same + eye2byte
321. 
322. MiniMax Code	`C:\Users\ynotf\.minimax\mcp\mcp.json`	✅	arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking
323. Mavis	`C:\Users\ynotf\.mavis\mcp\mcp.json`	✅	arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking
324. Claude Desktop	`AppData/Roaming/Claude/claude_desktop_config.json`	✅	droidrun, obsidian-mcp-tools — CONTAINS EMBEDDED SECRET
325. MCP control plane	`D:\MCP-Control-Plane\renderers\cursor-global.mcp.json`	✅	Renderer only — not live runtime
326. 4.2 MCP Server Registry
327. Server	Transport	Command / URL	FS write?	DB write?	Risk
328. arabold-docs	stdio	node → `arabold-docs-mcp/dist/index.js`	No	No	Low
329. artiforge	http	`https://tools.artiforge.ai/mcp?pat=[REDACTED]`	No	No	Low
330. context-fabric	stdio	node → `context-fabric/dist/index.js`	Minimal	No	Low
331. cursor-agent-mcp	stdio	`npx cursor-agent-mcp@latest`	Indirect	No	Medium
332. filesystem	stdio	`npx @modelcontextprotocol/server-filesystem`	YES — allowed roots	No	HIGH
333. global-memory-gateway	stdio	`D:\Codex_Managed\.venv\...\python.exe -m autonomy_factory.global_memory_gateway`	No	YES (agent_core :55432)	HIGH
334. github-mcp	stdio/Docker	`docker run ghcr.io/github/github-mcp-server`	No	No	Medium
335. mcp-debugger	stdio	`npx @debugmcp/mcp-debugger@latest`	No	No	Low
336. obsidian-vault	stdio → PS1	`C:\Users\ynotf\.openclaw\start-obsidian-mcp-server.ps1`	YES (via REST)	No	CRITICAL
337. playwright	stdio	`npx @playwright/mcp@latest`	Screenshots	No	Low–Medium
338. sequential-thinking	stdio	`npx @modelcontextprotocol/server-sequential-thinking`	No	No	Low
339. serena	stdio	`C:\Users\ynotf\AppData\Roaming\uv\tools\serena-agent\Scripts\serena.exe start-mcp-server --transport stdio --context <client-context>`	YES (code edits)	No	HIGH
340. eye2byte	stdio	OpenClaw-only	Unknown	Unknown	Medium
341. Filesystem MCP allowed roots:
342. ```
343. C:\Users\ynotf, D:\Codex_Managed, D:\cursor_setup, D:\openclaw, D:\Obsidian, F:\AgentCore, E:\AgentCoreArchive
344. ```
345. global-memory-gateway env vars:
346. ```
347. AGENT_CORE_PGHOST=127.0.0.1
348. AGENT_CORE_PGPORT=55432
349. AGENT_CORE_PGDATABASE=agent_core
350. AGENT_CORE_PGUSER=agent_ingest
351. AGENT_CORE_PGPASSWORD=[REDACTED]
352. OPENAI_API_KEY=[REDACTED]
353. MEM0_DEFAULT_USER_ID=master_developer_profile
354. ```
355. 4.3 New MCP Server Onboarding (mandatory procedure)
356. Read this file first — understand the existing server inventory.
357. Verify config: `Test-Path 'C:\Users\ynotf\.cursor\mcp.json'`
358. Verify command binary exists: `Test-Path <full path to executable>`
359. Verify env var names (not values): confirm vars are set in OS environment.
360. Verify port if TCP: `netstat -ano | findstr :<port>`
361. Start read-only first — use `agent_read` role, GET-only API calls.
362. Test tool discovery via IDE MCP panel before enabling writes.
363. Avoid writes until project explicitly approved for that session.
364. Log all actions to `D:\ChaosCentral-Current-Build\_evidence\`.
365. Never add `cursor-agent-mcp`, `global-memory-gateway`, or `obsidian-vault` writes without single-operator rule.
366. ---
367. PART 5 — NETWORK AND PORT MAP
368. 5.1 Complete Port Inventory (2026-06-27)
369. Port	Process	Bind	LAN?	Service
370. 55432	postgres.exe	127.0.0.1	No	Agent Core PostgreSQL
371. 5432	com.docker.backend	127.0.0.1	No	Docker → n8n Postgres
372. 5678	com.docker.backend	127.0.0.1	No	n8n UI
373. 6333	com.docker.backend	0.0.0.0	YES ⚠	Qdrant HTTP
374. 6334	com.docker.backend	0.0.0.0	YES ⚠	Qdrant gRPC
375. 7700	meilisearch.exe	127.0.0.1	No	SwarmRecall Meilisearch
376. 3300	node.exe	127.0.0.1	No	SwarmRecall API
377. 11434	ollama.exe	127.0.0.1	No	Ollama (when running)
378. 18789	ClawX.exe	127.0.0.1	No	OpenClaw gateway
379. 27124	Obsidian.exe	127.0.0.1	No	Obsidian REST (HTTPS)
380. 27123	Obsidian.exe	127.0.0.1	No	Obsidian REST (HTTP)
381. 8384	syncthing.exe	127.0.0.1	No	Syncthing UI
382. 45653	Standard Notes	127.0.0.1	No	Standard Notes local
383. 5177 / 19988	Interpreter.exe	127.0.0.1	No	Open Interpreter
384. 3389	svchost	0.0.0.0	YES ⚠	RDP
385. 8005	com.docker.backend	0.0.0.0	YES ⚠	Portainer HTTP
386. 9443	com.docker.backend	0.0.0.0	YES ⚠	Portainer HTTPS
387. 17500–17501	Dropbox.exe	0.0.0.0	Yes	Dropbox LAN sync
388. 22000	syncthing.exe	0.0.0.0	Yes	Syncthing data port
389. 443 (Tailscale)	tailscaled.exe	100.111.111.124	Tailscale	Tailscale VPN
390. 5.2 LAN Exposure Risk Matrix
391. Port	Service	Risk	Action needed
392. 6333–6334	Qdrant	CRITICAL	Bind to 127.0.0.1 in docker-compose.yml
393. 3389	RDP	HIGH	Restrict source IPs in Windows Firewall
394. 9443	Portainer HTTPS	HIGH	Strong password + firewall restriction
395. 8005	Portainer HTTP	HIGH	Bind to 127.0.0.1 or disable
396. 22000	Syncthing	Medium	Expected for LAN sync
397. 17500–17501	Dropbox	Medium	Expected for LAN sync
398. ---
399. PART 6 — AUTOMATION AND SERVICES
400. 6.1 Windows Services (running)
401. Service	Start type	Purpose
402. Tailscale	Automatic	VPN mesh
403. WSLService	Automatic	WSL 2
404. vmcompute	Manual	Docker / Hyper-V isolation
405. TermService	Manual	RDP
406. 6.2 Scheduled Tasks (2026-06-27 state)
407. Task	Path	State	Last result	Schedule
408. PostgresRuntime	`\AgentCore\`	Ready	3221225786 ⚠ FAILED	On demand / at boot
409. SwarmRecallApi	`\AgentCore\`	Ready	3221225786 ⚠	—
410. SwarmRecallMeilisearch	`\AgentCore\`	Ready	3221225786 ⚠	—
411. NightlyBackup	`\AgentCore\`	Ready	0 (success)	~3:00 AM
412. NightlyRestoreTest	`\AgentCore\`	Ready	0 (success)	~3:30 AM
413. DailyDriftCheck	`\AgentCore\`	Ready	0 (success)	~4:00 AM
414. WeeklyMaintenance	`\AgentCore\`	Ready	267011 (check)	Weekly
415. CodexDisasterRecovery6h	`\Codex\`	Ready	0 (success)	Every 6h
416. CodexHomeBackupEvery6Hours	`\Codex\`	Ready	0 (success)	Every 6h
417. CodexAgentStackBackup6h	`\`	Running	—	Every 6h
418. OpenClaw Gateway	`\`	Ready	0 (success)	—
419. LocalAgentStack-OllamaServe	`\`	Ready	0 (success)	—
420. Syncthing	`\`	Ready	0 (success)	—
421. > **⚠ PostgresRuntime / SwarmRecallApi / SwarmRecallMeilisearch** last result = 3221225786 (0xC000_0042 = STATUS_OBJECT_NAME_NOT_FOUND). The scheduled task binary path may be stale or the service is being launched differently now. Postgres IS listening on :55432 (confirmed by netstat), so it's starting through some other mechanism. Investigate task action arguments.
422. 6.3 Background Processes (running at scan time)
423. Process	PID (approx)	Ports	Purpose
424. postgres.exe (×7)	—	55432	Agent core Postgres
425. meilisearch.exe	—	7700	SwarmRecall
426. ollama.exe	—	(not listening)	Ollama (idle)
427. ClawX.exe (×5)	—	18789	OpenClaw gateway
428. Interpreter.exe	—	5177, 19988	Open Interpreter
429. syncthing.exe	—	8384, 22000	File sync
430. Dropbox.exe	—	17500–17501	Cloud sync
431. com.docker.backend	—	many	Docker Desktop
432. tailscaled.exe	—	443	Tailscale
433. Obsidian.exe	—	27123, 27124	Vault + REST API
434. 6.4 Local API Endpoints
435. URL	Auth	Purpose
436. `http://127.0.0.1:5678`	username/password	n8n workflow UI
437. `http://127.0.0.1:7700`	Master key header	Meilisearch
438. `http://127.0.0.1:11434`	None (localhost)	Ollama API
439. `http://127.0.0.1:8384`	GUI password	Syncthing UI
440. `http://127.0.0.1:18789`	Gateway token [REDACTED]	OpenClaw gateway
441. `https://127.0.0.1:27124`	Bearer [REDACTED]	Obsidian REST
442. `https://localhost:9443`	Admin password	Portainer
443. `http://127.0.0.1:6333`	API key [REDACTED] optional	Qdrant
444. `http://127.0.0.1:3300`	API key [REDACTED]	SwarmRecall API
445. ---
446. PART 7 — KNOWLEDGE VAULTS
447. 7.1 Obsidian Vaults
448. Vault	Path	Active	Files	Size
449. Dungeon Vault	`D:\Obsidian\Dungeon Vault\`	YES — auto-opens	207	~141 MB
450. Obsidian Vault	`D:\Obsidian\Obsidian Vault\`	No	71	~9.3 MB
451. Projects-Global	`D:\Projects-Global\`	No	32	~4.9 MB
452. Obsidian running: Yes | REST :27123: Yes | REST :27124: Yes | Dropbox dup: No (was present, now gone)
453. MCP access to vaults:
454. Cursor/OpenClaw: `obsidian-vault` MCP → PowerShell → HTTPS :27124 → `OBSIDIAN_API_KEY` [REDACTED]
455. Claude Desktop: `obsidian-mcp-tools` → plugin binary → EMBEDDED KEY IN CONFIG — ROTATE IMMEDIATELY
456. 7.2 Agent Memory Paths
457. Path	Role	Agent access
458. `D:\Codex_Managed\`	Codex Python workspace	Read/write with care
459. `D:\memory-bank\`	Placeholder (empty)	Free to use
460. `D:\CursorMemory\`	Cursor memory (~19 KB)	Read/write
461. `E:\CodexMemory\`	Codex memory exports root — DOES NOT EXIST	Create if needed
462. `E:\CodexMemory\markdown-vault\`	(env `CODEX_MEMORY_MARKDOWN_VAULT`) — absent	Create if needed
463. 7.3 Write Policy
464. Active vault (Dungeon Vault): Use `obsidian-vault` MCP REST only. Never direct filesystem write while Obsidian is open.
465. Syncthing: Pause before bulk programmatic writes; resume after.
466. Dropbox vault copy: Not currently detected — read-only if it returns.
467. One writer per vault — Cursor, ClawX, MiniMax, Claude all have separate MCP paths; coordinate before concurrent vault operations.
468. ---
469. PART 8 — ENVIRONMENT VARIABLES (names only — values redacted)
470. Database
471. Variable	Value/Role
472. `AGENT_CORE_PGHOST`	127.0.0.1
473. `AGENT_CORE_PGPORT`	55432
474. `AGENT_CORE_PGDATABASE`	agent_core
475. `AGENT_CORE_PGUSER`	agent_ingest
476. `AGENT_CORE_AGENT_INGEST_PASSWORD`	[REDACTED]
477. `AGENT_CORE_AGENT_ADMIN_PASSWORD`	[REDACTED]
478. `AGENT_CORE_AGENT_READ_PASSWORD`	[REDACTED]
479. `AGENT_CORE_POSTGRES_PASSWORD`	[REDACTED]
480. `AGENT_CORE_SWARMRECALL_API_KEY`	[REDACTED]
481. `AGENT_CORE_SWARMRECALL_MEILI_MASTER_KEY`	[REDACTED]
482. `N8N_ENCRYPTION_KEY`	[REDACTED]
483. `QDRANT_API_KEY`	[REDACTED]
484. AI / LLM
485. Variable	Used by
486. `OPENAI_API_KEY`	arabold-docs, global-memory-gateway, embeddings
487. `CURSOR_API_KEY`	cursor-agent-mcp
488. `ARTIFORGE_PAT`	artiforge MCP
489. `MEM0_API_KEY`	mem0 / OpenMemory
490. `OPENMEMORY_API_KEY`	OpenMemory
491. `OLLAMA_HOST`	127.0.0.1:11434
492. `OLLAMA_DEFAULT_MODEL`	qwen3-coder:30b
493. `OPENCLAW_GATEWAY_TOKEN`	ClawX gateway
494. `OPENCLAW_CODEX_API_KEY`	OpenClaw Codex
495. Obsidian
496. Variable	Value
497. `OBSIDIAN_API_KEY`	[REDACTED]
498. `OBSIDIAN_LOCAL_REST_API`	[REDACTED]
499. `OBSIDIAN_BASE_URL`	https://127.0.0.1:27124
500. `OBSIDIAN_PORT`	27124
501. Codex paths
502. Variable	Value
503. `CODEX_HOME`	`C:\Users\ynotf\.codex`
504. `CODEX_MEMORY_ROOT`	`E:\CodexMemory` (path ABSENT — create)
505. `CODEX_MEMORY_MARKDOWN_VAULT`	`E:\CodexMemory\markdown-vault` (absent)
506. `CODEX_ALLOWED_ROOTS`	`C:\Users\ynotf;E:\CodexMemory;C:\Users\ynotf\CodexAutonomyStack`
507. `CODEX_PROTECTED_ROOTS`	`C:\Windows;C:\Program Files;...`
508. `CODEX_SKILLS_HOME`	`C:\Users\ynotf\.agents\skills\`
509. VCS / containers
510. Variable	Used by
511. `GITHUB_PERSONAL_ACCESS_TOKEN`	github-mcp, gh CLI
512. `GITHUB_TOKEN`	GitHub Actions
513. `DOCKERHUB_USERNAME`	ynotfins
514. `ANDROID_HOME`	`C:\Users\ynotf\AppData\Local\Android\Sdk`
515. `JAVA_HOME`	`...\jdk-17.0.16.8-hotspot`
516. ---
517. PART 9 — SECURITY BASELINE
518. Critical items requiring immediate action
519. #	Item	Severity
520. 1	Plaintext Obsidian API key in Claude Desktop config	CRITICAL — rotate now
521. 2	Qdrant :6333/:6334 on 0.0.0.0	CRITICAL — restrict to 127.0.0.1
522. 3	RDP :3389 on 0.0.0.0	HIGH — add firewall IP restriction
523. 4	Portainer :9443/:8005 on 0.0.0.0	HIGH — strong password + restrict
524. 5	`D:\Autonomy\secrets-backups\` not in any sync tool	HIGH — audit
525. Agent least-privilege rules
526. Connect as `agent_read` first; escalate to `agent_ingest` only with task justification.
527. Load all credentials from OS environment — never from this file or any docs.
528. Never write to `C:\Users\ynotf\.cursor\mcp.json` without human approval.
529. Never modify scheduled tasks without human approval.
530. Never run `docker stop/rm` on production containers without human approval.
531. Use `CODEX_PROTECTED_ROOTS` to prevent writes to `C:\Windows`, `C:\Program Files`, etc.
532. Log every write action to `D:\ChaosCentral-Current-Build\_evidence\`.
533. Config files that may contain secrets
534. File	Risk
535. `AppData/Roaming/Claude/claude_desktop_config.json`	CRITICAL — plaintext key
536. `~/.openclaw/openclaw.json`	Gateway token — verify is `${env:...}` reference
537. `D:\Autonomy\` docker `.env` files	May contain passwords — never commit
538. ---
539. PART 10 — BACKUP AND DISASTER RECOVERY
540. Backup coverage summary
541. Asset	Coverage	Gap
542. Agent Postgres (`F:\AgentCore\database_cluster\`)	`\AgentCore\NightlyBackup` → `F:\AgentCore\backups\`	✅ Covered
543. Obsidian Dungeon Vault	Syncthing + Dropbox sync	⚠ Sync ≠ backup
544. Codex home (`~/.codex/`)	`CodexHomeBackupEvery6Hours`	✅
545. Codex managed workspace	`CodexAgentStackBackup6h`	✅
546. n8n workflows (Docker volume)	NOT CONFIRMED	HIGH GAP
547. Qdrant vectors (Docker volume)	NOT CONFIRMED	HIGH GAP
548. `~/.cursor/mcp.json`	NOT CONFIRMED	HIGH GAP
549. `~/.openclaw/openclaw.json`	NOT CONFIRMED	HIGH GAP
550. `F:\VectorDB\` native dirs	NOT CONFIRMED	HIGH GAP
551. Windows env / Credential Manager	`secrets-backups/` dir exists; coverage unknown	CRITICAL GAP
552. GitHub repos	Git remote push (if pushed)	⚠ If not pushed, lost
553. Restore order (catastrophic failure)
554. F: Agent Postgres — `F:\AgentCore\backups\` restore
555. Windows env secrets — `D:\Autonomy\secrets-backups\`
556. MCP configs — `~/.cursor/mcp.json`, `~/.openclaw/`
557. Codex home — from 6h backup
558. Codex managed workspace / venv
559. Obsidian vaults — Syncthing peer or Dropbox
560. Docker volumes — rebuild or restore
561. GitHub repos — re-clone
562. D:\Autonomy — restore from archive
563. ---
564. PART 11 — CAPACITY AND PERFORMANCE
565. Drive	Total	Free	Used%	Growth hotspot
566. C:	1.91 TB	629 GB	67%	Docker VHDX (~14 GB growing), Cursor globalStorage (~13 GB)
567. D:	1.91 TB	893 GB	53%	D:\Autonomy (~98 GB), HF_Cache, models
568. E:	5.59 TB	5.59 TB	<1%	Underused — ideal for model cache, cold archive
569. F:	3.64 TB	3.72 TB	<1%	Ideal for DB growth
570. G:	3.64 TB	2.17 TB	42%	Backup accumulation
571. Warning thresholds: C: → 80% (~1.53 TB used, ~250 GB away); D: → 80% (~1.53 TB used, ~520 GB away)
572. RAM: 128 GB — fully populated, no expansion possible  
573. GPU VRAM: 12 GB GDDR6X — Ollama `qwen3-coder:30b` may require quantization at high load  
574. CPU: i9-14900KF — not a bottleneck for current stack  
575. I/O bottleneck: Docker VHDX on C: (OS NVMe) competes with system I/O — migrate to D:/F: bind mounts
576. ---
577. PART 12 — EXPANSION DECISION GUIDE
578. Hardware expansion status (post physical inspection)
579. M.2 NVMe: NO FREE SLOTS. All 3 (M.2_1, M.2_2, M.2_3) are occupied. Cannot add NVMe without removing a drive.
580. PSU: Corsair RM1000 1000W — ~600 W headroom — adequate for PCIe expansion card if slot exists.
581. Options if more storage is needed:
582. Option	Feasibility	Best for
583. Replace C: T-FORCE (1.91 TB) → larger NVMe	Viable (OS migration)	If OS drive space is the constraint
584. Replace D: T-FORCE (1.91 TB) → larger NVMe	Viable (data migration)	If dev workspace is the constraint
585. PCIe NVMe expansion card	Possible — free PCIe slot NOT CONFIRMED	Docker/WSL dedicated tier
586. USB NVMe enclosure	Not for DBs	Archive/backup only
587. Before purchase checklist:
588. [ ] Open case — confirm PCIe slot availability
589. [ ] Download ASUS Z790 GAMING WIFI7 manual — check lane sharing
590. [ ] Confirm riser cable PCIe generation
591. [ ] Confirm BIOS compatibility with target NVMe model
592. Software-only capacity improvements (no hardware needed)
593. Action	Expected gain
594. Move Docker data root to D: or F: bind mounts	-14 GB+ from C: VHDX, stops growth
595. Move `D:\HF_Cache\` → `E:\HF_Cache\`	Frees D:
596. Move `D:\models\` → `E:\models\`	Frees D:
597. Archive `D:\Autonomy\Backups\` → G:/E:	Frees up to tens of GB from D:
598. Move n8n Postgres + Qdrant volumes to F: bind mounts	Better I/O + enables direct backup
599. ---
600. PART 13 — AUTONOMOUS WORKFLOW DESIGN GUIDE
601. System architecture flow
602. ```
603. New AI Agent
604.     │
605.     ▼
606. IDE / Agent Runtime
607. (Cursor :1.126 / Codex :26.623 / ClawX :0.4 / MiniMax / Mavis)
608.     │
609.     ▼
610. ~/.cursor/mcp.json  (or per-IDE equivalent)
611.     │
612.     ├── stdio MCP servers (serena, filesystem, playwright, sequential-thinking, arabold-docs)
613.     │
614.     ├── global-memory-gateway (stdio → Python venv D:\Codex_Managed\.venv)
615.     │         │
616.     │         ▼
617.     │   PostgreSQL :55432 agent_core  (F: Samsung 990 PRO Gen4)
618.     │
619.     ├── obsidian-vault (stdio → PS1 → HTTPS :27124)
620.     │         │
621.     │         ▼
622.     │   D:\Obsidian\Dungeon Vault\   (D: T-FORCE NVMe)
623.     │
624.     ├── github-mcp (stdio → ephemeral Docker container)
625.     │
626.     └── OpenClaw gateway :18789
627.               │
628.               ▼
629.          ClawX.exe → eye2byte + all Cursor MCPs
630.               │
631.               ▼
632.     Qdrant :6333 (Docker) → agentops_qdrant_storage (C: VHDX — migrate to F:)
633. ```
634. Multi-agent coordination rules
635. Rule	Reason
636. Single writer to agent_core Postgres	global-memory-gateway spawns one writer; Cursor + OpenClaw + Mavis can all trigger it — coordinate or use sequential sessions
637. Single writer to Obsidian vault	obsidian-vault MCP via REST; do not use filesystem MCP on vault while Obsidian is open
638. Do not confuse :55432 vs :5432	55432 = agent memory (F:, native); 5432 = n8n automation DB (C:, Docker)
639. Pause Syncthing before bulk vault writes	File conflict artifacts
640. Load all secrets from env, never from docs	All [REDACTED] values must be read at runtime from Windows environment
641. Use agent_read for discovery, agent_ingest for writes	Postgres least privilege
642. Log all write actions to `D:\ChaosCentral-Current-Build\_evidence\`	Audit trail
643. Agent onboarding checklist (Step 1 of every new session)
644. Step 1 — Read source of truth:
645. [ ] Read `MCP_AND_AI_AGENT_INTEGRATION.md` (Part 4 of this doc)
646. [ ] Read `DATABASE_AND_VECTOR_STORAGE.md` (Part 3)
647. [ ] Read `NETWORK_AND_PORTS.md` (Part 5)
648. [ ] Read `DRIVE_ROLE_MAP.md` (Part 1.4)
649. Step 2 — Verify live runtime:
650. [ ] Confirm `~/.cursor/mcp.json` exists
651. [ ] Confirm `:55432` listening: `netstat -ano | findstr 55432`
652. [ ] Confirm `:27124` listening (if vault access needed)
653. [ ] Confirm `D:\Codex_Managed\.venv\Scripts\python.exe` exists
654. [ ] Confirm no backup task running (NightlyBackup ~3:00 AM)
655. Step 3 — Connect with least privilege:
656. [ ] DB: use `agent_read` role first
657. [ ] Vault: use obsidian-vault MCP REST only
658. [ ] Filesystem: scope to narrowest allowed root
659. [ ] Escalate to `agent_ingest` only when explicit write task begins
660. [ ] Abort on port, path, or schema mismatch
661. Known friction points for autonomous workflow
662. PostgresRuntime task last result = 3221225786 — scheduled task binary path stale; Postgres IS running but task state inconsistent. Investigate task action before relying on task-based restart.
663. Docker DBs on C: VHDX — I/O contention + no direct backup path + growth pressure on OS drive.
664. Qdrant LAN-exposed — fix before exposing any agent that calls Qdrant to external network.
665. Plaintext Obsidian key in Claude Desktop — any agent using Claude Desktop can write to vault without MCP guardrails.
666. `E:\CodexMemory\` path absent — env var set but directory does not exist; create before any Codex memory operation.
667. Multiple IDEs (Cursor + ClawX + MiniMax + Mavis) all pointing to same Postgres agent_core — ensure only one memory-writing session active at a time.
668. No vault write-lock protocol — implement coordination mechanism before running parallel vault-writing agents.
669. git status — 12/13 repos dirty — many uncommitted changes in D:\github repos; may affect agent code operations.
670. ---
671. PART 14 — STILL REQUIRES ADMIN OR PHYSICAL INSPECTION
672. Item	How to resolve
673. Drive health (SMART)	`Get-PhysicalDisk` as admin
674. BitLocker encryption status	`Get-BitLockerVolume` as admin
675. Exact disk-to-letter mapping	`Get-Partition -DriveLetter` as admin
676. Full firewall rule export	`Get-NetFirewallRule` as admin
677. M.2 slot-to-drive mapping (which is C:, D:, F:)	Physical inspection + label silkscreen
678. CPU cooler brand/model	Physical inspection
679. GPU PCIe slot label	Physical inspection
680. GPU power connector type	Physical inspection
681. PCIe riser cable generation	Physical inspection
682. Empty PCIe slots	Physical inspection
683. SATA ports/cables	Physical inspection
684. `\AgentCore\PostgresRuntime` task failure root cause	`Get-ScheduledTask
685. NightlyBackup coverage (what exactly it backs up)	Inspect task script
686. Meilisearch data directory	Inspect SwarmRecallMeilisearch task action
687. ---
688. PART 15 — RECOMMENDED ACTIONS (ranked by impact)
689. #	Action	Impact
690. 1	Rotate Claude Desktop Obsidian API key; replace with `${env:OBSIDIAN_LOCAL_REST_API}` env ref	CRITICAL
691. 2	Restrict Qdrant to 127.0.0.1 in `D:\AgentOps\infra\docker-compose.yml`	CRITICAL
692. 3	Add Windows Firewall rule restricting RDP :3389 to trusted IPs	HIGH
693. 4	Migrate Docker volumes to F:\ bind mounts (removes C: VHDX pressure + enables backup)	HIGH
694. 5	Move `D:\HF_Cache\` + `D:\models\` → `E:\`	HIGH
695. 6	Add Docker volume backup (n8n Postgres + Qdrant) to NightlyBackup	HIGH
696. 7	Create `E:\CodexMemory\` directory tree to match env vars	HIGH
697. 8	Single canonical Obsidian write path; retire Claude obsidian-mcp-tools	HIGH
698. 9	Investigate and fix `\AgentCore\PostgresRuntime` task result 3221225786	MEDIUM
699. 10	Discover Meilisearch data dir; add to backup	MEDIUM
700. 11	Record M.2 slot-to-drive mapping on next case opening	MEDIUM
701. 12	Check BIOS 1805 against latest ASUS update	LOW
702. ---
703. APPENDIX — EVIDENCE PROVENANCE
704. Source	Date	Type
705. PowerShell CIM discovery (Win32_BaseBoard, Win32_BIOS, Win32_Processor, Win32_PhysicalMemory, Win32_VideoController, Win32_DiskDrive, Win32_LogicalDisk, Win32_PnPEntity)	2026-06-26	Automated
706. `netstat -ano`, `tasklist`, `docker ps`, `docker volume ls/inspect`, `docker compose ls`, `wsl --list`, `winget list`, `Get-ScheduledTask`, `Get-Service`	2026-06-27	Automated (scripts/Collect-SystemEcosystemInventory.ps1)
707. MCP config files read: `mcp.json`, `openclaw.json`, `minimax/mcp.json`, `mavis/mcp.json`, `claude_desktop_config.json`, docker-compose YAML, `postgresql.conf`	2026-06-27	File inspection
708. nvidia-smi telemetry	2026-06-27	Live
709. Physical case inspection	2026-06-27	Human observation
710. Evidence JSON	`D:\ChaosCentral-Current-Build\_evidence\system-ecosystem-20260627-194037.json`	229 KB
711. All credential values in this document are `[REDACTED]`. No secrets were stored during generation.
712. 
713. ---
714. PART 16 — OPTIMIZED 23-AGENT WORKFLOW FOR THIS PC
715. 16.1 Why not run all 23 as independent runtime agents
716. The 23-agent plan is strong as a mental model, but weak as a literal execution graph. The main failure modes are predictable:
717. Failure mode	What happens	PC-specific effect
718. Context bloat	Every agent appends logs, code, critiques, and state	Huge prompts, slow loops, lower quality
719. Critic contradiction	Code critic, architecture critic, performance critic, and judge disagree	Rework loops burn API budget and never merge
720. Same-working-tree branch collision	Main builder and A/B builder both call `git checkout` in same repo	Branch corruption, lost diffs, broken commits
721. Memory write race	Many agents write persistent memory directly	Duplicate, stale, or contradictory AgentCore facts
722. Obsidian write race	Docs agent, Claude plugin, filesystem MCP, and Obsidian REST can all touch vault	Sync conflicts or note corruption
723. Over-privileged tool access	Filesystem MCP and Open Interpreter can reach broad paths	Accidental secrets/config/database damage
724. Latency explosion	23 model calls plus tests and retries	Simple PRs become long and expensive
725. Therefore: keep the 23 roles, but execute them as six hubs.
726. 16.2 Recommended six-hub runtime mapping
727. Runtime hub	Absorbed 23-agent roles	Allowed tools	Writes?
728. 1. Intake + Policy Hub	Orchestrator Lead, Specification & Scope, Token Budget Guard, Human Proxy	issue reader, repo metadata, cost ledger	run manifest only
729. 2. Context / Architecture / RAG Hub	Context Weaver, Modular Architect, Macro Best Practices, Refactor Catalyst, Friction & Unused Code	filesystem read, git read, SwarmRecall read, SwarmVault read, Meilisearch read	context bundle only
730. 3. Main Builder Hub	Lead Implementer, Real-Time Debugger, Refactor Executor	git worktree, filesystem write in worktree, test command runner	isolated worktree only
731. 4. A/B Builder Hub	A/B Branch Creator, Parallel Stream Specialist, Real-Time Debugger	separate git worktree, filesystem write in worktree, test command runner	isolated worktree only
732. 5. Verification + Critic Hub	QA & Unit Test, Integration Tester, Performance & Drift Checker, Primary/Secondary/Tertiary Critics, A/B Evaluator	test/lint/type/security scanners, coverage, benchmark runner	reports only
733. 6. Governance / PR / Memory-Broker Hub	Scorer, Judge, Git Stream Specialist, Documentation Engineer, Human Proxy	GitHub CLI/API, docs writer lock, memory broker, PR creator	PR, docs, approved memory event
734. The Omniagent Interface Agent should become a tool gateway library, not a reasoning agent. It should enforce path guards, port policy, token budget, credential lookup, command allowlists, retry/timeout behavior, and trace logging.
735. 16.3 Canonical autonomous run flow
736. ```text
737. 1. Create run_id.
738. 2. Create D:\AgentSwarm\runs\<run_id>\.
739. 3. Create run manifest and budget ledger.
740. 4. Refuse unsafe target repos unless baseline state is known.
741. 5. Create two isolated worktrees:
742.       D:\AgentSwarm\runs\<run_id>\main
743.       D:\AgentSwarm\runs\<run_id>\ab
744. 6. Context Hub reads repo docs, AGENTS.md, architecture files, SwarmRecall, SwarmVault.
745. 7. Context Hub emits compact task packet: scope, allowed files, tests, risks, acceptance criteria.
746. 8. Main Builder creates conventional patch in main worktree.
747. 9. A/B Builder creates alternative patch in ab worktree.
748. 10. Verification Hub runs deterministic checks on both worktrees.
749. 11. Critic Hub reads evidence, not whole transcripts.
750. 12. Scorer computes deterministic score.
751. 13. Judge selects main, A/B, or reject/rework.
752. 14. Governance Hub creates PR only; no direct merge.
753. 15. Documentation Engineer updates docs through a docs lock.
754. 16. Memory Write Broker writes one durable memory summary only after approval.
755. 17. Run artifacts are archived; raw temporary worktrees may be retained for replay or cleaned after retention period.
756. ```
757. 16.4 Required run folder layout
758. ```text
759. D:\AgentSwarm\
760.   runs\
761.     <run_id>\
762.       run_manifest.json
763.       budget_ledger.jsonl
764.       locks\
765.       main\                 # git worktree for conventional implementation
766.       ab\                   # git worktree for alternative implementation
767.       evidence\
768.         context_bundle.json
769.         repo_map.txt
770.         test_main.json
771.         test_ab.json
772.         lint_main.json
773.         lint_ab.json
774.         security_main.sarif
775.         security_ab.sarif
776.         perf_main.json
777.         perf_ab.json
778.         critic_report.json
779.         scorecard.json
780.         judge_decision.json
781.       patches\
782.         main.patch
783.         ab.patch
784.       logs\
785.         orchestrator.jsonl
786.         tools.jsonl
787.         subprocess.jsonl
788.         model_usage.jsonl
789.       docs\
790.         pr_body.md
791.         rollback_plan.md
792.         memory_event_proposal.md
793.   artifacts\
794.   locks\
795.   cache\
796. ```
797. Recommended root creation command:
798. ```powershell
799. New-Item -ItemType Directory -Force `
800.   D:\AgentSwarm\runs, `
801.   D:\AgentSwarm\artifacts, `
802.   D:\AgentSwarm\logs, `
803.   D:\AgentSwarm\locks, `
804.   D:\AgentSwarm\cache
805. ```
806. 16.5 Required git worktree model
807. Never let both builders write to one repo working directory. Use worktrees:
808. ```powershell
809. $Repo = 'D:\github\your-repo'
810. $Run  = '20260628-001-feature-name'
811. $Root = "D:\AgentSwarm\runs\$Run"
812. 
813. New-Item -ItemType Directory -Force $Root
814. 
815. git -C $Repo fetch origin main
816. git -C $Repo worktree add "$Root\main" -b "ai/$Run/main" origin/main
817. git -C $Repo worktree add "$Root\ab"   -b "ai/$Run/ab"   origin/main
818. ```
819. All agent commands must use explicit working directory:
820. ```powershell
821. git -C "$Root\main" status --short
822. git -C "$Root\ab" status --short
823. ```
824. The PR branch should be created from the selected worktree only after verification. Do not auto-delete other worktrees until evidence is preserved.
825. 16.6 Reference-based graph state
826. Do not store full code, raw logs, and giant transcripts in LangGraph state. Store paths and references:
827. ```python
828. from typing import TypedDict, Literal
829. 
830. class BranchState(TypedDict, total=False):
831.     branch_name: str
832.     worktree_path: str
833.     base_commit: str
834.     head_commit: str
835.     patch_path: str
836.     test_report_path: str
837.     lint_report_path: str
838.     security_report_path: str
839.     perf_report_path: str
840.     score: dict
841. 
842. class TeamState(TypedDict, total=False):
843.     run_id: str
844.     task_id: str
845.     repo_root: str
846.     risk_class: Literal['low', 'medium', 'high', 'critical']
847.     allowed_write_roots: list[str]
848.     protected_roots: list[str]
849.     task_packet_path: str
850.     context_refs: list[dict]
851.     branches: dict[str, BranchState]
852.     selected_branch: str
853.     judge_decision_path: str
854.     pr_url: str
855.     loop_count: int
856.     budget: dict
857.     locks: dict
858.     next_node: str
859. ```
860. 16.7 Deterministic scorecard
861. The Scorer should not ask an LLM to invent a grade. Compute the grade from evidence first, then ask an LLM to explain it.
862. Category	Weight	Data source
863. Correctness	30	unit/integration/e2e tests
864. Security	20	secret scan, CodeQL/SAST, dependency scan, MCP/tool risk
865. Maintainability	20	diff size, complexity, architecture rules, affected modules
866. Performance	15	benchmark delta, memory delta, DB query count, cold-start time
867. Operability	10	logs, rollback plan, migrations, feature flags, docs
868. Cost/latency	5	token spend, runtime, agent loop count
869. Hard fails:
870. ```text
871. Any hardcoded secret                          → fail
872. Any test failure in required suite            → fail
873. Any critical CodeQL/SAST finding              → fail
874. Direct write outside allowed worktree         → fail
875. Direct write to F:\AgentCore raw paths         → fail
876. Direct write to active Obsidian vault by FS   → fail
877. Unapproved DB migration                       → fail
878. Unapproved main merge or production deploy    → fail
879. ```
880. ---
881. PART 17 — SOFTWARE SELECTION MATRIX
882. 17.1 Orchestration layer
883. Candidate	Fit for ChaosCentral	Recommendation
884. LangGraph	Excellent for durable, stateful, branchy workflows with checkpoints, persistence, subgraphs, human review, and state inspection	Primary orchestrator
885. OpenAI Agents SDK	Excellent inside code-first hubs that need typed tools, MCP, guardrails, hosted tools, and SDK-managed run objects	Use inside hubs; do not replace LangGraph unless workflow becomes OpenAI-only
886. n8n	Excellent for schedule/event glue, notifications, webhook handoffs, backup monitors	Use for automation edges, not core code-writing brain	
887. Cursor agent mode	Excellent human-in-the-loop IDE surface	Primary operator UI; not the durable workflow engine
888. GitHub Copilot cloud agent	Good for GitHub-native hosted PR tasks, especially routine issues and independent comparison	External comparator / overflow worker
889. OpenClaw/ClawX	Useful secondary gateway with MCP parity and custom tools	Keep, but restrict write scope and avoid parallel memory writers
890. MiniMax/Mavis	Useful secondary experiments	Read-mostly until policy is proven
891. Open Interpreter	Powerful but high risk because it executes arbitrary code	Quarantine; never connect to production DBs by default
892. AutoGen-style fully free multi-agent swarm	More complexity and weaker fit than LangGraph for your current state/memory needs	Do not make it the main runtime
893. 17.2 Coding-agent layer
894. Tool	Best use	Do not use for
895. Cursor	Interactive architecture, local edits, MCP reads, controlled agent sessions	Unlocked autonomous writes to broad filesystem roots
896. Codex CLI/Desktop	Local coding tasks, repo-level edits, automation handoffs, evidence generation	Direct production deploys or direct raw memory writes
897. GitHub Copilot cloud agent	Hosted branch work, routine bugs, docs, tests, GitHub issue tasks	Local SwarmVault/SwarmRecall access; it should not own local memory
898. Claude Code / frontier code agent if installed later	Complex refactors, codebase reasoning, long debugging loops	Sole judge/security authority without deterministic scans
899. Ollama local model	Cheap summarization, log clustering, first-pass doc drafts	Final architecture, final security review, critical judge decisions
900. 17.3 Memory / RAG / search layer
901. Component	Role	Recommendation
902. AgentCore Postgres `agent_core` :55432	Canonical durable agent memory DB	Keep canonical; connect as `agent_read` first; write only through broker
903. pgvector	Vector search inside canonical Postgres	Preferred for memory facts tied to relational metadata
904. SwarmRecall API :3300	Recall/runtime API	Read-heavy; write through broker or approved gateway
905. SwarmVault	Curated long-term RAG/wiki	Treat as durable knowledge, not scratchpad
906. Meilisearch :7700	Full-text index for SwarmRecall	Keep local; add backup coverage once data dir confirmed
907. Qdrant	High-performance vector DB	Fix loopback + migrate data to F: before expanding use
908. Chroma/LanceDB dirs	Local vector experiments	Use only when a project explicitly needs local embedded vector files
909. Obsidian	Human-readable knowledge vault	Use REST MCP with one writer; not raw file writes
910. 17.4 Security / verification toolchain
911. Minimum recommended gate stack:
912. ```text
913. Unit tests + integration tests + typecheck + lint
914. + secret scanning
915. + dependency scanning
916. + CodeQL/SAST
917. + container/IaC scan where relevant
918. + prompt-injection / MCP-tool red-team tests
919. + deterministic scorecard
920. + PR branch protection
921. ```
922. Recommended tools by role:
923. Need	Recommended tool family	Notes
924. Static security	CodeQL, Semgrep	CodeQL integrates with GitHub code scanning; Semgrep is useful locally/CI
925. Secret scanning	GitHub secret scanning, gitleaks/detect-secrets	Must run before any PR
926. Dependency review	Dependabot, GitHub dependency review, npm/pip audit	Required for agent-added packages
927. Container/IaC	Trivy, Docker Scout, checkov/tflint where applicable	Relevant to Docker/n8n/Qdrant stack
928. AI red-team	Promptfoo	Use for prompt injection, RAG leakage, tool misuse, MCP attack scenarios
929. Observability	LangSmith, OpenTelemetry, Phoenix-style traces	Must record model calls, tool calls, paths, decisions, cost
930. Supply-chain integrity	SLSA provenance, signed artifacts, pinned actions	Important once agents can release packages or build images
931. ---
932. PART 18 — BOTTLENECK AND FRICTION MATRIX
933. 18.1 Ranked bottlenecks
934. Rank	Bottleneck	Current evidence	Workflow impact	Fix
935. 1	Qdrant LAN exposure	`6333/6334` on `0.0.0.0`	Data exfiltration / malicious vector writes	Bind to `127.0.0.1`; add API key
936. 2	Plaintext Obsidian key	Claude Desktop config contains embedded key	Vault write compromise	Rotate key, env var only, retire duplicate MCP
937. 3	Broad filesystem MCP roots	`C:\Users\ynotf`, `D:\Obsidian`, `F:\AgentCore` in scope	Accidental or malicious writes to configs/DB/vault	Split read-only/write profiles
938. 4	Docker DBs on C: VHDX	n8n Postgres + Qdrant in Docker VHDX	OS-drive I/O contention and backup gap	F: bind mounts
939. 5	Multi-agent memory writes	global-memory-gateway writes to `agent_core`	Race conditions and inconsistent facts	Single Memory Write Broker
940. 6	Obsidian sync/write overlap	Obsidian + Syncthing + MCP + possible Claude plugin	Note corruption / sync conflicts	Single writer lock; REST-only
941. 7	Dirty repo set	Many repos not clean in latest scan	Agents may overwrite human work	Baseline diff capture and refusal policy
942. 8	Raw 23-agent graph	too many nodes, critics, loops	Latency/cost/context bloat	Six hubs with compact state
943. 9	Ollama unavailable at scan	`11434` false in latest report	local-model route fails	preflight route check
944. 10	Toolchain gaps	Gradle/Maven/Rust/Go/fd/jq not in PATH	builds may fail or agents improvise	per-project tool bootstrap
945. 11	M.2 expansion blocked	all three M.2 slots occupied	no simple new NVMe	software migration first; PCIe card only after inspection
946. 12	Scheduled task anomaly	AgentCore persistent tasks show `3221225786`	restart automation uncertainty	inspect task actions and fix launchers
947. 18.2 Measurement plan
948. Metric	Command/source	Warning	Critical
949. C: used %	`Get-CimInstance Win32_LogicalDisk`	80%	90%
950. D: used %	same	80%	90%
951. F: used %	same	70%	85%
952. Docker VHDX size	`Get-Item ...docker_data.vhdx`	50 GB	100 GB
953. GPU VRAM used	`nvidia-smi`	10 GB	11.5 GB
954. Postgres connections	`pg_stat_activity`	>70	>90
955. Agent loop count	run manifest	3	5
956. Agent cost/run	model usage ledger	configurable	hard stop
957. Worktree disk per run	`Get-ChildItem D:\AgentSwarm\runs`	10 GB	25 GB
958. Dirty repo count	`git status --short` sweep	>0 for target repo	refuse if untracked secrets/large diffs
959. PR failure rate	GitHub checks	>20%	>50%
960. Memory write queue depth	broker metrics	>50	>200
961. 18.3 Performance tuning targets
962. Component	Target behavior
963. CPU	Use 8–12 test workers initially; avoid saturating 32 threads while IDEs/DBs active
964. RAM	Plenty for local indexing; cap per-process memory for test runners and vector ingestion
965. GPU	One heavy local LLM job at a time; quantized models only for 30B-class workloads
966. D:	Fast code/test tier; avoid filling with model caches/backups
967. F:	Hot DB/vector tier; all access through services/APIs except maintenance windows
968. E:	Cold model/cache/archive; okay for large read-mostly assets
969. G:	Backup only; never live DB
970. ---
971. PART 19 — WRITE SAFETY, LOCKING, AND PATH GUARDS
972. 19.1 Mandatory path policy
973. Agents may write automatically only under:
974. ```text
975. D:\AgentSwarm\runs\
976. D:\AgentSwarm\logs\
977. D:\AgentSwarm\artifacts\
978. D:\github\<repo>\ only through git worktrees or approved repo scope
979. D:\github_2\<repo>\ only through git worktrees or approved repo scope
980. D:\Autonomy\ only with project-specific approval
981. ```
982. Agents must not write automatically to:
983. ```text
984. C:\Windows\
985. C:\Program Files\
986. C:\Users\ynotf\.cursor\mcp.json
987. C:\Users\ynotf\.openclaw\openclaw.json
988. C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json
989. D:\Autonomy\secrets-backups\
990. D:\Obsidian\* by filesystem writes
991. F:\AgentCore\database_cluster\
992. F:\AgentCore\agentmemory\
993. F:\VectorDB\* by raw file writes
994. E:\AgentCoreArchive\ except append-only archive operations
995. G:\ except backup jobs
996. ```
997. 19.2 Python path guard
998. ```python
999. from pathlib import Path
1000. 
1001. ALLOWED_WRITE_ROOTS = [
1002.     Path(r"D:\AgentSwarm\runs").resolve(),
1003.     Path(r"D:\AgentSwarm\logs").resolve(),
1004.     Path(r"D:\AgentSwarm\artifacts").resolve(),
1005.     Path(r"D:\github").resolve(),
1006.     Path(r"D:\github_2").resolve(),
1007. ]
1008. 
1009. PROTECTED_ROOTS = [
1010.     Path(r"C:\Windows").resolve(),
1011.     Path(r"C:\Program Files").resolve(),
1012.     Path(r"C:\Users\ynotf\.cursor").resolve(),
1013.     Path(r"C:\Users\ynotf\.openclaw").resolve(),
1014.     Path(r"C:\Users\ynotf\AppData\Roaming\Claude").resolve(),
1015.     Path(r"D:\Autonomy\secrets-backups").resolve(),
1016.     Path(r"D:\Obsidian").resolve(),
1017.     Path(r"F:\AgentCore").resolve(),
1018.     Path(r"F:\VectorDB").resolve(),
1019. ]
1020. 
1021. def is_child_or_same(path: Path, root: Path) -> bool:
1022.     return path == root or root in path.parents
1023. 
1024. def resolve_allowed_write_path(raw_path: str) -> Path:
1025.     target = Path(raw_path).resolve()
1026. 
1027.     for protected in PROTECTED_ROOTS:
1028.         if is_child_or_same(target, protected):
1029.             raise PermissionError(f"Protected path blocked: {target}")
1030. 
1031.     for root in ALLOWED_WRITE_ROOTS:
1032.         if is_child_or_same(target, root):
1033.             return target
1034. 
1035.     raise PermissionError(f"Path outside approved agent workspaces: {target}")
1036. ```
1037. 19.3 Lock table
1038. Resource	Lock key	Owner	Enforcement
1039. Target repo	`repo:<absolute_repo_path>`	Git Stream Specialist	file lock + git worktree allocation
1040. Worktree	`worktree:<run_id>:<branch>`	Builder Hub	run manifest
1041. AgentCore memory write	`memory:agent_core`	Memory Write Broker	Postgres advisory lock + queue
1042. SwarmVault write	`memory:swarmvault`	Memory Write Broker	queue + path lock
1043. Obsidian vault write	`obsidian:<vault_id>`	Documentation Engineer	filesystem/REST lock
1044. GitHub PR creation	`github:<owner/repo>`	Governance Hub	single writer per repo
1045. Docker stack mutation	`docker:<compose_project>`	Ops-approved task only	human approval
1046. Scheduled task mutation	`scheduled_task:<task_name>`	human/admin only	hard block by default
1047. 19.4 Approval tiers
1048. Action	Approval requirement
1049. Read repo files	automatic
1050. Read SwarmRecall/SwarmVault	automatic, read-only
1051. Create D:\AgentSwarm run folder	automatic
1052. Create git worktree	automatic if repo clean or baseline recorded
1053. Write patch in worktree	automatic
1054. Run tests/lint/typecheck	automatic
1055. Run secret/security scan	automatic
1056. Create PR	automatic after checks pass
1057. Merge PR	human or protected-branch gates only
1058. Deploy production	human approval
1059. DB migration	human approval
1060. Modify MCP config	human approval
1061. Modify scheduled tasks	human/admin approval
1062. Write Obsidian active vault	docs lock + task approval
1063. Write AgentCore memory	broker-only; no direct agent writes
1064. Stop Docker/Postgres/SwarmRecall	human approval
1065. ---
1066. PART 20 — MEMORY AND RAG OPERATING MODEL
1067. 20.1 Memory planes
1068. Plane	Location	Purpose	Write policy
1069. Working context	LangGraph state references	per-run routing and state	orchestrator only
1070. Run evidence	`D:\AgentSwarm\runs\<run_id>\evidence`	reproducibility	automatic
1071. Durable relational memory	`agent_core` Postgres :55432 on F:	canonical agent facts	Memory Broker only
1072. Vector memory	pgvector / Qdrant / SwarmRecall	retrieval	broker / ingestion job only
1073. Curated knowledge	SwarmVault	long-lived wiki/RAG	broker + docs approval
1074. Human notes	Obsidian	human-readable knowledge	docs writer lock only
1075. 20.2 Retrieval strategy
1076. The Context Hub should retrieve in this order:
1077. ```text
1078. 1. Repo-local AGENTS.md / README / architecture docs.
1079. 2. Current task issue/spec.
1080. 3. Git diff and recent commits.
1081. 4. SwarmVault curated rules for repo/project.
1082. 5. SwarmRecall prior task summaries.
1083. 6. Meilisearch full-text matches.
1084. 7. Vector top-k results with source IDs.
1085. 8. Target source files only after the candidate list is small.
1086. ```
1087. Never dump the entire memory store or full repo into model context. Return source IDs, paths, excerpts, and confidence.
1088. 20.3 Memory write event schema
1089. ```json
1090. {
1091.   "event_type": "agent_run_summary",
1092.   "run_id": "20260628-001",
1093.   "repo": "D:\\github\\example",
1094.   "branch": "ai/20260628-001/main",
1095.   "base_commit": "...",
1096.   "head_commit": "...",
1097.   "pr_url": "https://github.com/.../pull/123",
1098.   "task": "short task summary",
1099.   "decision": "merged|pr_opened|rejected|abandoned",
1100.   "durable_lessons": ["short fact 1", "short fact 2"],
1101.   "files_changed": ["src/foo.py"],
1102.   "tests_run": ["pytest", "npm test"],
1103.   "security_findings": [],
1104.   "source_evidence_paths": ["D:\\AgentSwarm\\runs\\...\\evidence\\scorecard.json"],
1105.   "created_at": "2026-06-28T00:00:00-04:00"
1106. }
1107. ```
1108. Memory writes must be short, source-attributed, non-secret, and deduplicated.
1109. ---
1110. PART 21 — CI/CD, PR, AND RELEASE MODEL
1111. 21.1 Required PR template
1112. Every autonomous PR should include:
1113. ```markdown
1114. ## Task
1115. <what was requested>
1116. 
1117. ## Selected approach
1118. <main vs A/B and why>
1119. 
1120. ## Files changed
1121. - file: reason
1122. 
1123. ## Verification evidence
1124. - Tests: pass/fail + command
1125. - Lint/typecheck: pass/fail + command
1126. - Security scan: pass/fail + tool
1127. - Performance: baseline vs result
1128. 
1129. ## Risks
1130. - migration risk
1131. - API compatibility risk
1132. - dependency risk
1133. 
1134. ## Rollback plan
1135. <exact rollback steps>
1136. 
1137. ## Memory update proposal
1138. <durable memory fact to store after approval>
1139. 
1140. ## Agent run metadata
1141. - run_id:
1142. - base_commit:
1143. - selected_branch:
1144. - evidence folder:
1145. ```
1146. 21.2 Required branch protection
1147. Recommended protected-branch settings for `main`:
1148. ```text
1149. Require pull request before merge
1150. Require at least one approval for high-risk code
1151. Require status checks
1152. Require conversation resolution
1153. Require signed commits if practical
1154. Require linear history or merge queue for busy repos
1155. Disallow force-push and deletion
1156. Restrict who can push directly to main
1157. Require deployment success before production merge where relevant
1158. ```
1159. 21.3 Minimal GitHub Actions check matrix
1160. ```yaml
1161. name: agent-pr-checks
1162. on:
1163.   pull_request:
1164.     branches: [main]
1165. 
1166. jobs:
1167.   verify:
1168.     runs-on: ubuntu-latest
1169.     steps:
1170.       - uses: actions/checkout@v4
1171.       - name: Set up project
1172.         run: echo "project-specific setup here"
1173.       - name: Lint
1174.         run: echo "run lint"
1175.       - name: Typecheck
1176.         run: echo "run typecheck"
1177.       - name: Test
1178.         run: echo "run tests"
1179.       - name: Secret scan
1180.         run: echo "run gitleaks or equivalent"
1181.       - name: Dependency audit
1182.         run: echo "run npm audit/pip-audit/etc"
1183. ```
1184. For production repos, add CodeQL, dependency review, container/IaC scanning, and required status checks before merge.
1185. ---
1186. PART 22 — OPERATIONS PLAYBOOK FOR WORKFLOW ENGINEERING
1187. 22.1 Preflight before any autonomous run
1188. ```powershell
1189. # Confirm AgentCore Postgres
1190. netstat -ano | findstr ":55432"
1191. 
1192. # Confirm SwarmRecall and Meilisearch
1193. netstat -ano | findstr ":3300"
1194. netstat -ano | findstr ":7700"
1195. 
1196. # Confirm Obsidian REST if docs/vault work is needed
1197. netstat -ano | findstr ":27124"
1198. 
1199. # Confirm Docker stack health if task uses n8n/Qdrant
1200. Docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
1201. 
1202. # Confirm target repo status
1203. git -C "D:\github\target-repo" status --short
1204. 
1205. # Confirm local model route if selected
1206. curl http://127.0.0.1:11434/api/tags
1207. ```
1208. 22.2 Refuse/stop conditions
1209. The orchestrator must stop and ask for intervention when:
1210. ```text
1211. target repo is dirty and no baseline approval exists
1212. required port is not listening
1213. Qdrant is reachable on LAN and task needs Qdrant writes
1214. Obsidian key has not been rotated and task needs vault writes
1215. tests require missing build tools and no bootstrap is approved
1216. agent wants to write to protected roots
1217. agent wants to modify secrets, MCP configs, scheduled tasks, or Docker services
1218. agent wants to run destructive git commands outside its worktree
1219. model budget or loop budget exceeded
1220. ```
1221. 22.3 Safe daily health summary
1222. ```powershell
1223. Get-CimInstance Win32_LogicalDisk | Select DeviceID, VolumeName,
1224.   @{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB,1)}},
1225.   @{N='TotalGB';E={[math]::Round($_.Size/1GB,1)}},
1226.   @{N='UsedPct';E={[math]::Round((1-$_.FreeSpace/$_.Size)*100,1)}} | Format-Table
1227. 
1228. Get-ScheduledTask -TaskPath '\AgentCore\' | Get-ScheduledTaskInfo |
1229.   Select TaskName, LastRunTime, LastTaskResult, NextRunTime | Format-Table
1230. 
1231. docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
1232. 
1233. $ports = @(3300,5432,5678,6333,6334,7700,9443,11434,18789,27124,55432)
1234. foreach ($p in $ports) { netstat -ano | findstr ":$p" }
1235. ```
1236. ---
1237. PART 23 — UPGRADE ROADMAP
1238. 23.1 Phase 0 — Safety blockers
1239. Priority	Upgrade	Outcome
1240. 1	Rotate Claude Desktop Obsidian key	Removes critical vault compromise path
1241. 2	Restrict Qdrant to loopback	Removes LAN vector DB exposure
1242. 3	Restrict Portainer/RDP	Reduces remote execution/control-plane risk
1243. 4	Split filesystem MCP profiles	Prevents raw writes to F: AgentCore and Obsidian
1244. 5	Create `D:\AgentSwarm` structure	Gives agents a safe default workspace
1245. 6	Disable direct auto-merge/deploy	Prevents runaway production changes
1246. 23.2 Phase 1 — Reliability and performance
1247. Priority	Upgrade	Outcome
1248. 1	Migrate Docker n8n/Qdrant volumes to F: bind mounts	Faster I/O, less C: pressure, direct backupability
1249. 2	Add Docker volume backup coverage	Protects n8n workflows and Qdrant vectors
1250. 3	Create `E:\CodexMemory` and `E:\CodexMemory\markdown-vault`	Fixes absent env target
1251. 4	Move `D:\HF_Cache` and `D:\models` to E: where practical	Frees D: for code/worktrees
1252. 5	Fix AgentCore scheduled task anomalies	Makes service restart operations trustworthy
1253. 6	Add deterministic scorecard	Reduces LLM hallucinated approvals
1254. 23.3 Phase 2 — Agent quality
1255. Priority	Upgrade	Outcome
1256. 1	Collapse 23 agents into six hubs	Faster and more stable runtime
1257. 2	Add Memory Write Broker	Prevents memory corruption and drift
1258. 3	Add prompt-injection/MCP red-team tests	Protects tool-connected agents
1259. 4	Add LangGraph/LangSmith/OpenTelemetry traces	Makes decisions auditable
1260. 5	Add internal benchmark tasks	Measures real repo performance, not vendor demos
1261. 23.4 Phase 3 — Optional hardware
1262. Do not buy hardware until after software-only migrations. All three M.2 slots are occupied. If more high-speed storage becomes necessary, options are:
1263. Option	When justified	Caveat
1264. Replace D: with larger NVMe	D: exceeds 80% after caches/backups moved	Requires data migration
1265. Replace C: with larger NVMe	C: exceeds 80% after Docker migration	Requires OS migration
1266. PCIe NVMe expansion card	confirmed free PCIe slot + lane sharing acceptable	PCIe slot availability still not recorded
1267. USB NVMe	archive/cache only	not for DB/vector hot tier
1268. ---
1269. PART 24 — OFFICIAL EXTERNAL REFERENCES USED FOR SOFTWARE DECISIONS
1270. These references are included so future engineers can verify why the workflow favors certain software:
1271. Topic	Reference
1272. LangGraph orchestration	`https://docs.langchain.com/oss/python/langgraph/overview`
1273. OpenAI Agents SDK	`https://developers.openai.com/api/docs/guides/agents`
1274. MCP security best practices	`https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices`
1275. GitHub Copilot cloud agent	`https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent`
1276. GitHub branch protection	`https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches`
1277. CodeQL code scanning	`https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-code-scanning`
1278. OWASP LLM Top 10	`https://owasp.org/www-project-top-10-for-large-language-model-applications/`
1279. SLSA supply-chain framework	`https://slsa.dev/`
1280. Promptfoo red teaming	`https://www.promptfoo.dev/docs/red-team/`
1281. ---
1282. PART 25 — FINAL ENGINEERING SUMMARY
1283. The current machine is already powerful enough for a highly capable autonomous developer team. The largest gains do not come from buying hardware. They come from:
1284. ```text
1285. 1. safety remediation,
1286. 2. narrow tool scopes,
1287. 3. isolated git worktrees,
1288. 4. single-writer memory/docs policy,
1289. 5. moving Docker hot data off C:,
1290. 6. deterministic verification,
1291. 7. PR-only governance,
1292. 8. traceable state and evidence,
1293. 9. six runtime hubs instead of 23 independent loops.
1294. ```
1295. The workflow should be engineered around the PC’s real topology:
1296. ```text
1297. C: protect
1298. D: build
1299. F: remember/search
1300. E: archive
1301. G: backup
1302. ```
1303. Once the critical exposures are fixed, this system can run as a local-first autonomous software factory with strong RAG, persistent memory, multi-agent coding, A/B implementation, deterministic verification, and governed PR creation.
