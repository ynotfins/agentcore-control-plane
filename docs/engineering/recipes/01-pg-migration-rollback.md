# Recipe 01 — PostgreSQL Migration and Rollback

**Pattern:** versioned, idempotent, reversible schema change with evidence record.  
**Stack:** PostgreSQL 18, psycopg 3.x, PowerShell.  
**Reference implementation:** `docs/engineering/reference-implementations/pg-migration-rollback/`

---

## Structure

```
migrations/
  <milestone>/
    NNN_up_<description>.sql     ← apply
    NNN_down_<description>.sql   ← rollback
```

## UP Migration Template

```sql
-- <milestone> NNN UP - <Description>
-- Authority: BLUEPRINT.md <milestone>
-- Target: PostgreSQL 18 agent_core on 127.0.0.1:55433

BEGIN;

CREATE TABLE IF NOT EXISTS agentcore.<table_name> (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  uuid NOT NULL REFERENCES agentcore.projects(id) ON DELETE RESTRICT,
    -- ... columns ...
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_<table>_project ON agentcore.<table_name>(project_id);

-- Grants
GRANT SELECT ON agentcore.<table_name> TO agentcore_read, agentcore_worker, agentcore_backup;
GRANT INSERT, UPDATE ON agentcore.<table_name> TO agentcore_worker, agentcore_admin;
GRANT ALL ON agentcore.<table_name> TO agentcore_admin;

-- Evidence record (idempotent)
INSERT INTO agentcore.schema_migrations (version, description, blueprint_level)
VALUES ('<milestone>.NNN', '<description>', '<Milestone>')
ON CONFLICT (version) DO NOTHING;

COMMIT;
```

## DOWN Migration Template

```sql
-- <milestone> NNN DOWN - rollback
BEGIN;

DROP TABLE IF EXISTS agentcore.<table_name> CASCADE;
DELETE FROM agentcore.schema_migrations WHERE version = '<milestone>.NNN';

COMMIT;
```

## Applying with psql

```powershell
$pass = $env:AGENT_CORE_POSTGRES_PASSWORD
$psql = "F:\PostgreSQL18\bin\psql.exe"
& $psql "host=127.0.0.1 port=55433 dbname=agent_core user=postgres password=$pass" `
    -v ON_ERROR_STOP=1 `
    -f "migrations\<milestone>\NNN_up_<description>.sql"
```

## Rules

- Every migration has a corresponding DOWN migration.
- UP migrations are `BEGIN/COMMIT` wrapped.
- `ON CONFLICT DO NOTHING` on the schema_migrations INSERT ensures idempotency.
- Never ALTER a column type that contains data without a verified backup.
- Destructive operations (DROP, TRUNCATE, ALTER with data loss) require operator approval.
- Test UP + DOWN in a disposable database before applying to `agent_core`.

## Disposable Test Database Pattern

```powershell
$ts = Get-Date -Format "yyyyMMddHHmmss"
$testDb = "agentcore_m6_rollback_$ts"
# Apply migrations to test DB, verify, then drop
& $psql "... user=postgres ..." -c "CREATE DATABASE $testDb"
& $psql "host=... dbname=$testDb ..." -f "migrations/m6/001_up_langgraph_workflow.sql"
# Verify
& $psql "host=... dbname=$testDb ..." -f "migrations/m6/001_down_langgraph_workflow.sql"
& $psql "... user=postgres ..." -c "DROP DATABASE $testDb"
```
