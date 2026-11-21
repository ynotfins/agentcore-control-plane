from pathlib import Path
import json
from datetime import datetime, timezone
REPO = Path("d:/github/agentcore-control-plane")
enr = REPO / "scripts" / "maf_recall" / "repo_enrollment_status.md"
text = """# Repo enrollment status (read-only note)

Avoid editing contracts/agentcore-project-enrollment.json from this package.

## Currently enrolled project_key values

- agentcore-control-plane
- agentcore-context-engine
- codebase-analyzer
- openhands
- nfa-alerts-database
- nfa-notification-collector
- odysseus

## Swarm roots must not be enrolled

Swarm ecosystem roots remain denylisted. Use agentcore-memory behind gateway only.

## Not enrolled yet

- nfa-platform
- Cloud Mia

Authority-maintainer change required to enroll those identities.
"""
enr.write_text(text, encoding="utf-8", newline="\n")
audit_path = REPO / "audits" / "MAF_RECALL_REALIGNMENT_AUDIT_2026-08-26.json"
audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
audit["updated_at"] = datetime.now(timezone.utc).isoformat()
audit.setdefault("evidence", []).append({
    "id": "maf_host_verify_followup",
    "import_ok": True,
    "version": "1.15.0",
    "venv": "scripts/maf_recall/maf_host/.venv",
    "port_8080_guard": "RuntimeError refuse bind confirmed",
})
audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print("PATCH_OK")