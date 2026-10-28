"""Install or verify the canonical AgentCore lifecycle skill on supported hosts.

The repository skill is the only source. Unsupported/manual hosts are reported,
not guessed. Applying creates timestamped rollback copies before replacement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "contracts" / "agentcore-alignment-skill-hosts.json"
PUBLICATION_CONTRACT = REPO_ROOT / "contracts" / "bifrost-skills-publication.json"
BACKUP_ROOT = Path(r"E:\AgentCore-Backups\agentcore-alignment-skill")
INSTALLABLE = {"native_skill", "native_skill_empirical"}
APPROVED_TARGETS = {
    "zed": r"{userprofile}\.agents\skills\agentcore-project-lifecycle",
    "eigent": r"{userprofile}\.eigent\skills\agentcore-project-lifecycle",
    "cursor": r"{userprofile}\.cursor\skills\agentcore-project-lifecycle",
    "codex": r"{userprofile}\.agents\skills\agentcore-project-lifecycle",
    "claude-code": r"{userprofile}\.claude\skills\agentcore-project-lifecycle",
    "minimax": r"{userprofile}\.minimax\skills\agentcore-project-lifecycle",
    "mavis": r"{userprofile}\.mavis\skills\agentcore-project-lifecycle",
}
DEFAULT_SKILL = "agentcore-project-lifecycle"


def _safe_leaf(name: str) -> None:
    if (
        not isinstance(name, str)
        or not name
        or name in (".", "..")
        or Path(name).is_absolute()
        or bool(Path(name).drive)
        or "/" in name
        or "\\" in name
    ):
        raise RuntimeError(f"unsafe skill name: {name!r}")


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    if not root.is_dir():
        return "missing"
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def load_publication() -> dict:
    return json.loads(PUBLICATION_CONTRACT.read_text(encoding="utf-8"))


def resolve_target(raw: str) -> Path:
    userprofile = os.environ.get("USERPROFILE")
    if not userprofile:
        raise RuntimeError("USERPROFILE is not set")
    return Path(raw.replace("{userprofile}", userprofile))


def approved_target(host: str, raw: str, skill_name: str = DEFAULT_SKILL) -> Path:
    expected_raw = APPROVED_TARGETS.get(host)
    if expected_raw is None or raw != expected_raw:
        raise RuntimeError(f"unapproved target manifest entry for {host}: {raw}")
    _safe_leaf(skill_name)
    expected = resolve_target(expected_raw)
    parent = expected.parent.resolve(strict=False)
    target = parent / skill_name
    if target.parent != parent or target.name != skill_name:
        raise RuntimeError(f"unsafe target for {host}: {target}")
    return target


def remove_exact_skill_dir(path: Path, expected: Path) -> None:
    resolved = path.resolve(strict=False)
    expected_resolved = expected.resolve(strict=False)
    if resolved != expected_resolved:
        raise RuntimeError(f"refusing recursive removal outside exact skill leaf: {resolved}")
    _safe_leaf(resolved.name)
    if path.exists():
        shutil.rmtree(path)


def remove_exact_staging(path: Path, parent: Path, marker: str) -> None:
    resolved = path.resolve(strict=False)
    resolved_parent = parent.resolve(strict=False)
    if marker not in {".staging-", ".prior-", ".failed-"} or resolved.parent != resolved_parent:
        raise RuntimeError(f"refusing staging cleanup outside approved parent: {resolved}")
    prefix, separator, token = resolved.name[1:].rpartition(marker)
    if not separator or not token:
        raise RuntimeError(f"refusing staging cleanup outside approved parent: {resolved}")
    _safe_leaf(prefix)
    if path.exists():
        shutil.rmtree(path)


def backup_and_replace(
    source: Path,
    target: Path,
    backup_run: Path,
    owner: str,
    source_hash: str,
) -> None:
    token = uuid.uuid4().hex
    staging = target.parent / f".{target.name}.staging-{token}"
    prior = target.parent / f".{target.name}.prior-{token}"
    backup = backup_run / owner / target.name
    had_prior = target.exists()

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, staging)
    if tree_digest(staging) != source_hash:
        remove_exact_staging(staging, target.parent, ".staging-")
        raise RuntimeError(f"staged skill digest mismatch for {owner}")

    if target.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(target, backup)
        if tree_digest(backup) != tree_digest(target):
            remove_exact_staging(staging, target.parent, ".staging-")
            raise RuntimeError(f"rollback backup digest mismatch for {owner}")

    try:
        if had_prior:
            os.replace(target, prior)
        os.replace(staging, target)
        if tree_digest(target) != source_hash:
            raise RuntimeError(f"installed skill digest mismatch for {owner}")
    except Exception as install_error:
        failed: Path | None = None
        if target.exists():
            failed = target.parent / f".{target.name}.failed-{token}"
            os.replace(target, failed)
        if prior.exists():
            os.replace(prior, target)
        if staging.exists():
            try:
                remove_exact_staging(staging, target.parent, ".staging-")
            except OSError:
                pass
        if failed is not None and failed.exists():
            try:
                remove_exact_staging(failed, target.parent, ".failed-")
            except OSError:
                pass
        raise install_error
    else:
        if prior.exists():
            remove_exact_staging(prior, target.parent, ".prior-")


def approved_publication_records(publication: dict) -> list[dict]:
    skills = publication.get("skills")
    if not isinstance(skills, list):
        raise RuntimeError("publication contract skills must be a list")
    names = [skill.get("name") for skill in skills]
    if len(names) != len(set(names)):
        raise RuntimeError("duplicate skill names in publication contract")
    records: list[dict] = []
    for skill in skills:
        if skill.get("status") != "approved":
            continue
        if skill.get("publication_allowed") is not True:
            continue
        name = skill.get("name")
        source_path = skill.get("source_path")
        _safe_leaf(name)
        _safe_leaf(source_path)
        if source_path != name:
            raise RuntimeError(f"source_path mismatch for {name}")
        records.append(skill)
    return records


def select_publication_records(
    publication: dict,
    requested_skills: list[str] | None = None,
    all_approved: bool = False,
) -> list[dict]:
    approved = approved_publication_records(publication)
    approved_map = {r["name"]: r for r in approved}
    if all_approved:
        return approved
    names = [DEFAULT_SKILL] if requested_skills is None else requested_skills
    seen: set[str] = set()
    result: list[dict] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        if name not in approved_map:
            all_names = {s["name"] for s in publication.get("skills", [])}
            if name in all_names:
                raise RuntimeError(f"skill {name!r} is not approved for publication")
            raise RuntimeError(f"unknown skill: {name!r}")
        result.append(approved_map[name])
    return result


def resolve_skill_source(record: dict) -> Path:
    source_root_name = record.get("source_root")
    name = record.get("name")
    source_path = record.get("source_path")
    _safe_leaf(name)
    _safe_leaf(source_path)
    if source_path != name:
        raise RuntimeError(f"source_path mismatch for {name}")
    if source_root_name == "repository_skills":
        root = REPO_ROOT / ".agents" / "skills"
    elif source_root_name == "user_skills":
        userprofile = os.environ.get("USERPROFILE")
        if not userprofile:
            raise RuntimeError("USERPROFILE is not set")
        root = Path(userprofile) / ".agents" / "skills"
    else:
        raise RuntimeError(f"unknown source_root: {source_root_name!r}")
    resolved_root = root.resolve(strict=False)
    resolved_source = (root / source_path).resolve(strict=False)
    if resolved_source != resolved_root / name or resolved_source.parent != resolved_root:
        raise RuntimeError(f"unsafe skill source: {resolved_source}")
    if not resolved_source.is_dir():
        raise RuntimeError(f"skill source missing: {resolved_source}")
    return resolved_source


def execute_installation(
    manifest: dict,
    selected_records: list[dict],
    apply: bool,
    backup_run: Path,
) -> dict:
    source_cache: dict[str, tuple[Path, str]] = {}
    skill_payloads = {
        record["name"]: {
            "name": record["name"],
            "source": None,
            "source_sha256": None,
            "hosts": [],
        }
        for record in selected_records
    }
    ops: dict[str, dict] = {}

    for record in selected_records:
        skill_name = record["name"]
        source = resolve_skill_source(record)
        source_hash = tree_digest(source)
        source_cache[skill_name] = (source, source_hash)
        skill_payloads[skill_name]["source"] = str(source)
        skill_payloads[skill_name]["source_sha256"] = source_hash
        for entry in manifest["hosts"]:
            if entry["delivery"] not in INSTALLABLE:
                continue
            target = approved_target(entry["host"], entry["target"], skill_name)
            key = os.path.normcase(str(target.resolve(strict=False)))
            existing = ops.get(key)
            if existing is not None:
                if (
                    existing["skill_name"] != skill_name
                    or existing["source"] != source
                    or existing["source_hash"] != source_hash
                ):
                    raise RuntimeError("conflicting skill target")
                existing["entries"].append(entry)
            else:
                ops[key] = {
                    "target": target,
                    "source": source,
                    "source_hash": source_hash,
                    "entries": [entry],
                    "skill_name": skill_name,
                }

    for op in ops.values():
        target = op["target"]
        source = op["source"]
        source_hash = op["source_hash"]
        entries = op["entries"]
        hosts = [entry["host"] for entry in entries]
        skill_name = op["skill_name"]
        canonical_source = source.resolve(strict=False)
        canonical_target = target.resolve(strict=False)
        before = tree_digest(target)
        if canonical_source == canonical_target:
            after = before
            status = "source_target_same"
        else:
            if apply and before != source_hash:
                owner = hosts[0] if len(hosts) == 1 else "shared-" + "--".join(sorted(hosts))
                backup_and_replace(source, target, backup_run, owner, source_hash)
            after = tree_digest(target)
            status = "installed_unverified" if after == source_hash else "drift"

        for entry in entries:
            skill_payloads[skill_name]["hosts"].append(
                {
                    "host": entry["host"],
                    "delivery": entry["delivery"],
                    "validation": entry["validation"],
                    "target": str(target),
                    "before_sha256": before,
                    "after_sha256": after,
                    "status": status,
                }
            )

    for record in selected_records:
        skill_name = record["name"]
        source, source_hash = source_cache[skill_name]
        for entry in manifest["hosts"]:
            delivery = entry["delivery"]
            if delivery in INSTALLABLE:
                continue
            result = {
                "host": entry["host"],
                "delivery": delivery,
                "validation": entry["validation"],
            }
            if delivery == "alias_of_minimax":
                target = approved_target(entry["host"], entry["target"], skill_name)
                minimax_entry = next(
                    (host for host in manifest["hosts"] if host["host"] == "minimax"),
                    None,
                )
                if minimax_entry is None:
                    result.update({"target": str(target), "status": "alias_unverified"})
                else:
                    minimax_target = approved_target(
                        minimax_entry["host"], minimax_entry["target"], skill_name
                    )
                    result.update(
                        {
                            "target": str(target),
                            "status": (
                                "same_data_root_no_second_copy"
                                if target == minimax_target
                                else "alias_unverified"
                            ),
                        }
                    )
            else:
                result.update(
                    {"source": entry.get("source"), "status": entry["validation"]}
                )
            skill_payloads[skill_name]["hosts"].append(result)

    return {"skills": list(skill_payloads.values())}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="install hash-matched copies")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all-approved", action="store_true", help="install all approved skills")
    group.add_argument("--skill", action="append", dest="skills", help="install named skill (repeatable)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    manifest = load_manifest()
    publication = load_publication()

    requested_skills: list[str] | None = None
    all_approved = False
    if args.all_approved:
        all_approved = True
    elif args.skills:
        requested_skills = args.skills

    selected = select_publication_records(publication, requested_skills, all_approved)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_run = BACKUP_ROOT / stamp

    exec_result = execute_installation(manifest, selected, args.apply, backup_run)

    # Legacy top-level source/source_sha256 for default lifecycle-only selection
    first_skill = exec_result["skills"][0] if exec_result["skills"] else None
    default_source = first_skill["source"] if first_skill else None
    default_source_sha256 = first_skill["source_sha256"] if first_skill else None

    # Collect hosts from skills payload for backward compatibility
    hosts_list: list[dict] = []
    for skill_entry in exec_result["skills"]:
        for h in skill_entry["hosts"]:
            hosts_list.append(h)

    any_drift = any(
        h.get("status") == "drift"
        for skill_entry in exec_result["skills"]
        for h in skill_entry["hosts"]
    )

    payload = {
        "ok": not any_drift if args.apply else True,
        "mode": "apply" if args.apply else "check",
        "source": default_source,
        "source_sha256": default_source_sha256,
        "backup_root": str(backup_run) if args.apply and backup_run.exists() else None,
        "hosts": hosts_list,
        "skills": exec_result["skills"],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"mode={payload['mode']} source_sha256={default_source_sha256}")
        for skill_entry in exec_result["skills"]:
            for h in skill_entry["hosts"]:
                print(f"{h['host']}: {h['status']} ({skill_entry['name']})")
        if payload["backup_root"]:
            print(f"backup_root={payload['backup_root']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
