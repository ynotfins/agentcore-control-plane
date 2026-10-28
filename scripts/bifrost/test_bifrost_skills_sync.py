from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "ops" / "bifrost" / "Sync-AgentCoreBifrostSkillsRepository.ps1"
PUBLICATION_CONTRACT = REPO_ROOT / "contracts" / "bifrost-skills-publication.json"
PUBLICATION_SCHEMA = REPO_ROOT / "contracts" / "schemas" / "bifrost-skills-publication.schema.json"

TEST_PUBLICATION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["schema_version", "skills"],
    "additionalProperties": False,
    "properties": {
        "schema_version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
        "skills": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "name",
                    "source_root",
                    "source_path",
                    "version",
                    "source_sha256",
                    "license",
                    "review",
                    "compatibility",
                    "served_state",
                    "hash_policy",
                    "status",
                    "publication_allowed",
                ],
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"},
                    "source_root": {"enum": ["repository_skills", "user_skills"]},
                    "source_path": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"},
                    "version": {
                        "type": "string",
                        "pattern": r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$",
                    },
                    "source_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "license": {
                        "type": "object",
                        "required": ["status", "spdx_id"],
                        "additionalProperties": False,
                        "properties": {
                            "status": {"enum": ["reviewed", "pending"]},
                            "spdx_id": {"type": ["string", "null"]},
                        },
                    },
                    "review": {
                        "type": "object",
                        "required": ["status", "authority"],
                        "additionalProperties": False,
                        "properties": {
                            "status": {"enum": ["approved", "pending"]},
                            "authority": {"type": ["string", "null"]},
                        },
                    },
                    "compatibility": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string", "minLength": 1},
                    },
                    "served_state": {"enum": ["enabled", "planned"]},
                    "hash_policy": {
                        "type": "object",
                        "required": ["algorithm", "scope"],
                        "additionalProperties": False,
                        "properties": {
                            "algorithm": {"const": "sha256"},
                            "scope": {"const": "published_files"},
                        },
                    },
                    "status": {"enum": ["approved", "planned"]},
                    "publication_allowed": {"type": "boolean"},
                },
            },
        },
    },
}


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _skill_record(
    name: str,
    *,
    status: str = "approved",
    source_root: str = "repository_skills",
    version: str = "1.0.0",
) -> dict:
    approved = status == "approved"
    return {
        "name": name,
        "source_root": source_root,
        "source_path": name,
        "version": version,
        "source_sha256": "0" * 64,
        "license": {"status": "reviewed" if approved else "pending", "spdx_id": "MIT" if approved else None},
        "review": {
            "status": "approved" if approved else "pending",
            "authority": "AUTH-2026-09-05-UNIVERSAL-IDE-BIFROST-SKILLS-ALIGNMENT" if approved else None,
        },
        "compatibility": ["Codex", "Claude Code"],
        "served_state": "enabled" if approved else "planned",
        "hash_policy": {"algorithm": "sha256", "scope": "published_files"},
        "status": status,
        "publication_allowed": approved,
    }


def _write_publication_files(tmp_path: Path, records: list[dict]) -> tuple[Path, Path]:
    contract_path = _write_json(
        tmp_path / "bifrost-skills-publication.json",
        {"schema_version": "1.0.0", "skills": records},
    )
    schema_path = _write_json(tmp_path / "bifrost-skills-publication.schema.json", TEST_PUBLICATION_SCHEMA)
    return contract_path, schema_path


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


def _run_sync(
    tmp_path: Path,
    skill_root: Path,
    list_payload: dict,
    *args: str,
    publication_contract_path: Path | None = None,
    publication_schema_path: Path | None = None,
) -> tuple[dict, list[dict], subprocess.CompletedProcess[str]]:
    list_path = _write_json(tmp_path / "skills-list.json", list_payload)
    write_log_path = tmp_path / "write-log.json"
    command = [
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
    ]
    if publication_contract_path is not None:
        command.extend(["-PublicationContractPath", str(publication_contract_path)])
    if publication_schema_path is not None:
        command.extend(["-PublicationSchemaPath", str(publication_schema_path)])
    command.extend(args)
    result = subprocess.run(
        command,
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


def test_source_hash_mismatch_fails_before_writes(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "agentcore-project-lifecycle")
    contract_path, schema_path = _write_publication_files(
        tmp_path, [_skill_record("agentcore-project-lifecycle")]
    )

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {"skills": [], "total": 0},
        "-IncludeSkill",
        "agentcore-project-lifecycle",
        "-EnforceSourceHashInTestMode",
        publication_contract_path=contract_path,
        publication_schema_path=schema_path,
    )

    assert result.returncode == 1
    assert calls == []
    assert summary["errors"] == [
        {"skill": "agentcore-project-lifecycle", "error": "skill_source_hash_mismatch"}
    ]


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
        {
            "skills": [
                {"id": "skill-langfuse", "name": "langfuse", "latest_version": "0.9.0"}
            ],
            "total": 1,
        },
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


def test_update_existing_skips_exact_current_version_without_put(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "langfuse")
    contract_path, schema_path = _write_publication_files(
        tmp_path, [_skill_record("langfuse", version="1.0.1")]
    )

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {
            "skills": [
                {"id": "skill-langfuse", "name": "langfuse", "latest_version": "1.0.1"}
            ],
            "total": 1,
        },
        "-Apply",
        "-UpdateExisting",
        publication_contract_path=contract_path,
        publication_schema_path=schema_path,
    )

    assert result.returncode == 0, result.stderr
    assert summary["skipped_existing"] == ["langfuse"]
    assert summary["updated"] == []
    assert calls == []


def test_update_existing_upgrades_older_version(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "langfuse")
    contract_path, schema_path = _write_publication_files(
        tmp_path, [_skill_record("langfuse", version="1.0.1")]
    )

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {
            "skills": [
                {"id": "skill-langfuse", "name": "langfuse", "latest_version": "1.0.0"}
            ],
            "total": 1,
        },
        "-Apply",
        "-UpdateExisting",
        publication_contract_path=contract_path,
        publication_schema_path=schema_path,
    )

    assert result.returncode == 0, result.stderr
    assert summary["updated"] == ["langfuse"]
    assert [(call["method"], call["name"]) for call in calls] == [("PUT", "langfuse")]


def test_update_existing_refuses_version_downgrade(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "langfuse")
    contract_path, schema_path = _write_publication_files(
        tmp_path, [_skill_record("langfuse", version="1.0.1")]
    )

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {
            "skills": [
                {"id": "skill-langfuse", "name": "langfuse", "latest_version": "1.1.0"}
            ],
            "total": 1,
        },
        "-Apply",
        "-UpdateExisting",
        publication_contract_path=contract_path,
        publication_schema_path=schema_path,
    )

    assert result.returncode == 1
    assert summary["errors"] == [
        {"skill": "langfuse", "error": "skill_version_downgrade_denied"}
    ]
    assert summary["updated"] == []
    assert calls == []


def test_update_existing_compares_core_version_before_prerelease(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "langfuse")
    contract_path, schema_path = _write_publication_files(
        tmp_path, [_skill_record("langfuse", version="1.9.9")]
    )

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {
            "skills": [
                {"id": "skill-langfuse", "name": "langfuse", "latest_version": "2.0.0-1"}
            ],
            "total": 1,
        },
        "-Apply",
        "-UpdateExisting",
        publication_contract_path=contract_path,
        publication_schema_path=schema_path,
    )

    assert result.returncode == 1
    assert summary["errors"] == [
        {"skill": "langfuse", "error": "skill_version_downgrade_denied"}
    ]
    assert calls == []


@pytest.mark.parametrize(
    ("existing_version", "expected_error"),
    [
        ("1.0", "existing_skill_version_invalid"),
        ("1.0.0-01", "existing_skill_version_invalid"),
        (None, "existing_skill_version_invalid"),
    ],
)
def test_update_existing_rejects_malformed_or_missing_existing_version(
    tmp_path: Path, existing_version: str | None, expected_error: str
) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "langfuse")
    contract_path, schema_path = _write_publication_files(
        tmp_path, [_skill_record("langfuse", version="1.0.1")]
    )
    existing = {"id": "skill-langfuse", "name": "langfuse"}
    if existing_version is not None:
        existing["latest_version"] = existing_version

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {"skills": [existing], "total": 1},
        "-Apply",
        "-UpdateExisting",
        publication_contract_path=contract_path,
        publication_schema_path=schema_path,
    )

    assert result.returncode == 1
    assert summary["errors"] == [{"skill": "langfuse", "error": expected_error}]
    assert calls == []


def test_update_existing_rejects_semantically_invalid_desired_version(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "langfuse")
    contract_path, schema_path = _write_publication_files(
        tmp_path, [_skill_record("langfuse", version="1.0.0-01")]
    )

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {
            "skills": [
                {"id": "skill-langfuse", "name": "langfuse", "latest_version": "1.0.0"}
            ],
            "total": 1,
        },
        "-Apply",
        "-UpdateExisting",
        publication_contract_path=contract_path,
        publication_schema_path=schema_path,
    )

    assert result.returncode == 1
    assert summary["errors"] == [
        {"skill": "langfuse", "error": "desired_skill_version_invalid"}
    ]
    assert calls == []


def test_update_existing_mixed_batch_writes_only_missing_and_older_versions(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    for name in ("agentcore-project-lifecycle", "langfuse", "nia"):
        _write_skill(skill_root, name)
    contract_path, schema_path = _write_publication_files(
        tmp_path,
        [
            _skill_record("agentcore-project-lifecycle", version="1.0.0"),
            _skill_record("langfuse", version="1.0.1"),
            _skill_record("nia", version="1.0.0"),
        ],
    )

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {
            "skills": [
                {
                    "id": "skill-lifecycle",
                    "name": "agentcore-project-lifecycle",
                    "latest_version": "1.0.0",
                },
                {"id": "skill-langfuse", "name": "langfuse", "latest_version": "1.0.0"},
            ],
            "total": 2,
        },
        "-Apply",
        "-UpdateExisting",
        publication_contract_path=contract_path,
        publication_schema_path=schema_path,
    )

    assert result.returncode == 0, result.stderr
    assert summary["skipped_existing"] == ["agentcore-project-lifecycle"]
    assert summary["updated"] == ["langfuse"]
    assert summary["created"] == ["nia"]
    assert [(call["method"], call["name"]) for call in calls] == [
        ("PUT", "langfuse"),
        ("POST", "nia"),
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


def test_repository_publication_contract_is_schema_valid() -> None:
    schema = json.loads(PUBLICATION_SCHEMA.read_text(encoding="utf-8"))
    contract = json.loads(PUBLICATION_CONTRACT.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)

    by_name = {record["name"]: record for record in contract["skills"]}
    assert set(by_name) == {
        "agentcore-project-lifecycle",
        "langfuse",
        "nia",
        "agentcore-tool-discovery",
        "morph-source-workflows",
        "zoo-roo-code-workflows",
    }
    assert {
        name for name, record in by_name.items() if record["status"] == "approved" and record["publication_allowed"]
    } == set(by_name)

    expected_versions = {
        "agentcore-tool-discovery": "1.0.1",
        "morph-source-workflows": "1.0.0",
        "zoo-roo-code-workflows": "1.0.0",
    }
    for name, expected_version in expected_versions.items():
        record = by_name[name]
        assert record["version"] == expected_version
        assert record["license"] == {
            "status": "reviewed",
            "spdx_id": "LicenseRef-AgentCore-Internal",
        }
        assert record["review"] == {
            "status": "approved",
            "authority": "AUTH-2026-09-05-UNIVERSAL-IDE-BIFROST-SKILLS-ALIGNMENT",
        }
        assert record["served_state"] == "enabled"


def test_missing_publication_contract_fails_before_writes(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "agentcore-project-lifecycle")
    _, schema_path = _write_publication_files(tmp_path, [_skill_record("agentcore-project-lifecycle")])

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {"skills": [], "total": 0},
        publication_contract_path=tmp_path / "missing-contract.json",
        publication_schema_path=schema_path,
    )

    assert result.returncode == 1
    assert calls == []
    assert summary["errors"] == [{"skill": None, "error": "publication_contract_missing"}]


@pytest.mark.parametrize(
    "contract_text",
    [
        "{not-json",
        json.dumps({"schema_version": "1.0.0", "skills": [{"name": "incomplete"}]}),
    ],
    ids=["malformed-json", "schema-invalid"],
)
def test_invalid_publication_contract_fails_before_writes(tmp_path: Path, contract_text: str) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "agentcore-project-lifecycle")
    _, schema_path = _write_publication_files(tmp_path, [_skill_record("agentcore-project-lifecycle")])
    contract_path = tmp_path / "invalid-contract.json"
    contract_path.write_text(contract_text, encoding="utf-8")

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {"skills": [], "total": 0},
        publication_contract_path=contract_path,
        publication_schema_path=schema_path,
    )

    assert result.returncode == 1
    assert calls == []
    assert summary["errors"] == [{"skill": None, "error": "publication_contract_invalid"}]


@pytest.mark.parametrize("missing_field", ["license", "review", "hash_policy"])
def test_publication_contract_requires_governance_fields(tmp_path: Path, missing_field: str) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "agentcore-project-lifecycle")
    record = _skill_record("agentcore-project-lifecycle")
    del record[missing_field]
    contract_path, schema_path = _write_publication_files(tmp_path, [record])

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {"skills": [], "total": 0},
        publication_contract_path=contract_path,
        publication_schema_path=schema_path,
    )

    assert result.returncode == 1
    assert calls == []
    assert summary["errors"] == [{"skill": None, "error": "publication_contract_invalid"}]


def test_planned_skill_is_not_approved_for_sync(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    _write_skill(skill_root, "future-planned-skill")
    contract_path, schema_path = _write_publication_files(
        tmp_path,
        [_skill_record("future-planned-skill", status="planned")],
    )

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {"skills": [], "total": 0},
        "-IncludeSkill",
        "future-planned-skill",
        publication_contract_path=contract_path,
        publication_schema_path=schema_path,
    )

    assert result.returncode == 1
    assert calls == []
    assert summary["errors"] == [
        {"skill": "future-planned-skill", "error": "skill_not_approved_for_sync"}
    ]
    assert summary["scanned"] == []


def test_default_enumeration_syncs_only_approved_publishable_skills(tmp_path: Path) -> None:
    skill_root = tmp_path / "skills"
    approved = [
        "agentcore-project-lifecycle",
        "agentcore-tool-discovery",
        "langfuse",
        "morph-source-workflows",
        "nia",
        "zoo-roo-code-workflows",
    ]
    planned = ["future-planned-skill"]
    for name in approved + planned:
        _write_skill(skill_root, name)
    contract_path, schema_path = _write_publication_files(
        tmp_path,
        [_skill_record(name) for name in approved] + [_skill_record(name, status="planned") for name in planned],
    )

    summary, calls, result = _run_sync(
        tmp_path,
        skill_root,
        {"skills": [], "total": 0},
        publication_contract_path=contract_path,
        publication_schema_path=schema_path,
    )

    assert result.returncode == 0, result.stderr
    assert summary["approved_skills"] == sorted(approved)
    assert [item["name"] for item in summary["scanned"]] == sorted(approved)
    assert summary["would_create"] == sorted(approved)
    assert calls == []
