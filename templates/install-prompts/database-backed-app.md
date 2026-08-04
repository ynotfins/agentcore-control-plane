# Database-backed App Install Prompt

```text
DATABASE-BACKED APP INTAKE - READ ONLY FIRST

Target app/repo:
Name: <APP NAME>
Candidate path: <PATH>
Source/installer: <URL / COMMAND / PATH>
Purpose: <PURPOSE>

Work from @D:\github\agentcore-control-plane.

Read:
@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md
@D:\github\agentcore-control-plane\DOC_AUTHORITY.md
@D:\github\agentcore-control-plane\docs\install-platform\INSTALLATION_POLICY.md
@D:\github\agentcore-control-plane\docs\install-platform\INSTALL_NEW_THING.md
@D:\github\agentcore-control-plane\contracts\install-target-policy.json

Do not mutate anything until the plan is approved.

Required investigation:
1. Prove the project root. If it is a Git repo, use git rev-parse --show-toplevel.
2. Identify every durable store the app uses: SQLite, Chroma, LanceDB, DuckDB, Postgres, Meilisearch, Qdrant, cache, logs, uploads, runtime state.
3. Identify whether any inherited global environment variable such as DATABASE_URL changes app behavior.
4. Identify whether the app has official config support for moving data off the source repo.
5. If not, propose a backup plus NTFS junction from the repo-local data path to I:\LocalApps\<AppName>\data.

Hard storage rule:
- No primary DB/vector/index/app data on C: or D:.
- Default data target: I:\LocalApps\<AppName>\data.
- Default backup target: E:\LocalApps\Backups\<AppName>.
- Do not reuse AgentCore, Swarm, or neutral Recall databases directly.

Output:
- proven project root
- current storage paths
- proposed storage paths
- backup path
- exact migration plan
- rollback plan
- health checks
- files that would change
- commands pending approval
```
