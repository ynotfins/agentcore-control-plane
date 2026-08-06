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


def resolve_target(raw: str) -> Path:
    userprofile = os.environ.get("USERPROFILE")
    if not userprofile:
        raise RuntimeError("USERPROFILE is not set")
    return Path(raw.replace("{userprofile}", userprofile))


def approved_target(host: str, raw: str) -> Path:
    expected_raw = APPROVED_TARGETS.get(host)
    if expected_raw is None or raw != expected_raw:
        raise RuntimeError(f"unapproved target manifest entry for {host}: {raw}")
    target = resolve_target(raw).resolve(strict=False)
    expected = resolve_target(expected_raw).resolve(strict=False)
    if target != expected or target.name != "agentcore-project-lifecycle":
        raise RuntimeError(f"unsafe target for {host}: {target}")
    return target


def remove_exact_skill_dir(path: Path, expected: Path) -> None:
    resolved = path.resolve(strict=False)
    if resolved != expected.resolve(strict=False) or resolved.name != "agentcore-project-lifecycle":
        raise RuntimeError(f"refusing recursive removal outside exact skill leaf: {resolved}")
    if path.exists():
        shutil.rmtree(path)


def backup_and_replace(
    source: Path,
    target: Path,
    backup_run: Path,
    host: str,
    source_hash: str,
) -> None:
    token = uuid.uuid4().hex
    staging = target.parent / f".{target.name}.staging-{token}"
    prior = target.parent / f".{target.name}.prior-{token}"
    backup = backup_run / host
    had_prior = target.exists()

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, staging)
    if tree_digest(staging) != source_hash:
        remove_exact_staging(staging, target.parent, ".staging-")
        raise RuntimeError(f"staged skill digest mismatch for {host}")

    if target.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(target, backup)
        if tree_digest(backup) != tree_digest(target):
            remove_exact_staging(staging, target.parent, ".staging-")
            raise RuntimeError(f"rollback backup digest mismatch for {host}")

    try:
        if had_prior:
            os.replace(target, prior)
        os.replace(staging, target)
        if tree_digest(target) != source_hash:
            raise RuntimeError(f"installed skill digest mismatch for {host}")
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


def remove_exact_staging(path: Path, parent: Path, marker: str) -> None:
    resolved = path.resolve(strict=False)
    resolved_parent = parent.resolve(strict=False)
    if resolved.parent != resolved_parent or not resolved.name.startswith(
        f".agentcore-project-lifecycle{marker}"
    ):
        raise RuntimeError(f"refusing staging cleanup outside approved parent: {resolved}")
    if path.exists():
        shutil.rmtree(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="install hash-matched copies")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    manifest = load_manifest()
    source = REPO_ROOT / manifest["source"]
    source_hash = tree_digest(source)
    if source_hash == "missing":
        raise RuntimeError(f"canonical skill missing: {source}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_run = BACKUP_ROOT / stamp
    results: list[dict] = []

    for entry in manifest["hosts"]:
        delivery = entry["delivery"]
        result = {
            "host": entry["host"],
            "delivery": delivery,
            "validation": entry["validation"],
        }
        if delivery in INSTALLABLE:
            target = approved_target(entry["host"], entry["target"])
            before = tree_digest(target)
            result.update({"target": str(target), "before_sha256": before})
            if args.apply and before != source_hash:
                backup_and_replace(source, target, backup_run, entry["host"], source_hash)
            after = tree_digest(target)
            result.update(
                {
                    "after_sha256": after,
                    "status": "installed_unverified" if after == source_hash else "drift",
                }
            )
        elif delivery == "alias_of_minimax":
            target = approved_target(entry["host"], entry["target"])
            minimax = next(h for h in manifest["hosts"] if h["host"] == "minimax")
            minimax_target = approved_target(
                minimax["host"], minimax["target"]
            )
            try:
                same_root = target.resolve() == minimax_target.resolve()
            except OSError:
                same_root = False
            result.update(
                {
                    "target": str(target),
                    "status": "same_data_root_no_second_copy" if same_root else "alias_unverified",
                }
            )
        else:
            result["source"] = entry["source"]
            result["status"] = entry["validation"]
        results.append(result)

    payload = {
        "ok": all(r["status"] != "drift" for r in results) if args.apply else True,
        "mode": "apply" if args.apply else "check",
        "source": str(source),
        "source_sha256": source_hash,
        "backup_root": str(backup_run) if args.apply and backup_run.exists() else None,
        "hosts": results,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"mode={payload['mode']} source_sha256={source_hash}")
        for result in results:
            print(f"{result['host']}: {result['status']} ({result['delivery']})")
        if payload["backup_root"]:
            print(f"backup_root={payload['backup_root']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
