# Recipe 10 — Isolated Project and Worktree Execution

**Pattern:** Each project/feature gets an isolated Git worktree. Agents are scoped to their assigned worktree.  
**Stack:** Git 2.40+, PowerShell, Python.  
**Authority:** `docs/engineering/CONSTITUTION.md` §15, `CONTEXT_BLOCK.md` §11.

---

## Create a Feature Worktree

```powershell
# From the canonical repository
$feature = "feature/my-feature"
$worktreePath = "D:\github\agentcore-control-plane-$feature"

git worktree add $worktreePath -b $feature

# Verify
git worktree list
```

## Project Registration

```python
# Every repository gets a stable UUID in .agentcore/project.yaml
# This file identifies the project across worktrees and restarts

import yaml
from pathlib import Path
import uuid

def register_project(repo_root: Path) -> str:
    agentcore_dir = repo_root / ".agentcore"
    agentcore_dir.mkdir(exist_ok=True)
    project_file = agentcore_dir / "project.yaml"

    if project_file.exists():
        data = yaml.safe_load(project_file.read_text())
        return data["project_id"]

    project_id = str(uuid.uuid4())
    project_file.write_text(yaml.dump({
        "project_id": project_id,
        "repository": str(repo_root),
        "created_at": __import__("datetime").datetime.utcnow().isoformat(),
    }))
    return project_id
```

## Enforcing Write Boundaries

```python
from pathlib import Path

ALLOWED_WRITE_ROOT = Path(r"D:\github\agentcore-control-plane")

def safe_write(target: Path, content: str) -> None:
    """Refuse to write outside the assigned worktree."""
    try:
        target.resolve().relative_to(ALLOWED_WRITE_ROOT.resolve())
    except ValueError:
        raise PermissionError(
            f"Write to {target} rejected: outside assigned worktree {ALLOWED_WRITE_ROOT}"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
```

## Serena Scoped to Worktree

```python
# When using Serena for code navigation, always activate the project router
# with the current worktree path — not a global path.
# From AGENTS.md tool routing:
# agentcore_project_router-project_activate → Serena wrapper scoped to cwd
```

## Cleanup After Feature Work

```powershell
# Remove worktree when feature is merged
git worktree remove "D:\github\agentcore-control-plane-feature-my-feature"
git branch -d feature/my-feature
```

## Rules

- One canonical checkout at `D:\github\agentcore-control-plane` (main branch).
- Feature work in `D:\github\agentcore-control-plane-<branch>` worktrees.
- Never edit both the main checkout and a feature worktree simultaneously without intent.
- `project.yaml` is the stable identity anchor. Git remote URL is an alias, not the identity.
- Agents may read approved global knowledge but write only to their assigned worktree.
- Hard enforcement at the tool/process boundary: narrow Serena roots, isolated worktrees, protected DB paths.
