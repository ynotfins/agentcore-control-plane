from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "ops" / "bifrost" / "Sync-AgentCoreBifrostSkillsRepository.ps1"


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_skill(root: Path, name: str, extra_files: dict[str, str | bytes] | None = None) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = "\n".join(
        [
            "---",
            f"name: {name}",
            f"description: {name} test skill",
            "---",
            "",
            f"# {name}",
            "",
            "Test skill body.",
            "",
        ]
    )
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    for relative, content in (extra_files or {}).items():
        target = skill_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
    return skill_dir


def _run_sync(tmp_path: Path, skill_root: Path, list_payload: dict, *args: str) -> tuple[dict, list[dict], subprocess.CompletedProcess[str]]:
    list_path = _write_json(tmp_path / "skills-list.json", list_payload)
    write_log_path = tmp_path / "write-log.json"
    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(SCRIPT),
            "-TestMode",
            "-SkillRoot",
            str(skill_root),
            "-AdditionalSkillRoot",
            "",
            "-TestListResponsePath",
            str(list_path),
            "-TestWriteLogPath",
            str(write_log_path),
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    summary = json.loads(result.stdout) if result.stdout.strip() else {}
    calls = json.loads(write_log_path.read_text(encoding="utf-8-sig")) if write_log_path.exists() and write_log_path.read_text(encoding="utf-8-sig").strip() else []
    if isinstance(calls, dict):
        calls = [calls]
    return summary, calls, result


def test_bifrost_skills_sync_script_exists_and_parses() -> None:
    assert SCRIPT.is_file()
    command = (
        "$errors=$null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{SCRIPT}', [ref]$null, [ref]$errors) | Out-Null; "
        "if ($errors.Count) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_dry_run_no_apply_creates_no_write_calls(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "agentcore-project-lifecycle")
    _write_skill(skill_root, "langfuse")

    summary, calls, result = _run_sync(tmp_path, skill_root, {"skills": [], "total": 0})

    assert result.returncode == 0, result.stderr
    assert summary["apply"] is False
    assert summary["would_create"] == ["agentcore-project-lifecycle", "langfuse"]
    assert summary["created"] == []
    assert calls == []


def test_apply_creates_missing_and_updates_existing_only_when_requested(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "agentcore-project-lifecycle")
    _write_skill(skill_root, "langfuse")

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {"skills": [{"id": "skill-langfuse", "name": "langfuse"}], "total": 1},
        "-Apply",
        "-UpdateExisting",
    )

    assert result.returncode == 0, result.stderr
    assert summary["created"] == ["agentcore-project-lifecycle"]
    assert summary["updated"] == ["langfuse"]
    assert [(call["method"], call["uri"], call["name"]) for call in calls] == [
        ("POST", "http://127.0.0.1:8080/api/skills", "agentcore-project-lifecycle"),
        ("PUT", "http://127.0.0.1:8080/api/skills/skill-langfuse", "langfuse"),
    ]


def test_supporting_files_exclude_secret_backup_large_binary_and_skill_md(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(
        skill_root,
        "agentcore-project-lifecycle",
        {
            "references/keep.md": "keep me",
            "references/data.json": '{"ok": true}',
            ".agentcore-skill-backups/old.md": "skip me",
            "node_modules/pkg/index.js": "skip me",
            "secret-token.txt": "token: this_should_not_leave_repository_123456",
            "large.txt": "x" * 70000,
            "binary.bin": b"\x00\x01\x02",
        },
    )

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {"skills": [], "total": 0},
        "-Apply",
        "-IncludeSkill",
        "agentcore-project-lifecycle",
    )

    assert result.returncode == 0, result.stderr
    assert summary["created"] == ["agentcore-project-lifecycle"]
    payload_files = calls[0]["payload"]["files"]
    assert payload_files == [
        {
            "path": "references/data.json",
            "source_type": "text",
            "content": '{"ok": true}',
            "mime_type": "application/json",
        },
        {
            "path": "references/keep.md",
            "source_type": "text",
            "content": "keep me",
            "mime_type": "text/plain",
        },
    ]


def test_secondary_skill_root_can_publish_user_global_nia_skill(tmp_path: Path) -> None:
    repo_skill_root = tmp_path / "repo-skills"
    user_skill_root = tmp_path / "user-skills"
    _write_skill(repo_skill_root, "agentcore-project-lifecycle")
    _write_skill(user_skill_root, "nia", {"README.md": "Nia skill docs"})

    list_path = _write_json(tmp_path / "skills-list.json", {"skills": [], "total": 0})
    write_log_path = tmp_path / "write-log.json"
    result = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(SCRIPT),
            "-TestMode",
            "-SkillRoot",
            str(repo_skill_root),
            "-AdditionalSkillRoot",
            str(user_skill_root),
            "-TestListResponsePath",
            str(list_path),
            "-TestWriteLogPath",
            str(write_log_path),
            "-Apply",
            "-IncludeSkill",
            "nia",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    summary = json.loads(result.stdout)
    calls = json.loads(write_log_path.read_text(encoding="utf-8-sig"))
    assert result.returncode == 0, result.stderr
    assert summary["created"] == ["nia"]
    assert summary["scanned"][0]["source_root"] == str(user_skill_root)
    assert calls[0]["name"] == "nia"
    assert calls[0]["payload"]["files"] == [
        {
            "path": "README.md",
            "source_type": "text",
            "content": "Nia skill docs",
            "mime_type": "text/plain",
        }
    ]


def test_duplicate_existing_skill_names_are_not_recreated_without_update(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "agentcore-project-lifecycle")

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {
            "skills": [
                {"id": "first", "name": "agentcore-project-lifecycle"},
                {"id": "second", "name": "agentcore-project-lifecycle"},
            ],
            "total": 2,
        },
        "-Apply",
        "-IncludeSkill",
        "agentcore-project-lifecycle",
    )

    assert result.returncode == 0, result.stderr
    assert summary["skipped_existing"] == ["agentcore-project-lifecycle"]
    assert summary["created"] == []
    assert summary["updated"] == []
    assert calls == []


def test_outgoing_payload_secret_scan_fails_without_printing_secret(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    fake_secret = "sk-proj-" + ("A" * 32)
    _write_skill(skill_root, "agentcore-project-lifecycle", {"references/keep.md": f"api_key={fake_secret}"})

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {"skills": [], "total": 0},
        "-Apply",
        "-IncludeSkill",
        "agentcore-project-lifecycle",
    )

    assert result.returncode == 1
    assert calls == []
    assert "SECRET_SCAN_FAILED" in summary["errors"][0]["error"]
    assert fake_secret not in result.stdout
    assert fake_secret not in result.stderr
