# {{ project_name }}

MCP stdio server generated from `templates/mcp-server-python`.

**Server identity:** `{{ server_id }}`  
**Authority:** AgentCore Engineering Constitution §6

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Run

```powershell
python -m {{ project_slug }}.server
```

## Test

```powershell
pytest tests/ -v
```

## Lint and Type Check

```powershell
ruff check {{ project_slug }}/ tests/
ruff format --check {{ project_slug }}/ tests/
mypy {{ project_slug }}/
```

## Register in Bifrost

Add to `contracts/bifrost-upstream-mcp-registry.json`:

```json
{
  "id": "{{ server_id }}",
  "command": "python",
  "args": ["-m", "{{ project_slug }}.server"],
  "permitted_tools": ["{{ server_id | replace('-', '_') }}_status"]
}
```

## Update Template

```powershell
copier update
```

## Architecture

See `docs/engineering/CONSTITUTION.md` §6 and recipe `03-mcp-stdio-server.md`.

## Rollback

Restore previous version from Git: `git checkout <sha> -- {{ project_slug }}/`
