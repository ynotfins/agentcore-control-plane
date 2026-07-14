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
114. Case	HYTE Y70 Silver Wolf Honkai Star Rail Early Bird Edition
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
131. Free motherboard M.2 slots	NONE
132. M.2 slot-to-drive mapping	NOT RECORDED during inspection — requires follow-up
133. Additional PCIe NVMe storage	H: 2 TB internal NVMe installed via motherboard PCIe slot / NVMe expansion adapter (user-reported 2026-07-04); exact adapter, slot, lane width, and drive model TBD
134. GPU mount	Vertical (floor) mount via PCIe riser, ~6 in. from board
135. GPU slot label	NOT RECORDED
136. PCIe riser generation	NOT RECORDED
137. Other PCIe slots	One PCIe slot now used by H: NVMe expansion adapter; remaining free slots and lane sharing NOT RECORDED
138. SATA ports/cables	At least two internal SATA devices now installed: E: 10 TB HDD and I: 1 TB Crucial BX500 SSD; exact motherboard SATA port numbers NOT RECORDED
139. Expansion rule: Motherboard M.2 slots remain full. Additional NVMe is now possible only through PCIe expansion slots/adapters, with lane sharing and remaining slot availability to be verified. USB NVMe remains archive/transfer only, not preferred for live databases.
140. 1.2 Storage Devices
141. Drive	Model	Interface	Size	Drive letter	Volume label / state	Role
142. Internal NVMe	T-FORCE TM8FFW002T	PCIe NVMe	1.91 TB	C:	—	OS + user profile + Docker VHDX
143. Internal NVMe	T-FORCE TM8FFW002T	PCIe NVMe	1.91 TB	D:	New Volume	Dev workspaces + vaults + MCP
144. Internal NVMe	Samsung 990 PRO 4TB (heatsink)	PCIe Gen4	3.64 TB	F:	Agent_Vector_4TB	Hot DB + vectors
145. Internal NVMe	Model TBD — 2 TB NVMe installed in motherboard PCIe slot / expansion adapter	PCIe NVMe via adapter	2 TB nominal	H:	UNFORMATTED	New high-speed expansion NVMe tier — role TBD after format plan
146. Internal SATA SSD	Crucial BX500 1TB	SATA 6 Gb/s 2.5-inch SSD	1 TB nominal	I:	UNFORMATTED	New internal SATA SSD tier — role TBD after format plan
147. Internal SATA HDD	MDD HGST He10 / HUH721010ALE601 — 7200 RPM, 128 MB cache	SATA 6.0 Gb/s 3.5-inch enterprise HDD	10 TB nominal	E:	UNFORMATTED	New internal mass-storage / archive tier — role TBD after format plan
148. External USB HDD	Seagate BUP BK	USB HDD	3.64 TB	G:	Seagate Backup Plus	External backup
149. New-drive note	E:, H:, and I: are user-reported installed but unformatted as of 2026-07-04. Exact Windows usable capacity, partition style, filesystem, allocation unit size, and final volume labels must be recorded after formatting.					
150. 1.3 Storage Capacity (baseline + new unformatted drives, updated 2026-07-04)
151. Letter	Total	Free	Used%	Status
152. C:	1.91 TB	629 GB	67%	Existing OS NVMe — values from 2026-06-27 scan; re-scan after storage rebuild
153. D:	1.91 TB	893 GB	53%	Existing dev NVMe — values from 2026-06-27 scan; re-scan after storage rebuild
154. E:	10 TB nominal	N/A	N/A	NEW internal MDD HGST He10 HUH721010ALE601 HDD — UNFORMATTED
155. F:	3.64 TB	re-scan needed	re-scan needed	Existing Samsung 990 PRO hot DB/vector tier
156. G:	3.64 TB	2.17 TB	42%	Existing external backup target — values from 2026-06-27 scan
157. H:	2 TB nominal	N/A	N/A	NEW internal PCIe NVMe expansion drive — UNFORMATTED
158. I:	1 TB nominal	N/A	N/A	NEW internal Crucial BX500 SATA SSD — UNFORMATTED
159. C: warning threshold: 80% = ~1.53 TB used (2026-06-27 scan: ~1.28 TB used — ~250 GB until warning)  
160. Docker VHDX on C:: `docker_data.vhdx` = 14.08 GB in 2026-06-27 scan, growing with every container build
161. Post-format action: run `Get-CimInstance Win32_LogicalDisk` and update exact total/free/used values after E:, H:, and I: are partitioned and formatted.
162. 1.4 Drive Role Map (complete workload → path → drive)
163. Workload	Path	Drive
164. Windows-11-Pro OS	`C:\Windows\`	C:
165. 
166. User profile / app data	`C:\Users\ynotf\`	C:
167. Cursor install	`...\AppData\Local\Programs\cursor\`	C:
168. Cursor MCP config	`C:\Users\ynotf\.cursor\mcp.json`	C:
169. Cursor global storage	`...\Cursor\User\globalStorage\` (~13 GB)	C:
170. VS Code install + config	`...\Microsoft VS Code\` + `...\Code\User\`	C:
171. Android Studio + SDK	`C:\Program Files\Android\...` + `...\Android\Sdk\`	C:
172. ClawX binary	`C:\Program Files\ClawX\`	C:
173. OpenClaw config	`C:\Users\ynotf\.openclaw\`	C:
174. Codex home	`C:\Users\ynotf\.codex\`	C:
175. Codex skills	`C:\Users\ynotf\.agents\skills\`	C:
176. Ollama binary	`...\Programs\Ollama\ollama.exe`	C:
177. Open Interpreter	`...\Programs\Open Interpreter\`	C:
178. MiniMax Code	`...\Programs\MiniMax Code\`	C:
179. Docker Desktop	`C:\Program Files\Docker\`	C:
180. Docker WSL VHDX	`...\Docker\wsl\disk\docker_data.vhdx` (14 GB, growing)	C: ⚠ MIGRATE
181. n8n Postgres volume	Docker vol `local-agent-stack_postgres_data`	C: via VHDX ⚠
182. Qdrant Docker volume	Docker vol `agentops_qdrant_storage`	C: via VHDX ⚠
183. ChaosCentral SOT docs	`D:\ChaosCentral-Current-Build\`	D:
184. Primary dev monorepo	`D:\Autonomy\` (~98 GB)	D:
185. Codex managed workspace	`D:\Codex_Managed\` (~1.1 GB) + Python venv	D:
186. AgentOps infra / Qdrant compose	`D:\AgentOps\`	D:
187. MCP control plane	`D:\MCP-Control-Plane\`	D:
188. GitHub repos	`D:\github\`, `D:\github_2\`	D:
189. Obsidian active vault	`D:\Obsidian\Dungeon Vault\`	D:
190. Obsidian secondary vault	`D:\Obsidian\Obsidian Vault\`	D:
191. Global projects vault	`D:\Projects-Global\`	D:
192. HF model cache	`D:\HF_Cache\`	D: ⚠ candidate to move after new drive format plan — E: for cold/read-mostly cache, H: for high-I/O cache
193. LLM models	`D:\models\`	D: ⚠ candidate to move after new drive format plan — E: for large/cold models, H: for fast active model/cache work
194. Autonomy backups	`D:\Autonomy\Backups\`	D: ⚠ candidate to move to G:/E: after E: is formatted and backup policy is set
195. SENSITIVE — human only	`D:\Autonomy\secrets-backups\`	D:
196. Agent Postgres DB (native)	`F:\AgentCore\database_cluster\`	F: — DO NOT MOVE
197. Postgres runtime binaries	`F:\AgentCore\postgres_runtime_engine\pgsql\bin\`	F:
198. AgentCore memory workspace	`F:\AgentCore\agentmemory\`	F:
199. SwarmRecall data	`F:\AgentCore\agentmemory\swarmrecall\`	F:
200. SwarmVault	`F:\AgentCore\agentmemory\swarmvault\`	F:
201. Projection state	`F:\AgentCore\agentmemory\projection-state\`	F:
202. Qdrant native dir	`F:\VectorDB\qdrant\`	F:
203. Chroma native dir	`F:\VectorDB\chroma\`	F:
204. LanceDB native dir	`F:\VectorDB\lancedb\`	F:
205. pgvector artifacts	`F:\VectorDB\pgvector\`	F:
206. Agent core archive	`E:\AgentCoreArchive\` — MUST BE RECREATED after new E: format	E: pending format
207. Codex memory exports	`E:\CodexMemory\` — DOES NOT EXIST; MUST BE RECREATED after new E: format if E remains the memory-export target	E: pending format
208. PCIe NVMe expansion workspace	`H:\` — no approved root yet; drive is unformatted	H: pending format
209. SATA SSD utility / staging workspace	`I:\` — no approved root yet; drive is unformatted	I: pending format
210. Backup target	`G:\`	G:
211. 1.5 Paths That Must Not Be Moved
212. Path	Reason
213. `C:\Users\ynotf\.cursor\mcp.json`	Live Cursor MCP runtime — hardcoded by IDE
214. `D:\Codex_Managed\.venv\Scripts\python.exe`	Hardcoded in `mcp.json` global-memory-gateway command
215. `F:\AgentCore\database_cluster\`	Live Postgres data dir — stop `\AgentCore\PostgresRuntime` first
216. `F:\AgentCore\postgres_runtime_engine\`	Postgres binary referenced by scheduled task
217. `D:\Obsidian\Dungeon Vault\`	Active Obsidian vault — single writer policy
218. `D:\Autonomy\secrets-backups\`	Sensitive — no agent access
219. ---
220. PART 2 — SOFTWARE TOOLCHAIN (live, 2026-06-27)
221. 2.1 Core Runtimes
222. Tool	Version	Path
223. PowerShell	7.5.5	`C:\Program Files\PowerShell\7\pwsh.exe`
224. Node.js	v24.16.0	`C:\Program Files\nodejs\node.exe`
225. npm	11.13.0	nodejs dir
226. pnpm	11.7.0	Corepack shim
227. yarn	1.22.22	Corepack shim
228. Python 3.13 (default)	3.13.14	`...\Python313\python.exe`
229. Python 3.11 (legacy uvx path; not Serena default)	3.11.9	`...\Python311\Scripts\uvx.exe`
230. Python 3.12	3.12	MSIX
231. Python 3.10	3.10.11	winget
232. pip	26.1.2	Python 3.13 Scripts
233. uv	0.11.21	WinGet package
234. uvx	0.11.21	WinGet package
235. Java (PATH)	OpenJDK 21.0.11 LTS	Eclipse Adoptium JDK 21
236. JAVA_HOME	JDK 17.0.16	`...\jdk-17.0.16.8-hotspot\`
237. Git	2.51.1	`C:\Program Files\Git\cmd\git.exe`
238. GitHub CLI	2.93.0	`C:\Program Files\GitHub CLI\gh.exe`
239. Docker CLI	29.5.2	`C:\Program Files\Docker\...`
240. Docker Compose	v5.1.4 (plugin)	`docker compose`
241. C:\Windows-11-Pro\system32\wsl.exe`
242. winget	v1.29.280	—
243. ripgrep (rg)	15.1.0-cursor5	Cursor bundled
244. Not found in PATH: gradle, mvn, rustc, cargo, go, fd, jq
245. 2.2 IDEs and Agent Runtimes
246. 
247. Application	Version	Install path	Config
248. Cursor	1.126.0	`...\Programs\cursor\_\Cursor.exe`	`~/.cursor/mcp.json`
249. VS Code	1.126.0	`...\Microsoft VS Code\`	`AppData/Roaming/Code/User/`
250. Android Studio	2025.3	`C:\Program Files\Android\Android Studio\`	`AppData/Google/AndroidStudio*/`
251. OpenAI Codex	26.623.4041.0	WindowsApps MSIX	`C:\Users\ynotf\.codex\`
252. ClawX / OpenClaw	0.4.12	`C:\Program Files\ClawX\`	`~/.openclaw/openclaw.json`
253. MiniMax Code	—	`...\MiniMax Code\`	`~/.minimax/mcp/mcp.json`
254. Mavis	—	detected	`~/.mavis/mcp/mcp.json`
255. ChatGPT Desktop	1.2026.133.0	MSIX	—
256. Ollama	0.24.0	`...\Programs\Ollama\`	env vars
257. Open Interpreter	—	`...\Open Interpreter\`	`:5177`
258. Obsidian	1.12.7	`C:\Program Files\Obsidian\`	`AppData/Roaming/obsidian/`
259. Standard Notes	3.201.2	`@standardnotesinner-desktop`	`AppData/Roaming/@standardnotes/`
260. 2.3 Python Virtual Environments
261. venv	Path	Used by
262. Memory gateway	`D:\Codex_Managed\.venv\`	global-memory-gateway MCP — hardcoded path
263. Others	NOT exhaustively scanned	Per-project
264. ---
265. PART 3 — DATABASE AND VECTOR RUNTIME
266. 3.1 Active Services (all verified listening, 2026-06-27)
267. Service	Type	Port	Bind	Drive	Status
268. agent_core	PostgreSQL (native)	55432	127.0.0.1	F: Samsung 990 PRO	✅ Running
269. SwarmRecall API	Node.js API	3300	127.0.0.1	F:	✅ Running
270. Meilisearch	Full-text search	7700	127.0.0.1	UNKNOWN	✅ Running
271. n8n Postgres	PostgreSQL 18 (Docker)	5432	127.0.0.1	C: VHDX	✅ Running
272. Qdrant	Vector DB (Docker)	6333 / 6334	0.0.0.0	C: VHDX	✅ Running — LAN EXPOSED
273. n8n	Workflow automation	5678	127.0.0.1	C: VHDX	✅ Running
274. Ollama	LLM runtime	11434	127.0.0.1	—	⚠ Not listening at scan time
275. 3.2 agent_core PostgreSQL (primary)
276. Field	Value
277. Binary	`F:\AgentCore\postgres_runtime_engine\pgsql\bin\postgres.exe`
278. Config	`F:\AgentCore\database_cluster\postgresql.conf`
279. Port	55432
280. listen_addresses	localhost
281. max_connections	100
282. Database	`agent_core`
283. Roles	`agent_read` (RO), `agent_ingest` (RW), `agent_admin`
284. Env vars	`AGENT_CORE_PGHOST`, `AGENT_CORE_PGPORT`, `AGENT_CORE_PGDATABASE`, `AGENT_CORE_PGUSER`, `AGENT_CORE_AGENT_INGEST_PASSWORD` [REDACTED], `AGENT_CORE_AGENT_READ_PASSWORD` [REDACTED]
285. Scheduler	`\AgentCore\PostgresRuntime` scheduled task
286. Connection template	`postgresql://agent_read:[REDACTED]@127.0.0.1:55432/agent_core?sslmode=disable`
287. 3.3 Docker Stack Databases
288. DB	Container	Port	Volume	Data on
289. n8n Postgres 18	`local-agent-stack-postgres-1`	127.0.0.1:5432	`local-agent-stack_postgres_data`	C: VHDX
290. Qdrant	`agentops-qdrant`	0.0.0.0:6333-6334	`agentops_qdrant_storage`	C: VHDX
291. Portainer	`portainer`	0.0.0.0:9443, 8005	`portainer_data`	C: VHDX
292. n8n	`local-agent-stack-n8n-1`	127.0.0.1:5678	`local-agent-stack_n8n_data`	C: VHDX
293. Stopped containers (legacy): devcontainer-mariadb-1, devcontainer-redis-* (×3), devcontainer-frappe-1
294. 3.4 Native Vector Storage (F:)
295. Engine	Path	Status
296. Qdrant	`F:\VectorDB\qdrant\`	Directory exists
297. Chroma	`F:\VectorDB\chroma\`	Directory exists
298. LanceDB	`F:\VectorDB\lancedb\`	Directory exists
299. pgvector	`F:\VectorDB\pgvector\`	Directory exists
300. 3.5 Docker Compose Files
301. Stack	Compose file	Services
302. local-agent-stack	`D:\Autonomy\local-agent-stack\docker-compose.yml`	postgres, n8n, pgadmin (profile)
303. infra (AgentOps)	`D:\AgentOps\infra\docker-compose.yml`	qdrant, portainer
304. 3.6 Safe Connection Templates
305. ```
306. # Agent memory (primary — use this for AI agent connections)
307. postgresql://agent_read:[REDACTED]@127.0.0.1:55432/agent_core?sslmode=disable
308. postgresql://agent_ingest:[REDACTED]@127.0.0.1:55432/agent_core?sslmode=disable
309. 
310. # n8n automation DB (not for agents — n8n internal only)
311. postgresql://n8n:[REDACTED]@127.0.0.1:5432/n8n?sslmode=disable
312. 
313. # Qdrant vector DB
314. http://127.0.0.1:6333
315. # Header: api-key: [REDACTED] (if QDRANT_API_KEY set)
316. 
317. # Meilisearch (SwarmRecall)
318. http://127.0.0.1:7700
319. # Header: Authorization: Bearer [REDACTED]
320. 
321. # Ollama (when running)
322. http://127.0.0.1:11434/api/generate
323. ```
324. ---
325. PART 4 — MCP AND AGENT INTEGRATION MAP
326. 4.1 Config Files
327. Owner	Config path	Exists	Servers
328. Cursor (live)	`C:\Users\ynotf\.cursor\mcp.json`	✅	arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking, serena
329. OpenClaw / ClawX	`C:\Users\ynotf\.openclaw\openclaw.json`	✅	Same + eye2byte
330. 
331. MiniMax Code	`C:\Users\ynotf\.minimax\mcp\mcp.json`	✅	arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking
332. Mavis	`C:\Users\ynotf\.mavis\mcp\mcp.json`	✅	arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking
333. Claude Desktop	`AppData/Roaming/Claude/claude_desktop_config.json`	✅	droidrun, obsidian-mcp-tools — CONTAINS EMBEDDED SECRET
334. MCP control plane	`D:\MCP-Control-Plane\renderers\cursor-global.mcp.json`	✅	Renderer only — not live runtime
335. 4.2 MCP Server Registry
336. Server	Transport	Command / URL	FS write?	DB write?	Risk
337. arabold-docs	stdio	node → `arabold-docs-mcp/dist/index.js`	No	No	Low
338. artiforge	http	`https://tools.artiforge.ai/mcp?pat=[REDACTED]`	No	No	Low
339. context-fabric	stdio	node → `context-fabric/dist/index.js`	Minimal	No	Low
340. cursor-agent-mcp	stdio	`npx cursor-agent-mcp@latest`	Indirect	No	Medium
341. filesystem	stdio	`npx @modelcontextprotocol/server-filesystem`	YES — allowed roots	No	HIGH
342. global-memory-gateway	stdio	`D:\Codex_Managed\.venv\...\python.exe -m autonomy_factory.global_memory_gateway`	No	YES (agent_core :55432)	HIGH
343. github-mcp	stdio/Docker	`docker run ghcr.io/github/github-mcp-server`	No	No	Medium
344. mcp-debugger	stdio	`npx @debugmcp/mcp-debugger@latest`	No	No	Low
345. obsidian-vault	stdio → PS1	`C:\Users\ynotf\.openclaw\start-obsidian-mcp-server.ps1`	YES (via REST)	No	CRITICAL
346. playwright	stdio	`npx @playwright/mcp@latest`	Screenshots	No	Low–Medium
347. sequential-thinking	stdio	`npx @modelcontextprotocol/server-sequential-thinking`	No	No	Low
348. serena	stdio	`C:\Users\ynotf\AppData\Roaming\uv\tools\serena-agent\Scripts\serena.exe start-mcp-server --transport stdio --context <client-context>`	YES (code edits)	No	HIGH
349. eye2byte	stdio	OpenClaw-only	Unknown	Unknown	Medium
350. Filesystem MCP allowed roots:
351. ```
352. C:\Users\ynotf, D:\Codex_Managed, D:\cursor_setup, D:\openclaw, D:\Obsidian, F:\AgentCore, E:\AgentCoreArchive
353. > E:\AgentCoreArchive is a logical target only until the new E: drive is formatted and the directory is recreated. H: and I: are not approved MCP write roots until the drive-role plan is finalized.
354. ```
355. global-memory-gateway env vars:
356. ```
357. AGENT_CORE_PGHOST=127.0.0.1
358. AGENT_CORE_PGPORT=55432
359. AGENT_CORE_PGDATABASE=agent_core
360. AGENT_CORE_PGUSER=agent_ingest
361. AGENT_CORE_PGPASSWORD=[REDACTED]
362. OPENAI_API_KEY=[REDACTED]
363. MEM0_DEFAULT_USER_ID=master_developer_profile
364. ```
365. 4.3 New MCP Server Onboarding (mandatory procedure)
366. Read this file first — understand the existing server inventory.
367. Verify config: `Test-Path 'C:\Users\ynotf\.cursor\mcp.json'`
368. Verify command binary exists: `Test-Path <full path to executable>`
369. Verify env var names (not values): confirm vars are set in OS environment.
370. Verify port if TCP: `netstat -ano | findstr :<port>`
371. Start read-only first — use `agent_read` role, GET-only API calls.
372. Test tool discovery via IDE MCP panel before enabling writes.
373. Avoid writes until project explicitly approved for that session.
374. Log all actions to `D:\ChaosCentral-Current-Build\_evidence\`.
375. Never add `cursor-agent-mcp`, `global-memory-gateway`, or `obsidian-vault` writes without single-operator rule.
376. ---
377. PART 5 — NETWORK AND PORT MAP
378. 5.1 Complete Port Inventory (2026-06-27)
379. Port	Process	Bind	LAN?	Service
380. 55432	postgres.exe	127.0.0.1	No	Agent Core PostgreSQL
381. 5432	com.docker.backend	127.0.0.1	No	Docker → n8n Postgres
382. 5678	com.docker.backend	127.0.0.1	No	n8n UI
383. 6333	com.docker.backend	0.0.0.0	YES ⚠	Qdrant HTTP
384. 6334	com.docker.backend	0.0.0.0	YES ⚠	Qdrant gRPC
385. 7700	meilisearch.exe	127.0.0.1	No	SwarmRecall Meilisearch
386. 3300	node.exe	127.0.0.1	No	SwarmRecall API
387. 11434	ollama.exe	127.0.0.1	No	Ollama (when running)
388. 18789	ClawX.exe	127.0.0.1	No	OpenClaw gateway
389. 27124	Obsidian.exe	127.0.0.1	No	Obsidian REST (HTTPS)
390. 27123	Obsidian.exe	127.0.0.1	No	Obsidian REST (HTTP)
391. 8384	syncthing.exe	127.0.0.1	No	Syncthing UI
392. 45653	Standard Notes	127.0.0.1	No	Standard Notes local
393. 5177 / 19988	Interpreter.exe	127.0.0.1	No	Open Interpreter
394. 3389	svchost	0.0.0.0	YES ⚠	RDP
395. 8005	com.docker.backend	0.0.0.0	YES ⚠	Portainer HTTP
396. 9443	com.docker.backend	0.0.0.0	YES ⚠	Portainer HTTPS
397. 17500–17501	Dropbox.exe	0.0.0.0	Yes	Dropbox LAN sync
398. 22000	syncthing.exe	0.0.0.0	Yes	Syncthing data port
399. 443 (Tailscale)	tailscaled.exe	100.111.111.124	Tailscale	Tailscale VPN
400. 5.2 LAN Exposure Risk Matrix
401. Port	Service	Risk	Action needed
402. 6333–6334	Qdrant	CRITICAL	Bind to 127.0.0.1 in docker-compose.yml
403. 3389	RDP	HIGH	Restrict source IPs in Windows Firewall
404. 9443	Portainer HTTPS	HIGH	Strong password + firewall restriction
405. 8005	Portainer HTTP	HIGH	Bind to 127.0.0.1 or disable
406. 22000	Syncthing	Medium	Expected for LAN sync
407. 17500–17501	Dropbox	Medium	Expected for LAN sync
408. ---
409. PART 6 — AUTOMATION AND SERVICES
410. 6.1 Windows Services (running)
411. Service	Start type	Purpose
412. Tailscale	Automatic	VPN mesh
413. WSLService	Automatic	WSL 2
414. vmcompute	Manual	Docker / Hyper-V isolation
415. TermService	Manual	RDP
416. 6.2 Scheduled Tasks (2026-06-27 state)
417. Task	Path	State	Last result	Schedule
418. PostgresRuntime	`\AgentCore\`	Ready	3221225786 ⚠ FAILED	On demand / at boot
419. SwarmRecallApi	`\AgentCore\`	Ready	3221225786 ⚠	—
420. SwarmRecallMeilisearch	`\AgentCore\`	Ready	3221225786 ⚠	—
421. NightlyBackup	`\AgentCore\`	Ready	0 (success)	~3:00 AM
422. NightlyRestoreTest	`\AgentCore\`	Ready	0 (success)	~3:30 AM
423. DailyDriftCheck	`\AgentCore\`	Ready	0 (success)	~4:00 AM
424. WeeklyMaintenance	`\AgentCore\`	Ready	267011 (check)	Weekly
425. CodexDisasterRecovery6h	`\Codex\`	Ready	0 (success)	Every 6h
426. CodexHomeBackupEvery6Hours	`\Codex\`	Ready	0 (success)	Every 6h
427. CodexAgentStackBackup6h	`\`	Running	—	Every 6h
428. OpenClaw Gateway	`\`	Ready	0 (success)	—
429. LocalAgentStack-OllamaServe	`\`	Ready	0 (success)	—
430. Syncthing	`\`	Ready	0 (success)	—
431. > **⚠ PostgresRuntime / SwarmRecallApi / SwarmRecallMeilisearch** last result = 3221225786 (0xC000_0042 = STATUS_OBJECT_NAME_NOT_FOUND). The scheduled task binary path may be stale or the service is being launched differently now. Postgres IS listening on :55432 (confirmed by netstat), so it's starting through some other mechanism. Investigate task action arguments.
432. 6.3 Background Processes (running at scan time)
433. Process	PID (approx)	Ports	Purpose
434. postgres.exe (×7)	—	55432	Agent core Postgres
435. meilisearch.exe	—	7700	SwarmRecall
436. ollama.exe	—	(not listening)	Ollama (idle)
437. ClawX.exe (×5)	—	18789	OpenClaw gateway
438. Interpreter.exe	—	5177, 19988	Open Interpreter
439. syncthing.exe	—	8384, 22000	File sync
440. Dropbox.exe	—	17500–17501	Cloud sync
441. com.docker.backend	—	many	Docker Desktop
442. tailscaled.exe	—	443	Tailscale
443. Obsidian.exe	—	27123, 27124	Vault + REST API
444. 6.4 Local API Endpoints
445. URL	Auth	Purpose
446. `http://127.0.0.1:5678`	username/password	n8n workflow UI
447. `http://127.0.0.1:7700`	Master key header	Meilisearch
448. `http://127.0.0.1:11434`	None (localhost)	Ollama API
449. `http://127.0.0.1:8384`	GUI password	Syncthing UI
450. `http://127.0.0.1:18789`	Gateway token [REDACTED]	OpenClaw gateway
451. `https://127.0.0.1:27124`	Bearer [REDACTED]	Obsidian REST
452. `https://localhost:9443`	Admin password	Portainer
453. `http://127.0.0.1:6333`	API key [REDACTED] optional	Qdrant
454. `http://127.0.0.1:3300`	API key [REDACTED]	SwarmRecall API
455. ---
456. PART 7 — KNOWLEDGE VAULTS
457. 7.1 Obsidian Vaults
458. Vault	Path	Active	Files	Size
459. Dungeon Vault	`D:\Obsidian\Dungeon Vault\`	YES — auto-opens	207	~141 MB
460. Obsidian Vault	`D:\Obsidian\Obsidian Vault\`	No	71	~9.3 MB
461. Projects-Global	`D:\Projects-Global\`	No	32	~4.9 MB
462. Obsidian running: Yes | REST :27123: Yes | REST :27124: Yes | Dropbox dup: No (was present, now gone)
463. MCP access to vaults:
464. Cursor/OpenClaw: `obsidian-vault` MCP → PowerShell → HTTPS :27124 → `OBSIDIAN_API_KEY` [REDACTED]
465. Claude Desktop: `obsidian-mcp-tools` → plugin binary → EMBEDDED KEY IN CONFIG — ROTATE IMMEDIATELY
466. 7.2 Agent Memory Paths
467. Path	Role	Agent access
468. `D:\Codex_Managed\`	Codex Python workspace	Read/write with care
469. `D:\memory-bank\`	Placeholder (empty)	Free to use
470. `D:\CursorMemory\`	Cursor memory (~19 KB)	Read/write
471. `E:\CodexMemory\`	Codex memory exports root — DOES NOT EXIST; E: has been replaced with a new unformatted 10 TB HDD	Create only after E: is formatted and the drive-role plan confirms E remains the Codex memory export target
472. `E:\CodexMemory\markdown-vault\`	(env `CODEX_MEMORY_MARKDOWN_VAULT`) — absent; E: pending format	Create only after E: is formatted
473. 7.3 Write Policy
474. Active vault (Dungeon Vault): Use `obsidian-vault` MCP REST only. Never direct filesystem write while Obsidian is open.
475. Syncthing: Pause before bulk programmatic writes; resume after.
476. Dropbox vault copy: Not currently detected — read-only if it returns.
477. One writer per vault — Cursor, ClawX, MiniMax, Claude all have separate MCP paths; coordinate before concurrent vault operations.
478. ---
479. PART 8 — ENVIRONMENT VARIABLES (names only — values redacted)
480. Database
481. Variable	Value/Role
482. `AGENT_CORE_PGHOST`	127.0.0.1
483. `AGENT_CORE_PGPORT`	55432
484. `AGENT_CORE_PGDATABASE`	agent_core
485. `AGENT_CORE_PGUSER`	agent_ingest
486. `AGENT_CORE_AGENT_INGEST_PASSWORD`	[REDACTED]
487. `AGENT_CORE_AGENT_ADMIN_PASSWORD`	[REDACTED]
488. `AGENT_CORE_AGENT_READ_PASSWORD`	[REDACTED]
489. `AGENT_CORE_POSTGRES_PASSWORD`	[REDACTED]
490. `AGENT_CORE_SWARMRECALL_API_KEY`	[REDACTED]
491. `AGENT_CORE_SWARMRECALL_MEILI_MASTER_KEY`	[REDACTED]
492. `N8N_ENCRYPTION_KEY`	[REDACTED]
493. `QDRANT_API_KEY`	[REDACTED]
494. AI / LLM
495. Variable	Used by
496. `OPENAI_API_KEY`	arabold-docs, global-memory-gateway, embeddings
497. `CURSOR_API_KEY`	cursor-agent-mcp
498. `ARTIFORGE_PAT`	artiforge MCP
499. `MEM0_API_KEY`	mem0 / OpenMemory
500. `OPENMEMORY_API_KEY`	OpenMemory
501. `OLLAMA_HOST`	127.0.0.1:11434
502. `OLLAMA_DEFAULT_MODEL`	qwen3-coder:30b
503. `OPENCLAW_GATEWAY_TOKEN`	ClawX gateway
504. `OPENCLAW_CODEX_API_KEY`	OpenClaw Codex
505. Obsidian
506. Variable	Value
507. `OBSIDIAN_API_KEY`	[REDACTED]
508. `OBSIDIAN_LOCAL_REST_API`	[REDACTED]
509. `OBSIDIAN_BASE_URL`	https://127.0.0.1:27124
510. `OBSIDIAN_PORT`	27124
511. Codex paths
512. Variable	Value
513. `CODEX_HOME`	`C:\Users\ynotf\.codex`
514. `CODEX_MEMORY_ROOT`	`E:\CodexMemory` (path ABSENT; E: replaced with new unformatted 10 TB HDD — recreate after format if still desired)
515. `CODEX_MEMORY_MARKDOWN_VAULT`	`E:\CodexMemory\markdown-vault` (absent; E: pending format)
516. `CODEX_ALLOWED_ROOTS`	`C:\Users\ynotf;E:\CodexMemory;C:\Users\ynotf\CodexAutonomyStack` (E: path inactive until recreated after format)
517. `CODEX_PROTECTED_ROOTS`	`C:\Windows;C:\Program Files;...`
518. `CODEX_SKILLS_HOME`	`C:\Users\ynotf\.agents\skills\`
519. VCS / containers
520. Variable	Used by
521. `GITHUB_PERSONAL_ACCESS_TOKEN`	github-mcp, gh CLI
522. `GITHUB_TOKEN`	GitHub Actions
523. `DOCKERHUB_USERNAME`	ynotfins
524. `ANDROID_HOME`	`C:\Users\ynotf\AppData\Local\Android\Sdk`
525. `JAVA_HOME`	`...\jdk-17.0.16.8-hotspot`
526. ---
527. PART 9 — SECURITY BASELINE
528. Critical items requiring immediate action
529. #	Item	Severity
530. 1	Plaintext Obsidian API key in Claude Desktop config	CRITICAL — rotate now
531. 2	Qdrant :6333/:6334 on 0.0.0.0	CRITICAL — restrict to 127.0.0.1
532. 3	RDP :3389 on 0.0.0.0	HIGH — add firewall IP restriction
533. 4	Portainer :9443/:8005 on 0.0.0.0	HIGH — strong password + restrict
534. 5	`D:\Autonomy\secrets-backups\` not in any sync tool	HIGH — audit
535. Agent least-privilege rules
536. Connect as `agent_read` first; escalate to `agent_ingest` only with task justification.
537. Load all credentials from OS environment — never from this file or any docs.
538. Never write to `C:\Users\ynotf\.cursor\mcp.json` without human approval.
539. Never modify scheduled tasks without human approval.
540. Never run `docker stop/rm` on production containers without human approval.
541. Use `CODEX_PROTECTED_ROOTS` to prevent writes to `C:\Windows`, `C:\Program Files`, etc.
542. Log every write action to `D:\ChaosCentral-Current-Build\_evidence\`.
543. Config files that may contain secrets
544. File	Risk
545. `AppData/Roaming/Claude/claude_desktop_config.json`	CRITICAL — plaintext key
546. `~/.openclaw/openclaw.json`	Gateway token — verify is `${env:...}` reference
547. `D:\Autonomy\` docker `.env` files	May contain passwords — never commit
548. ---
549. PART 10 — BACKUP AND DISASTER RECOVERY
550. Backup coverage summary
551. Asset	Coverage	Gap
552. Agent Postgres (`F:\AgentCore\database_cluster\`)	`\AgentCore\NightlyBackup` → `F:\AgentCore\backups\`	✅ Covered
553. Obsidian Dungeon Vault	Syncthing + Dropbox sync	⚠ Sync ≠ backup
554. Codex home (`~/.codex/`)	`CodexHomeBackupEvery6Hours`	✅
555. Codex managed workspace	`CodexAgentStackBackup6h`	✅
556. n8n workflows (Docker volume)	NOT CONFIRMED	HIGH GAP
557. Qdrant vectors (Docker volume)	NOT CONFIRMED	HIGH GAP
558. `~/.cursor/mcp.json`	NOT CONFIRMED	HIGH GAP
559. `~/.openclaw/openclaw.json`	NOT CONFIRMED	HIGH GAP
560. `F:\VectorDB\` native dirs	NOT CONFIRMED	HIGH GAP
561. Windows env / Credential Manager	`secrets-backups/` dir exists; coverage unknown	CRITICAL GAP
562. GitHub repos	Git remote push (if pushed)	⚠ If not pushed, lost
563. Restore order (catastrophic failure)
564. F: Agent Postgres — `F:\AgentCore\backups\` restore
565. Windows env secrets — `D:\Autonomy\secrets-backups\`
566. MCP configs — `~/.cursor/mcp.json`, `~/.openclaw/`
567. Codex home — from 6h backup
568. Codex managed workspace / venv
569. Obsidian vaults — Syncthing peer or Dropbox
570. Docker volumes — rebuild or restore
571. GitHub repos — re-clone
572. D:\Autonomy — restore from archive; E: archive paths must be recreated after formatting the new 10 TB HDD
573. ---
574. PART 11 — CAPACITY AND PERFORMANCE
575. Drive	Total	Free	Used%	Growth hotspot
576. C:	1.91 TB	629 GB	67%	Docker VHDX (~14 GB growing), Cursor globalStorage (~13 GB) — values from 2026-06-27 scan
577. D:	1.91 TB	893 GB	53%	D:\Autonomy (~98 GB), HF_Cache, models — values from 2026-06-27 scan
578. E:	10 TB nominal	N/A	N/A	NEW unformatted MDD HGST He10 internal HDD — mass storage/archive/cold tier candidate
579. F:	3.64 TB	re-scan needed	re-scan needed	Existing Samsung 990 PRO hot DB/vector tier
580. G:	3.64 TB	2.17 TB	42%	External backup accumulation — values from 2026-06-27 scan
581. H:	2 TB nominal	N/A	N/A	NEW unformatted internal PCIe NVMe expansion drive — high-speed scratch/Docker/WSL/cache candidate
582. I:	1 TB nominal	N/A	N/A	NEW unformatted Crucial BX500 SATA SSD — utility/staging/light-cache candidate
583. Warning thresholds: C: → 80% (~1.53 TB used, ~250 GB away in 2026-06-27 scan); D: → 80% (~1.53 TB used, ~520 GB away in 2026-06-27 scan)
584. RAM: 128 GB — fully populated, no expansion possible  
585. GPU VRAM: 12 GB GDDR6X — Ollama `qwen3-coder:30b` may require quantization at high load  
586. CPU: i9-14900KF — not a bottleneck for current stack  
587. I/O bottleneck: Docker VHDX on C: (OS NVMe) competes with system I/O — migrate off C: after format plan, likely to H: for isolated high-speed container/WSL scratch or F: for DB/vector bind mounts where appropriate
588. ---
589. PART 12 — EXPANSION DECISION GUIDE
590. Hardware expansion status (post 2026-07-04 drive additions)
591. Motherboard M.2 NVMe: NO FREE MOTHERBOARD M.2 SLOTS. All 3 (M.2_1, M.2_2, M.2_3) are occupied. Cannot add another motherboard M.2 drive without removing/replacing one.
592. PCIe NVMe expansion: H: 2 TB internal NVMe has now been added through a motherboard PCIe slot / expansion adapter. Exact adapter, PCIe slot, lane width, and lane sharing still need to be recorded.
593. SATA expansion: E: 10 TB internal HDD and I: 1 TB Crucial BX500 internal SATA SSD are now installed. Exact SATA port numbers and remaining free SATA ports still need to be recorded.
594. PSU: Corsair RM1000 1000W — ~600 W headroom — adequate for the current added drives and typical storage expansion.
595. Options if more storage is needed:
596. Option	Feasibility	Best for
597. Replace C: T-FORCE (1.91 TB) → larger NVMe	Viable (OS migration)	If OS drive space remains the constraint after Docker/cache migration
598. Replace D: T-FORCE (1.91 TB) → larger NVMe	Viable (data migration)	If dev workspace remains the constraint after caches/backups move
599. Additional PCIe NVMe expansion	Unknown — H: already uses one PCIe slot; remaining slots/lane sharing not recorded	Only after ASUS lane-sharing check
600. Additional SATA storage	Unknown — at least two SATA devices now installed; remaining port count/ports not recorded	Cold archive or backup, not hot DB/vector tier
601. USB NVMe enclosure	Not for DBs	Archive/backup/transfer only
602. Before purchase / format checklist:
603. [ ] Record H: NVMe model, adapter model, PCIe slot, lane width, and lane-sharing impact
604. [ ] Record E: and I: SATA port numbers and cable routing
605. [ ] Download ASUS Z790 GAMING WIFI7 manual — check lane sharing for the H: PCIe NVMe adapter
606. [ ] Confirm riser cable PCIe generation
607. [ ] Confirm BIOS/device-manager visibility for E:, H:, and I:
608. [ ] Format E:, H:, and I: with final partition style/filesystem/volume labels, then re-run storage inventory
609. Software-only capacity improvements (after format plan)
610. Action	Expected gain
611. Move Docker data root / bind mounts off C: to H: or F: where appropriate	-14 GB+ from C: VHDX, stops growth, separates container I/O from OS
612. Move `D:\HF_Cache\` to E: for cold cache or H: for active high-I/O cache	Frees D:
613. Move `D:\models\` to E: for large/cold models or H: for active fast model work	Frees D:
614. Archive `D:\Autonomy\Backups\` → G:/E:	Frees up to tens of GB from D:
615. Move n8n Postgres + Qdrant volumes to F:/H: bind mounts after final drive-role decision	Better I/O + enables direct backup
616. ---
617. PART 13 — AUTONOMOUS WORKFLOW DESIGN GUIDE
618. System architecture flow
619. ```
620. New AI Agent
621.     │
622.     ▼
623. IDE / Agent Runtime
624. (Cursor :1.126 / Codex :26.623 / ClawX :0.4 / MiniMax / Mavis)
625.     │
626.     ▼
627. ~/.cursor/mcp.json  (or per-IDE equivalent)
628.     │
629.     ├── stdio MCP servers (serena, filesystem, playwright, sequential-thinking, arabold-docs)
630.     │
631.     ├── global-memory-gateway (stdio → Python venv D:\Codex_Managed\.venv)
632.     │         │
633.     │         ▼
634.     │   PostgreSQL :55432 agent_core  (F: Samsung 990 PRO Gen4)
635.     │
636.     ├── obsidian-vault (stdio → PS1 → HTTPS :27124)
637.     │         │
638.     │         ▼
639.     │   D:\Obsidian\Dungeon Vault\   (D: T-FORCE NVMe)
640.     │
641.     ├── github-mcp (stdio → ephemeral Docker container)
642.     │
643.     └── OpenClaw gateway :18789
644.               │
645.               ▼
646.          ClawX.exe → eye2byte + all Cursor MCPs
647.               │
648.               ▼
649.     Qdrant :6333 (Docker) → agentops_qdrant_storage (C: VHDX — migrate off C: to F:/H: bind mount after final drive-role plan)
650. ```
651. Multi-agent coordination rules
652. Rule	Reason
653. Single writer to agent_core Postgres	global-memory-gateway spawns one writer; Cursor + OpenClaw + Mavis can all trigger it — coordinate or use sequential sessions
654. Single writer to Obsidian vault	obsidian-vault MCP via REST; do not use filesystem MCP on vault while Obsidian is open
655. Do not confuse :55432 vs :5432	55432 = agent memory (F:, native); 5432 = n8n automation DB (C:, Docker)
656. Pause Syncthing before bulk vault writes	File conflict artifacts
657. Load all secrets from env, never from docs	All [REDACTED] values must be read at runtime from Windows environment
658. Use agent_read for discovery, agent_ingest for writes	Postgres least privilege
659. Log all write actions to `D:\ChaosCentral-Current-Build\_evidence\`	Audit trail
660. Agent onboarding checklist (Step 1 of every new session)
661. Step 1 — Read source of truth:
662. [ ] Read `MCP_AND_AI_AGENT_INTEGRATION.md` (Part 4 of this doc)
663. [ ] Read `DATABASE_AND_VECTOR_STORAGE.md` (Part 3)
664. [ ] Read `NETWORK_AND_PORTS.md` (Part 5)
665. [ ] Read `DRIVE_ROLE_MAP.md` (Part 1.4)
666. Step 2 — Verify live runtime:
667. [ ] Confirm `~/.cursor/mcp.json` exists
668. [ ] Confirm `:55432` listening: `netstat -ano | findstr 55432`
669. [ ] Confirm `:27124` listening (if vault access needed)
670. [ ] Confirm `D:\Codex_Managed\.venv\Scripts\python.exe` exists
671. [ ] Confirm no backup task running (NightlyBackup ~3:00 AM)
672. Step 3 — Connect with least privilege:
673. [ ] DB: use `agent_read` role first
674. [ ] Vault: use obsidian-vault MCP REST only
675. [ ] Filesystem: scope to narrowest allowed root
676. [ ] Escalate to `agent_ingest` only when explicit write task begins
677. [ ] Abort on port, path, or schema mismatch
678. Known friction points for autonomous workflow
679. PostgresRuntime task last result = 3221225786 — scheduled task binary path stale; Postgres IS running but task state inconsistent. Investigate task action before relying on task-based restart.
680. Docker DBs on C: VHDX — I/O contention + no direct backup path + growth pressure on OS drive.
681. Qdrant LAN-exposed — fix before exposing any agent that calls Qdrant to external network.
682. Plaintext Obsidian key in Claude Desktop — any agent using Claude Desktop can write to vault without MCP guardrails.
683. `E:\CodexMemory\` path absent — env var set but directory does not exist; E: has been replaced with a new unformatted 10 TB HDD, so recreate only after format and drive-role decision.
684. Multiple IDEs (Cursor + ClawX + MiniMax + Mavis) all pointing to same Postgres agent_core — ensure only one memory-writing session active at a time.
685. No vault write-lock protocol — implement coordination mechanism before running parallel vault-writing agents.
686. git status — 12/13 repos dirty — many uncommitted changes in D:\github repos; may affect agent code operations.
687. ---
688. PART 14 — STILL REQUIRES ADMIN OR PHYSICAL INSPECTION
689. Item	How to resolve
690. Drive health (SMART)	`Get-PhysicalDisk` as admin
691. BitLocker encryption status	`Get-BitLockerVolume` as admin
692. Exact disk-to-letter mapping	`Get-Partition -DriveLetter` as admin
693. Full firewall rule export	`Get-NetFirewallRule` as admin
694. M.2 slot-to-drive mapping (which is C:, D:, F:) plus H: PCIe adapter slot/lane mapping	Physical inspection + label silkscreen + device manager/BIOS
695. CPU cooler brand/model	Physical inspection
696. GPU PCIe slot label	Physical inspection
697. GPU power connector type	Physical inspection
698. PCIe riser cable generation	Physical inspection
699. Remaining empty PCIe slots / H: adapter slot / lane sharing	Physical inspection + ASUS manual
700. SATA ports/cables for E: and I:, plus remaining free SATA ports	Physical inspection
701. `\AgentCore\PostgresRuntime` task failure root cause	`Get-ScheduledTask
702. NightlyBackup coverage (what exactly it backs up)	Inspect task script
703. Meilisearch data directory	Inspect SwarmRecallMeilisearch task action
704. ---
705. PART 15 — RECOMMENDED ACTIONS (ranked by impact)
706. #	Action	Impact
707. 1	Rotate Claude Desktop Obsidian API key; replace with `${env:OBSIDIAN_LOCAL_REST_API}` env ref	CRITICAL
708. 2	Restrict Qdrant to 127.0.0.1 in `D:\AgentOps\infra\docker-compose.yml`	CRITICAL
709. 3	Add Windows Firewall rule restricting RDP :3389 to trusted IPs	HIGH
710. 4	Migrate Docker volumes off C: to F:/H: bind mounts after final drive-role plan (removes C: VHDX pressure + enables backup)	HIGH
711. 5	Move `D:\HF_Cache\` + `D:\models\` off D: after format plan — E: for cold/large assets, H: for high-I/O active cache/model work	HIGH
712. 6	Add Docker volume backup (n8n Postgres + Qdrant) to NightlyBackup	HIGH
713. 7	Create `E:\CodexMemory\` directory tree after the new E: drive is formatted, if E remains the Codex memory export target	HIGH
714. 8	Single canonical Obsidian write path; retire Claude obsidian-mcp-tools	HIGH
715. 9	Investigate and fix `\AgentCore\PostgresRuntime` task result 3221225786	MEDIUM
716. 10	Discover Meilisearch data dir; add to backup	MEDIUM
717. 11	Record M.2 slot-to-drive mapping on next case opening	MEDIUM
718. 12	Check BIOS 1805 against latest ASUS update	LOW
719. ---
720. APPENDIX — EVIDENCE PROVENANCE
721. Source	Date	Type
722. PowerShell CIM discovery (Win32_BaseBoard, Win32_BIOS, Win32_Processor, Win32_PhysicalMemory, Win32_VideoController, Win32_DiskDrive, Win32_LogicalDisk, Win32_PnPEntity)	2026-06-26	Automated
723. `netstat -ano`, `tasklist`, `docker ps`, `docker volume ls/inspect`, `docker compose ls`, `wsl --list`, `winget list`, `Get-ScheduledTask`, `Get-Service`	2026-06-27	Automated (scripts/Collect-SystemEcosystemInventory.ps1)
724. MCP config files read: `mcp.json`, `openclaw.json`, `minimax/mcp.json`, `mavis/mcp.json`, `claude_desktop_config.json`, docker-compose YAML, `postgresql.conf`	2026-06-27	File inspection
725. nvidia-smi telemetry	2026-06-27	Live
726. Physical case inspection	2026-06-27	Human observation
727. User-reported storage additions	2026-07-04	H: 2 TB internal PCIe NVMe, I: 1 TB Crucial BX500 SATA SSD, E: MDD HGST He10 HUH721010ALE601 10 TB SATA HDD; all three unformatted
728. Evidence JSON	`D:\ChaosCentral-Current-Build\_evidence\system-ecosystem-20260627-194037.json`	229 KB
729. All credential values in this document are `[REDACTED]`. No secrets were stored during generation.
730. 
731. ---
732. PART 16 — OPTIMIZED 23-AGENT WORKFLOW FOR THIS PC
733. 16.1 Why not run all 23 as independent runtime agents
734. The 23-agent plan is strong as a mental model, but weak as a literal execution graph. The main failure modes are predictable:
735. Failure mode	What happens	PC-specific effect
736. Context bloat	Every agent appends logs, code, critiques, and state	Huge prompts, slow loops, lower quality
737. Critic contradiction	Code critic, architecture critic, performance critic, and judge disagree	Rework loops burn API budget and never merge
738. Same-working-tree branch collision	Main builder and A/B builder both call `git checkout` in same repo	Branch corruption, lost diffs, broken commits
739. Memory write race	Many agents write persistent memory directly	Duplicate, stale, or contradictory AgentCore facts
740. Obsidian write race	Docs agent, Claude plugin, filesystem MCP, and Obsidian REST can all touch vault	Sync conflicts or note corruption
741. Over-privileged tool access	Filesystem MCP and Open Interpreter can reach broad paths	Accidental secrets/config/database damage
742. Latency explosion	23 model calls plus tests and retries	Simple PRs become long and expensive
743. Therefore: keep the 23 roles, but execute them as six hubs.
744. 16.2 Recommended six-hub runtime mapping
745. Runtime hub	Absorbed 23-agent roles	Allowed tools	Writes?
746. 1. Intake + Policy Hub	Orchestrator Lead, Specification & Scope, Token Budget Guard, Human Proxy	issue reader, repo metadata, cost ledger	run manifest only
747. 2. Context / Architecture / RAG Hub	Context Weaver, Modular Architect, Macro Best Practices, Refactor Catalyst, Friction & Unused Code	filesystem read, git read, SwarmRecall read, SwarmVault read, Meilisearch read	context bundle only
748. 3. Main Builder Hub	Lead Implementer, Real-Time Debugger, Refactor Executor	git worktree, filesystem write in worktree, test command runner	isolated worktree only
749. 4. A/B Builder Hub	A/B Branch Creator, Parallel Stream Specialist, Real-Time Debugger	separate git worktree, filesystem write in worktree, test command runner	isolated worktree only
750. 5. Verification + Critic Hub	QA & Unit Test, Integration Tester, Performance & Drift Checker, Primary/Secondary/Tertiary Critics, A/B Evaluator	test/lint/type/security scanners, coverage, benchmark runner	reports only
751. 6. Governance / PR / Memory-Broker Hub	Scorer, Judge, Git Stream Specialist, Documentation Engineer, Human Proxy	GitHub CLI/API, docs writer lock, memory broker, PR creator	PR, docs, approved memory event
752. The Omniagent Interface Agent should become a tool gateway library, not a reasoning agent. It should enforce path guards, port policy, token budget, credential lookup, command allowlists, retry/timeout behavior, and trace logging.
753. 16.3 Canonical autonomous run flow
754. ```text
755. 1. Create run_id.
756. 2. Create D:\AgentSwarm\runs\<run_id>\.
757. 3. Create run manifest and budget ledger.
758. 4. Refuse unsafe target repos unless baseline state is known.
759. 5. Create two isolated worktrees:
760.       D:\AgentSwarm\runs\<run_id>\main
761.       D:\AgentSwarm\runs\<run_id>\ab
762. 6. Context Hub reads repo docs, AGENTS.md, architecture files, SwarmRecall, SwarmVault.
763. 7. Context Hub emits compact task packet: scope, allowed files, tests, risks, acceptance criteria.
764. 8. Main Builder creates conventional patch in main worktree.
765. 9. A/B Builder creates alternative patch in ab worktree.
766. 10. Verification Hub runs deterministic checks on both worktrees.
767. 11. Critic Hub reads evidence, not whole transcripts.
768. 12. Scorer computes deterministic score.
769. 13. Judge selects main, A/B, or reject/rework.
770. 14. Governance Hub creates PR only; no direct merge.
771. 15. Documentation Engineer updates docs through a docs lock.
772. 16. Memory Write Broker writes one durable memory summary only after approval.
773. 17. Run artifacts are archived; raw temporary worktrees may be retained for replay or cleaned after retention period.
774. ```
775. 16.4 Required run folder layout
776. ```text
777. D:\AgentSwarm\
778.   runs\
779.     <run_id>\
780.       run_manifest.json
781.       budget_ledger.jsonl
782.       locks\
783.       main\                 # git worktree for conventional implementation
784.       ab\                   # git worktree for alternative implementation
785.       evidence\
786.         context_bundle.json
787.         repo_map.txt
788.         test_main.json
789.         test_ab.json
790.         lint_main.json
791.         lint_ab.json
792.         security_main.sarif
793.         security_ab.sarif
794.         perf_main.json
795.         perf_ab.json
796.         critic_report.json
797.         scorecard.json
798.         judge_decision.json
799.       patches\
800.         main.patch
801.         ab.patch
802.       logs\
803.         orchestrator.jsonl
804.         tools.jsonl
805.         subprocess.jsonl
806.         model_usage.jsonl
807.       docs\
808.         pr_body.md
809.         rollback_plan.md
810.         memory_event_proposal.md
811.   artifacts\
812.   locks\
813.   cache\
814. ```
815. Recommended root creation command:
816. ```powershell
817. New-Item -ItemType Directory -Force `
818.   D:\AgentSwarm\runs, `
819.   D:\AgentSwarm\artifacts, `
820.   D:\AgentSwarm\logs, `
821.   D:\AgentSwarm\locks, `
822.   D:\AgentSwarm\cache
823. ```
824. 16.5 Required git worktree model
825. Never let both builders write to one repo working directory. Use worktrees:
826. ```powershell
827. $Repo = 'D:\github\your-repo'
828. $Run  = '20260628-001-feature-name'
829. $Root = "D:\AgentSwarm\runs\$Run"
830. 
831. New-Item -ItemType Directory -Force $Root
832. 
833. git -C $Repo fetch origin main
834. git -C $Repo worktree add "$Root\main" -b "ai/$Run/main" origin/main
835. git -C $Repo worktree add "$Root\ab"   -b "ai/$Run/ab"   origin/main
836. ```
837. All agent commands must use explicit working directory:
838. ```powershell
839. git -C "$Root\main" status --short
840. git -C "$Root\ab" status --short
841. ```
842. The PR branch should be created from the selected worktree only after verification. Do not auto-delete other worktrees until evidence is preserved.
843. 16.6 Reference-based graph state
844. Do not store full code, raw logs, and giant transcripts in LangGraph state. Store paths and references:
845. ```python
846. from typing import TypedDict, Literal
847. 
848. class BranchState(TypedDict, total=False):
849.     branch_name: str
850.     worktree_path: str
851.     base_commit: str
852.     head_commit: str
853.     patch_path: str
854.     test_report_path: str
855.     lint_report_path: str
856.     security_report_path: str
857.     perf_report_path: str
858.     score: dict
859. 
860. class TeamState(TypedDict, total=False):
861.     run_id: str
862.     task_id: str
863.     repo_root: str
864.     risk_class: Literal['low', 'medium', 'high', 'critical']
865.     allowed_write_roots: list[str]
866.     protected_roots: list[str]
867.     task_packet_path: str
868.     context_refs: list[dict]
869.     branches: dict[str, BranchState]
870.     selected_branch: str
871.     judge_decision_path: str
872.     pr_url: str
873.     loop_count: int
874.     budget: dict
875.     locks: dict
876.     next_node: str
877. ```
878. 16.7 Deterministic scorecard
879. The Scorer should not ask an LLM to invent a grade. Compute the grade from evidence first, then ask an LLM to explain it.
880. Category	Weight	Data source
881. Correctness	30	unit/integration/e2e tests
882. Security	20	secret scan, CodeQL/SAST, dependency scan, MCP/tool risk
883. Maintainability	20	diff size, complexity, architecture rules, affected modules
884. Performance	15	benchmark delta, memory delta, DB query count, cold-start time
885. Operability	10	logs, rollback plan, migrations, feature flags, docs
886. Cost/latency	5	token spend, runtime, agent loop count
887. Hard fails:
888. ```text
889. Any hardcoded secret                          → fail
890. Any test failure in required suite            → fail
891. Any critical CodeQL/SAST finding              → fail
892. Direct write outside allowed worktree         → fail
893. Direct write to F:\AgentCore raw paths         → fail
894. Direct write to active Obsidian vault by FS   → fail
895. Unapproved DB migration                       → fail
896. Unapproved main merge or production deploy    → fail
897. ```
898. ---
899. PART 17 — SOFTWARE SELECTION MATRIX
900. 17.1 Orchestration layer
901. Candidate	Fit for ChaosCentral	Recommendation
902. LangGraph	Excellent for durable, stateful, branchy workflows with checkpoints, persistence, subgraphs, human review, and state inspection	Primary orchestrator
903. OpenAI Agents SDK	Excellent inside code-first hubs that need typed tools, MCP, guardrails, hosted tools, and SDK-managed run objects	Use inside hubs; do not replace LangGraph unless workflow becomes OpenAI-only
904. n8n	Excellent for schedule/event glue, notifications, webhook handoffs, backup monitors	Use for automation edges, not core code-writing brain	
905. Cursor agent mode	Excellent human-in-the-loop IDE surface	Primary operator UI; not the durable workflow engine
906. GitHub Copilot cloud agent	Good for GitHub-native hosted PR tasks, especially routine issues and independent comparison	External comparator / overflow worker
907. OpenClaw/ClawX	Useful secondary gateway with MCP parity and custom tools	Keep, but restrict write scope and avoid parallel memory writers
908. MiniMax/Mavis	Useful secondary experiments	Read-mostly until policy is proven
909. Open Interpreter	Powerful but high risk because it executes arbitrary code	Quarantine; never connect to production DBs by default
910. AutoGen-style fully free multi-agent swarm	More complexity and weaker fit than LangGraph for your current state/memory needs	Do not make it the main runtime
911. 17.2 Coding-agent layer
912. Tool	Best use	Do not use for
913. Cursor	Interactive architecture, local edits, MCP reads, controlled agent sessions	Unlocked autonomous writes to broad filesystem roots
914. Codex CLI/Desktop	Local coding tasks, repo-level edits, automation handoffs, evidence generation	Direct production deploys or direct raw memory writes
915. GitHub Copilot cloud agent	Hosted branch work, routine bugs, docs, tests, GitHub issue tasks	Local SwarmVault/SwarmRecall access; it should not own local memory
916. Claude Code / frontier code agent if installed later	Complex refactors, codebase reasoning, long debugging loops	Sole judge/security authority without deterministic scans
917. Ollama local model	Cheap summarization, log clustering, first-pass doc drafts	Final architecture, final security review, critical judge decisions
918. 17.3 Memory / RAG / search layer
919. Component	Role	Recommendation
920. AgentCore Postgres `agent_core` :55432	Canonical durable agent memory DB	Keep canonical; connect as `agent_read` first; write only through broker
921. pgvector	Vector search inside canonical Postgres	Preferred for memory facts tied to relational metadata
922. SwarmRecall API :3300	Recall/runtime API	Read-heavy; write through broker or approved gateway
923. SwarmVault	Curated long-term RAG/wiki	Treat as durable knowledge, not scratchpad
924. Meilisearch :7700	Full-text index for SwarmRecall	Keep local; add backup coverage once data dir confirmed
925. Qdrant	High-performance vector DB	Fix loopback + migrate data to F: before expanding use
926. Chroma/LanceDB dirs	Local vector experiments	Use only when a project explicitly needs local embedded vector files
927. Obsidian	Human-readable knowledge vault	Use REST MCP with one writer; not raw file writes
928. 17.4 Security / verification toolchain
929. Minimum recommended gate stack:
930. ```text
931. Unit tests + integration tests + typecheck + lint
932. + secret scanning
933. + dependency scanning
934. + CodeQL/SAST
935. + container/IaC scan where relevant
936. + prompt-injection / MCP-tool red-team tests
937. + deterministic scorecard
938. + PR branch protection
939. ```
940. Recommended tools by role:
941. Need	Recommended tool family	Notes
942. Static security	CodeQL, Semgrep	CodeQL integrates with GitHub code scanning; Semgrep is useful locally/CI
943. Secret scanning	GitHub secret scanning, gitleaks/detect-secrets	Must run before any PR
944. Dependency review	Dependabot, GitHub dependency review, npm/pip audit	Required for agent-added packages
945. Container/IaC	Trivy, Docker Scout, checkov/tflint where applicable	Relevant to Docker/n8n/Qdrant stack
946. AI red-team	Promptfoo	Use for prompt injection, RAG leakage, tool misuse, MCP attack scenarios
947. Observability	LangSmith, OpenTelemetry, Phoenix-style traces	Must record model calls, tool calls, paths, decisions, cost
948. Supply-chain integrity	SLSA provenance, signed artifacts, pinned actions	Important once agents can release packages or build images
949. ---
950. PART 18 — BOTTLENECK AND FRICTION MATRIX
951. 18.1 Ranked bottlenecks
952. Rank	Bottleneck	Current evidence	Workflow impact	Fix
953. 1	Qdrant LAN exposure	`6333/6334` on `0.0.0.0`	Data exfiltration / malicious vector writes	Bind to `127.0.0.1`; add API key
954. 2	Plaintext Obsidian key	Claude Desktop config contains embedded key	Vault write compromise	Rotate key, env var only, retire duplicate MCP
955. 3	Broad filesystem MCP roots	`C:\Users\ynotf`, `D:\Obsidian`, `F:\AgentCore` in scope	Accidental or malicious writes to configs/DB/vault	Split read-only/write profiles
956. 4	Docker DBs on C: VHDX	n8n Postgres + Qdrant in Docker VHDX	OS-drive I/O contention and backup gap	Move off C: to F:/H: bind mounts after final drive-role plan
957. 5	Multi-agent memory writes	global-memory-gateway writes to `agent_core`	Race conditions and inconsistent facts	Single Memory Write Broker
958. 6	Obsidian sync/write overlap	Obsidian + Syncthing + MCP + possible Claude plugin	Note corruption / sync conflicts	Single writer lock; REST-only
959. 7	Dirty repo set	Many repos not clean in latest scan	Agents may overwrite human work	Baseline diff capture and refusal policy
960. 8	Raw 23-agent graph	too many nodes, critics, loops	Latency/cost/context bloat	Six hubs with compact state
961. 9	Ollama unavailable at scan	`11434` false in latest report	local-model route fails	preflight route check
962. 10	Toolchain gaps	Gradle/Maven/Rust/Go/fd/jq not in PATH	builds may fail or agents improvise	per-project tool bootstrap
963. 11	Motherboard M.2 expansion blocked, PCIe NVMe now added	all three motherboard M.2 slots occupied; H: 2 TB PCIe NVMe expansion installed	future NVMe expansion depends on remaining PCIe slots/lane sharing	record H: adapter slot/lane mapping before further expansion
964. 12	Scheduled task anomaly	AgentCore persistent tasks show `3221225786`	restart automation uncertainty	inspect task actions and fix launchers
965. 18.2 Measurement plan
966. Metric	Command/source	Warning	Critical
967. C: used %	`Get-CimInstance Win32_LogicalDisk`	80%	90%
968. D: used %	same	80%	90%
969. E: used %	same after format	70%	85%
970. F: used %	same	70%	85%
971. H: used %	same after format	70%	85%
972. I: used %	same after format	70%	85%
973. Docker VHDX size	`Get-Item ...docker_data.vhdx`	50 GB	100 GB
974. GPU VRAM used	`nvidia-smi`	10 GB	11.5 GB
975. Postgres connections	`pg_stat_activity`	>70	>90
976. Agent loop count	run manifest	3	5
977. Agent cost/run	model usage ledger	configurable	hard stop
978. Worktree disk per run	`Get-ChildItem D:\AgentSwarm\runs`	10 GB	25 GB
979. Dirty repo count	`git status --short` sweep	>0 for target repo	refuse if untracked secrets/large diffs
980. PR failure rate	GitHub checks	>20%	>50%
981. Memory write queue depth	broker metrics	>50	>200
982. 18.3 Performance tuning targets
983. Component	Target behavior
984. CPU	Use 8–12 test workers initially; avoid saturating 32 threads while IDEs/DBs active
985. RAM	Plenty for local indexing; cap per-process memory for test runners and vector ingestion
986. GPU	One heavy local LLM job at a time; quantized models only for 30B-class workloads
987. D:	Fast code/test tier; avoid filling with model caches/backups
988. F:	Hot DB/vector tier; all access through services/APIs except maintenance windows
989. H:	New high-speed PCIe NVMe expansion tier after format; strong candidate for Docker/WSL scratch, active caches, and isolated high-I/O noncanonical workloads
990. I:	New SATA SSD tier after format; candidate for staging, utility scratch, installers, lightweight cache, or noncritical service data
991. E:	New 10 TB internal HDD after format; cold model/cache/archive/mass storage tier, not hot DB/vector tier
992. G:	External backup only; never live DB
993. ---
994. PART 19 — WRITE SAFETY, LOCKING, AND PATH GUARDS
995. 19.1 Mandatory path policy
996. Agents may write automatically only under:
997. ```text
998. D:\AgentSwarm\runs\
999. D:\AgentSwarm\logs\
1000. D:\AgentSwarm\artifacts\
1001. D:\github\<repo>\ only through git worktrees or approved repo scope
1002. D:\github_2\<repo>\ only through git worktrees or approved repo scope
1003. D:\Autonomy\ only with project-specific approval
1004. ```
1005. Agents must not write automatically to:
1006. ```text
1007. C:\Windows\
1008. C:\Program Files\
1009. C:\Users\ynotf\.cursor\mcp.json
1010. C:\Users\ynotf\.openclaw\openclaw.json
1011. C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json
1012. D:\Autonomy\secrets-backups\
1013. D:\Obsidian\* by filesystem writes
1014. F:\AgentCore\database_cluster\
1015. F:\AgentCore\agentmemory\
1016. F:\VectorDB\* by raw file writes
1017. E:\AgentCoreArchive\ except append-only archive operations after E: is formatted and recreated
1018. H:\ until drive-role plan approves specific write roots
1019. I:\ until drive-role plan approves specific write roots
1020. G:\ except backup jobs
1021. ```
1022. 19.2 Python path guard
1023. ```python
1024. from pathlib import Path
1025. 
1026. ALLOWED_WRITE_ROOTS = [
1027.     Path(r"D:\AgentSwarm\runs").resolve(),
1028.     Path(r"D:\AgentSwarm\logs").resolve(),
1029.     Path(r"D:\AgentSwarm\artifacts").resolve(),
1030.     Path(r"D:\github").resolve(),
1031.     Path(r"D:\github_2").resolve(),
1032. ]
1033. 
1034. PROTECTED_ROOTS = [
1035.     Path(r"C:\Windows").resolve(),
1036.     Path(r"C:\Program Files").resolve(),
1037.     Path(r"C:\Users\ynotf\.cursor").resolve(),
1038.     Path(r"C:\Users\ynotf\.openclaw").resolve(),
1039.     Path(r"C:\Users\ynotf\AppData\Roaming\Claude").resolve(),
1040.     Path(r"D:\Autonomy\secrets-backups").resolve(),
1041.     Path(r"D:\Obsidian").resolve(),
1042.     Path(r"F:\AgentCore").resolve(),
1043.     Path(r"F:\VectorDB").resolve(),
1044. ]
1045. 
1046. def is_child_or_same(path: Path, root: Path) -> bool:
1047.     return path == root or root in path.parents
1048. 
1049. def resolve_allowed_write_path(raw_path: str) -> Path:
1050.     target = Path(raw_path).resolve()
1051. 
1052.     for protected in PROTECTED_ROOTS:
1053.         if is_child_or_same(target, protected):
1054.             raise PermissionError(f"Protected path blocked: {target}")
1055. 
1056.     for root in ALLOWED_WRITE_ROOTS:
1057.         if is_child_or_same(target, root):
1058.             return target
1059. 
1060.     raise PermissionError(f"Path outside approved agent workspaces: {target}")
1061. ```
1062. 19.3 Lock table
1063. Resource	Lock key	Owner	Enforcement
1064. Target repo	`repo:<absolute_repo_path>`	Git Stream Specialist	file lock + git worktree allocation
1065. Worktree	`worktree:<run_id>:<branch>`	Builder Hub	run manifest
1066. AgentCore memory write	`memory:agent_core`	Memory Write Broker	Postgres advisory lock + queue
1067. SwarmVault write	`memory:swarmvault`	Memory Write Broker	queue + path lock
1068. Obsidian vault write	`obsidian:<vault_id>`	Documentation Engineer	filesystem/REST lock
1069. GitHub PR creation	`github:<owner/repo>`	Governance Hub	single writer per repo
1070. Docker stack mutation	`docker:<compose_project>`	Ops-approved task only	human approval
1071. Scheduled task mutation	`scheduled_task:<task_name>`	human/admin only	hard block by default
1072. 19.4 Approval tiers
1073. Action	Approval requirement
1074. Read repo files	automatic
1075. Read SwarmRecall/SwarmVault	automatic, read-only
1076. Create D:\AgentSwarm run folder	automatic
1077. Create git worktree	automatic if repo clean or baseline recorded
1078. Write patch in worktree	automatic
1079. Run tests/lint/typecheck	automatic
1080. Run secret/security scan	automatic
1081. Create PR	automatic after checks pass
1082. Merge PR	human or protected-branch gates only
1083. Deploy production	human approval
1084. DB migration	human approval
1085. Modify MCP config	human approval
1086. Modify scheduled tasks	human/admin approval
1087. Write Obsidian active vault	docs lock + task approval
1088. Write AgentCore memory	broker-only; no direct agent writes
1089. Stop Docker/Postgres/SwarmRecall	human approval
1090. ---
1091. PART 20 — MEMORY AND RAG OPERATING MODEL
1092. 20.1 Memory planes
1093. Plane	Location	Purpose	Write policy
1094. Working context	LangGraph state references	per-run routing and state	orchestrator only
1095. Run evidence	`D:\AgentSwarm\runs\<run_id>\evidence`	reproducibility	automatic
1096. Durable relational memory	`agent_core` Postgres :55432 on F:	canonical agent facts	Memory Broker only
1097. Vector memory	pgvector / Qdrant / SwarmRecall	retrieval	broker / ingestion job only
1098. Curated knowledge	SwarmVault	long-lived wiki/RAG	broker + docs approval
1099. Human notes	Obsidian	human-readable knowledge	docs writer lock only
1100. 20.2 Retrieval strategy
1101. The Context Hub should retrieve in this order:
1102. ```text
1103. 1. Repo-local AGENTS.md / README / architecture docs.
1104. 2. Current task issue/spec.
1105. 3. Git diff and recent commits.
1106. 4. SwarmVault curated rules for repo/project.
1107. 5. SwarmRecall prior task summaries.
1108. 6. Meilisearch full-text matches.
1109. 7. Vector top-k results with source IDs.
1110. 8. Target source files only after the candidate list is small.
1111. ```
1112. Never dump the entire memory store or full repo into model context. Return source IDs, paths, excerpts, and confidence.
1113. 20.3 Memory write event schema
1114. ```json
1115. {
1116.   "event_type": "agent_run_summary",
1117.   "run_id": "20260628-001",
1118.   "repo": "D:\\github\\example",
1119.   "branch": "ai/20260628-001/main",
1120.   "base_commit": "...",
1121.   "head_commit": "...",
1122.   "pr_url": "https://github.com/.../pull/123",
1123.   "task": "short task summary",
1124.   "decision": "merged|pr_opened|rejected|abandoned",
1125.   "durable_lessons": ["short fact 1", "short fact 2"],
1126.   "files_changed": ["src/foo.py"],
1127.   "tests_run": ["pytest", "npm test"],
1128.   "security_findings": [],
1129.   "source_evidence_paths": ["D:\\AgentSwarm\\runs\\...\\evidence\\scorecard.json"],
1130.   "created_at": "2026-06-28T00:00:00-04:00"
1131. }
1132. ```
1133. Memory writes must be short, source-attributed, non-secret, and deduplicated.
1134. ---
1135. PART 21 — CI/CD, PR, AND RELEASE MODEL
1136. 21.1 Required PR template
1137. Every autonomous PR should include:
1138. ```markdown
1139. ## Task
1140. <what was requested>
1141. 
1142. ## Selected approach
1143. <main vs A/B and why>
1144. 
1145. ## Files changed
1146. - file: reason
1147. 
1148. ## Verification evidence
1149. - Tests: pass/fail + command
1150. - Lint/typecheck: pass/fail + command
1151. - Security scan: pass/fail + tool
1152. - Performance: baseline vs result
1153. 
1154. ## Risks
1155. - migration risk
1156. - API compatibility risk
1157. - dependency risk
1158. 
1159. ## Rollback plan
1160. <exact rollback steps>
1161. 
1162. ## Memory update proposal
1163. <durable memory fact to store after approval>
1164. 
1165. ## Agent run metadata
1166. - run_id:
1167. - base_commit:
1168. - selected_branch:
1169. - evidence folder:
1170. ```
1171. 21.2 Required branch protection
1172. Recommended protected-branch settings for `main`:
1173. ```text
1174. Require pull request before merge
1175. Require at least one approval for high-risk code
1176. Require status checks
1177. Require conversation resolution
1178. Require signed commits if practical
1179. Require linear history or merge queue for busy repos
1180. Disallow force-push and deletion
1181. Restrict who can push directly to main
1182. Require deployment success before production merge where relevant
1183. ```
1184. 21.3 Minimal GitHub Actions check matrix
1185. ```yaml
1186. name: agent-pr-checks
1187. on:
1188.   pull_request:
1189.     branches: [main]
1190. 
1191. jobs:
1192.   verify:
1193.     runs-on: ubuntu-latest
1194.     steps:
1195.       - uses: actions/checkout@v4
1196.       - name: Set up project
1197.         run: echo "project-specific setup here"
1198.       - name: Lint
1199.         run: echo "run lint"
1200.       - name: Typecheck
1201.         run: echo "run typecheck"
1202.       - name: Test
1203.         run: echo "run tests"
1204.       - name: Secret scan
1205.         run: echo "run gitleaks or equivalent"
1206.       - name: Dependency audit
1207.         run: echo "run npm audit/pip-audit/etc"
1208. ```
1209. For production repos, add CodeQL, dependency review, container/IaC scanning, and required status checks before merge.
1210. ---
1211. PART 22 — OPERATIONS PLAYBOOK FOR WORKFLOW ENGINEERING
1212. 22.1 Preflight before any autonomous run
1213. ```powershell
1214. # Confirm AgentCore Postgres
1215. netstat -ano | findstr ":55432"
1216. 
1217. # Confirm SwarmRecall and Meilisearch
1218. netstat -ano | findstr ":3300"
1219. netstat -ano | findstr ":7700"
1220. 
1221. # Confirm Obsidian REST if docs/vault work is needed
1222. netstat -ano | findstr ":27124"
1223. 
1224. # Confirm Docker stack health if task uses n8n/Qdrant
1225. Docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
1226. 
1227. # Confirm target repo status
1228. git -C "D:\github\target-repo" status --short
1229. 
1230. # Confirm local model route if selected
1231. curl http://127.0.0.1:11434/api/tags
1232. ```
1233. 22.2 Refuse/stop conditions
1234. The orchestrator must stop and ask for intervention when:
1235. ```text
1236. target repo is dirty and no baseline approval exists
1237. required port is not listening
1238. Qdrant is reachable on LAN and task needs Qdrant writes
1239. Obsidian key has not been rotated and task needs vault writes
1240. tests require missing build tools and no bootstrap is approved
1241. agent wants to write to protected roots
1242. agent wants to modify secrets, MCP configs, scheduled tasks, or Docker services
1243. agent wants to run destructive git commands outside its worktree
1244. model budget or loop budget exceeded
1245. ```
1246. 22.3 Safe daily health summary
1247. ```powershell
1248. Get-CimInstance Win32_LogicalDisk | Select DeviceID, VolumeName,
1249.   @{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB,1)}},
1250.   @{N='TotalGB';E={[math]::Round($_.Size/1GB,1)}},
1251.   @{N='UsedPct';E={[math]::Round((1-$_.FreeSpace/$_.Size)*100,1)}} | Format-Table
1252. 
1253. Get-ScheduledTask -TaskPath '\AgentCore\' | Get-ScheduledTaskInfo |
1254.   Select TaskName, LastRunTime, LastTaskResult, NextRunTime | Format-Table
1255. 
1256. docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
1257. 
1258. $ports = @(3300,5432,5678,6333,6334,7700,9443,11434,18789,27124,55432)
1259. foreach ($p in $ports) { netstat -ano | findstr ":$p" }
1260. ```
1261. ---
1262. PART 23 — UPGRADE ROADMAP
1263. 23.1 Phase 0 — Safety blockers
1264. Priority	Upgrade	Outcome
1265. 1	Rotate Claude Desktop Obsidian key	Removes critical vault compromise path
1266. 2	Restrict Qdrant to loopback	Removes LAN vector DB exposure
1267. 3	Restrict Portainer/RDP	Reduces remote execution/control-plane risk
1268. 4	Split filesystem MCP profiles	Prevents raw writes to F: AgentCore and Obsidian
1269. 5	Create `D:\AgentSwarm` structure	Gives agents a safe default workspace
1270. 6	Disable direct auto-merge/deploy	Prevents runaway production changes
1271. 23.2 Phase 1 — Reliability and performance
1272. Priority	Upgrade	Outcome
1273. 1	Migrate Docker n8n/Qdrant volumes off C: to F:/H: bind mounts after final drive-role plan	Faster I/O, less C: pressure, direct backupability
1274. 2	Add Docker volume backup coverage	Protects n8n workflows and Qdrant vectors
1275. 3	After formatting new E:, create `E:\CodexMemory` and `E:\CodexMemory\markdown-vault` if E remains the Codex memory export target	Fixes absent env target without assuming old E: contents still exist
1276. 4	Move `D:\HF_Cache` and `D:\models` off D: where practical — E: for cold/large assets, H: for active high-I/O assets	Frees D: for code/worktrees
1277. 5	Fix AgentCore scheduled task anomalies	Makes service restart operations trustworthy
1278. 6	Add deterministic scorecard	Reduces LLM hallucinated approvals
1279. 23.3 Phase 2 — Agent quality
1280. Priority	Upgrade	Outcome
1281. 1	Collapse 23 agents into six hubs	Faster and more stable runtime
1282. 2	Add Memory Write Broker	Prevents memory corruption and drift
1283. 3	Add prompt-injection/MCP red-team tests	Protects tool-connected agents
1284. 4	Add LangGraph/LangSmith/OpenTelemetry traces	Makes decisions auditable
1285. 5	Add internal benchmark tasks	Measures real repo performance, not vendor demos
1286. 23.4 Phase 3 — Optional hardware
1287. Do not buy more hardware until the new E:, H:, and I: drives are formatted, assigned roles, and measured. All three motherboard M.2 slots are occupied, and one PCIe slot is now used by the H: NVMe expansion adapter. If more high-speed storage becomes necessary, options are:
1288. Option	When justified	Caveat
1289. Replace D: with larger NVMe	D: exceeds 80% after caches/backups moved	Requires data migration
1290. Replace C: with larger NVMe	C: exceeds 80% after Docker migration	Requires OS migration
1291. Additional PCIe NVMe expansion	H: is insufficient and another free PCIe slot/lane budget is confirmed	Requires ASUS lane-sharing validation; current remaining PCIe slot availability not recorded
1292. Additional SATA HDD/SSD	Cold/archive/staging capacity is needed after E:/I: roles are set	Requires SATA port/power/cooling check
1293. USB NVMe	archive/cache/transfer only	not for DB/vector hot tier
1294. ---
1295. PART 24 — OFFICIAL EXTERNAL REFERENCES USED FOR SOFTWARE DECISIONS
1296. These references are included so future engineers can verify why the workflow favors certain software:
1297. Topic	Reference
1298. LangGraph orchestration	`https://docs.langchain.com/oss/python/langgraph/overview`
1299. OpenAI Agents SDK	`https://developers.openai.com/api/docs/guides/agents`
1300. MCP security best practices	`https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices`
1301. GitHub Copilot cloud agent	`https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent`
1302. GitHub branch protection	`https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches`
1303. CodeQL code scanning	`https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-code-scanning`
1304. OWASP LLM Top 10	`https://owasp.org/www-project-top-10-for-large-language-model-applications/`
1305. SLSA supply-chain framework	`https://slsa.dev/`
1306. Promptfoo red teaming	`https://www.promptfoo.dev/docs/red-team/`
1307. ---
1308. PART 25 — FINAL ENGINEERING SUMMARY
1309. The current machine is already powerful enough for a highly capable autonomous developer team. The largest gains do not come from buying hardware. They come from:
1310. ```text
1311. 1. safety remediation,
1312. 2. narrow tool scopes,
1313. 3. isolated git worktrees,
1314. 4. single-writer memory/docs policy,
1315. 5. moving Docker hot data off C:,
1316. 6. deterministic verification,
1317. 7. PR-only governance,
1318. 8. traceable state and evidence,
1319. 9. six runtime hubs instead of 23 independent loops.
1320. ```
1321. The workflow should be engineered around the PC’s real topology:
1322. ```text
1323. C: protect
1324. D: build
1325. F: remember/search
1326. H: high-speed expansion tier after format
1327. I: SATA utility/staging tier after format
1328. E: internal mass archive/cold storage after format
1329. G: external backup
1330. ```
1331. Once the critical exposures are fixed, this system can run as a local-first autonomous software factory with strong RAG, persistent memory, multi-agent coding, A/B implementation, deterministic verification, and governed PR creation.
1332. Case- Official HYTE Y70 Silver Wolf Honkai Star Rail Case Early Bird Edition
