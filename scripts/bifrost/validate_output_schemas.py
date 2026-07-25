#!/usr/bin/env python3
"""Validate MCP outputSchema coverage for the agentcore-gateway tool surface.

Gates (all deterministic and offline unless --probe-gateway is passed):

  1. contract      contracts/mcp-tool-output-schemas.json validates against its schema,
                   references a real envelope schema, and every profile family exists.
  2. coverage      every registry server resolves to an output-schema binding; every
                   server that is enabled AND reachable through a capability profile
                   resolves to an adapter that actually produces outputSchema.
                   -> MissingOutputSchema
  3. emitted       every advertised outputSchema is a valid Draft 2020-12 schema, stays
                   under the contract byte ceiling, and actually validates the envelopes
                   the normalizer produces (schema/handler agreement, MCP 2025-06-18).
  4. wiring        the registry output_schema_adapter block points at files that exist.
  5. rendered      renderers/bifrost/config.sanitized.json stdio launches match what the
                   renderer produces today (detects a stale generated artifact after a
                   contract or registry change).  Skip with --skip-rendered.
  6. gateway       optional live proof: MCP initialize + tools/list against the running
                   gateway, counting tools whose definition has no outputSchema.
                   Requires BIFROST_MCP_VIRTUAL_KEY in the environment.

Exit code 0 only when MissingOutputSchema == 0 and no gate reported an error.

Run:
  python scripts/bifrost/validate_output_schemas.py
  python scripts/bifrost/validate_output_schemas.py --probe-gateway
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mcp_output_schema as mos  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
CONTRACT = REPO_ROOT / "contracts" / "mcp-tool-output-schemas.json"
CONTRACT_SCHEMA = REPO_ROOT / "contracts" / "schemas" / "mcp-tool-output-schemas.schema.json"
GATEWAY_CLIENT = REPO_ROOT / "contracts" / "agentcore-gateway-client.json"
# The sanitized sidecar is the artifact render_bifrost_config.py owns end to end.
# renderers/bifrost/config.json has historically drifted from renderer output
# (extra providers, CRLF), so it is only a fallback for the drift comparison.
RENDERED_SANITIZED = REPO_ROOT / "renderers" / "bifrost" / "config.sanitized.json"
RENDERED_CONFIG = REPO_ROOT / "renderers" / "bifrost" / "config.json"

SCHEMA_PRODUCING_ADAPTERS = {"stdio_envelope", "upstream_native"}
STDIO_TRANSPORTS = {"stdio", "router"}
MCP_PROTOCOL_VERSION = "2025-06-18"


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------- offline gates


def gate_contract(errors: list[str]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    from jsonschema import Draft202012Validator

    for path in (CONTRACT, CONTRACT_SCHEMA):
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(REPO_ROOT)}")
            return None

    contract = load(CONTRACT)
    schema = load(CONTRACT_SCHEMA)
    for err in sorted(Draft202012Validator(schema).iter_errors(contract), key=lambda e: list(e.path)):
        location = ".".join(str(p) for p in err.path) or "<root>"
        errors.append(f"output-schema-contract: {location}: {err.message}")

    envelope_rel = str(contract.get("envelope_schema_path") or "").replace("\\", "/")
    envelope_path = REPO_ROOT / envelope_rel
    if not envelope_path.exists():
        errors.append(f"output-schema-contract: envelope_schema_path not found: {envelope_rel}")
        return None
    envelope = load(envelope_path)

    try:
        Draft202012Validator.check_schema(envelope)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"envelope: source schema is not valid Draft 2020-12: {exc}")

    declared = str(contract.get("envelope_version") or "")
    actual = str(envelope.get("envelope_version") or "")
    if declared != actual:
        errors.append(
            f"envelope: version drift (contract={declared!r} schema={actual!r}) — "
            "bump both together"
        )

    families = set(mos.family_names(envelope))
    for profile_id, profile in (contract.get("profiles") or {}).items():
        family = profile.get("family")
        if family not in families:
            errors.append(
                f"output-schema-contract: profiles.{profile_id}.family {family!r} "
                f"is not defined under $defs.family_data"
            )
    return contract, envelope


def gate_coverage(
    contract: dict[str, Any],
    registry: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    servers = registry.get("servers") or {}
    bindings = contract.get("servers") or {}
    profiles = contract.get("profiles") or {}

    exposed: set[str] = set()
    for profile in (registry.get("capability_profiles") or {}).values():
        exposed.update(profile.get("allowed_server_ids") or [])

    missing_servers: list[str] = []
    missing_tools: list[str] = []
    covered_tools = 0

    for server_id, server in sorted(servers.items()):
        binding = bindings.get(server_id)
        if binding is None:
            errors.append(
                f"coverage: registry server {server_id!r} has no entry in "
                "contracts/mcp-tool-output-schemas.json"
            )
            missing_servers.append(server_id)
            continue

        profile_id = binding.get("default_profile")
        if profile_id not in profiles:
            errors.append(
                f"coverage: {server_id}.default_profile {profile_id!r} is not a declared profile"
            )
        for tool_name, override in (binding.get("tool_profiles") or {}).items():
            if override not in profiles:
                errors.append(
                    f"coverage: {server_id}.tool_profiles.{tool_name} -> {override!r} "
                    "is not a declared profile"
                )

        adapter = binding.get("adapter")
        is_enabled = bool(server.get("enabled"))
        is_exposed = server_id in exposed
        transport = server.get("connection_type")

        if adapter == "stdio_envelope" and transport not in STDIO_TRANSPORTS:
            errors.append(
                f"coverage: {server_id} is adapter=stdio_envelope but connection_type="
                f"{transport!r}; a stdio normalizer cannot wrap it"
            )

        if is_enabled and is_exposed:
            if adapter not in SCHEMA_PRODUCING_ADAPTERS:
                errors.append(
                    f"MissingOutputSchema: {server_id} is enabled and reachable through a "
                    f"capability profile but adapter={adapter!r} produces no outputSchema"
                )
                missing_servers.append(server_id)
        elif adapter not in SCHEMA_PRODUCING_ADAPTERS:
            warnings.append(
                f"coverage: {server_id} adapter={adapter!r} (not exposed; "
                f"enabled={is_enabled} in_profile={is_exposed}) — "
                f"{binding.get('reason') or 'no reason recorded'}"
            )

        # Tool-granular accounting is only possible where the registry pins an
        # explicit allowlist. Wildcard servers are counted at server granularity
        # offline and proven tool-by-tool by --probe-gateway.
        permitted = server.get("permitted_tools") or []
        if permitted and permitted != ["*"]:
            for tool_name in permitted:
                if adapter in SCHEMA_PRODUCING_ADAPTERS:
                    covered_tools += 1
                elif is_enabled and is_exposed:
                    missing_tools.append(f"{server_id}-{tool_name}")
            unknown = [t for t in (binding.get("tool_profiles") or {}) if t not in permitted]
            if unknown:
                errors.append(
                    f"coverage: {server_id}.tool_profiles references tools outside "
                    f"permitted_tools: {sorted(unknown)}"
                )

    return {
        "exposed_servers": sorted(exposed),
        "missing_servers": sorted(set(missing_servers)),
        "missing_tools": sorted(set(missing_tools)),
        "covered_named_tools": covered_tools,
    }


def gate_emitted(
    contract: dict[str, Any],
    envelope: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    from jsonschema import Draft202012Validator

    resolver = mos.OutputSchemaResolver(contract=contract, envelope_src=envelope)
    ceiling = int((contract.get("defaults") or {}).get("max_output_schema_bytes") or 4096)
    sizes: dict[str, int] = {}

    for family in mos.family_names(envelope):
        built = resolver.schema_for_family(family)
        try:
            Draft202012Validator.check_schema(built)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"emitted: family {family!r} produced an invalid schema: {exc}")
            continue
        size = len(json.dumps(built, separators=(",", ":")))
        sizes[family] = size
        if size > ceiling:
            errors.append(
                f"emitted: family {family!r} outputSchema is {size}B > "
                f"max_output_schema_bytes {ceiling}B (keep tools/list compact)"
            )
        if built.get("type") != "object":
            errors.append(f"emitted: family {family!r} root type must be object")
        required = set(built.get("required") or [])
        if required != set(mos.ENVELOPE_KEYS):
            errors.append(
                f"emitted: family {family!r} required keys drifted from the envelope contract"
            )
        if "$defs" in built or "$ref" in json.dumps(built):
            errors.append(
                f"emitted: family {family!r} still contains $ref/$defs; MCP clients "
                "receive each tool definition in isolation and cannot resolve them"
            )

    for failure in mos.self_test(resolver):
        errors.append(f"emitted: {failure}")

    return {"schema_bytes": sizes}


def gate_wiring(registry: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    block = registry.get("output_schema_adapter")
    if not block:
        errors.append(
            "MissingOutputSchema: registry has no output_schema_adapter block; no upstream "
            "would advertise outputSchema"
        )
        return
    if not block.get("enabled"):
        warnings.append(
            "wiring: output_schema_adapter.enabled=false (rollback posture) — "
            "rendered config will not advertise outputSchema"
        )
    for key in ("script", "contract"):
        rel = str(block.get(key) or "").replace("\\", "/")
        if not rel:
            errors.append(f"wiring: output_schema_adapter.{key} is empty")
            continue
        if not (REPO_ROOT / rel).exists():
            errors.append(f"wiring: output_schema_adapter.{key} not found in repo: {rel}")
    interpreter = str(block.get("interpreter") or "")
    if not interpreter:
        errors.append("wiring: output_schema_adapter.interpreter is empty")
    elif not Path(interpreter).exists():
        warnings.append(
            f"wiring: interpreter not present on this host ({interpreter}); "
            "verify on the Bifrost host before restarting the gateway"
        )


def gate_rendered(registry: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    target = RENDERED_SANITIZED if RENDERED_SANITIZED.exists() else RENDERED_CONFIG
    if not target.exists():
        warnings.append("rendered: no renderers/bifrost artifact present; nothing to compare")
        return
    label = target.relative_to(REPO_ROOT).as_posix()
    import render_bifrost_config as rbc

    wiring = rbc.OutputSchemaWiring(registry)
    expected = {
        client["name"]: client
        for client in rbc.build_mcp_client_configs(registry, None, wiring)
        if client.get("connection_type") == "stdio"
    }
    rendered = {
        client.get("name"): client
        for client in (load(target).get("mcp") or {}).get("client_configs", [])
        if isinstance(client, dict) and client.get("connection_type") == "stdio"
    }
    for name, want in expected.items():
        have = rendered.get(name)
        if have is None:
            errors.append(f"rendered: stdio client {name!r} missing from {label}")
            continue
        want_stdio = want.get("stdio_config") or {}
        have_stdio = have.get("stdio_config") or {}
        if want_stdio.get("command") != have_stdio.get("command") or list(
            want_stdio.get("args") or []
        ) != list(have_stdio.get("args") or []):
            errors.append(
                f"rendered: stdio launch for {name!r} in {label} does not match the renderer "
                "— re-run `python scripts/bifrost/render_bifrost_config.py`, then restart Bifrost"
            )


# --------------------------------------------------------------------- live probe


def _mcp_post(
    url: str, payload: dict[str, Any], headers: dict[str, str]
) -> tuple[Any, dict[str, str]]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    for key, value in headers.items():
        request.add_header(key, value)
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - localhost gateway
        raw = response.read().decode("utf-8", errors="replace")
        response_headers = {k.lower(): v for k, v in response.headers.items()}
    content_type = response_headers.get("content-type", "")
    if "text/event-stream" in content_type:
        for line in raw.splitlines():
            if line.startswith("data:"):
                chunk = line[5:].strip()
                if chunk:
                    try:
                        return json.loads(chunk), response_headers
                    except ValueError:
                        continue
        return None, response_headers
    if not raw.strip():
        return None, response_headers
    return json.loads(raw), response_headers


def gate_gateway(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    gateway = load(GATEWAY_CLIENT)
    url = str(gateway.get("url") or "http://127.0.0.1:8080/mcp")
    env_name = ((gateway.get("auth") or {}).get("env_var_name")) or "BIFROST_MCP_VIRTUAL_KEY"
    virtual_key = os.environ.get(env_name)
    if not virtual_key:
        warnings.append(
            f"gateway: {env_name} not present in this process env; live probe skipped"
        )
        return {"probed": False}

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        "Authorization": f"Bearer {virtual_key}",
    }
    try:
        init, response_headers = _mcp_post(
            url,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "agentcore-output-schema-validator", "version": "1.0.0"},
                },
            },
            headers,
        )
        session_id = response_headers.get("mcp-session-id")
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        if not isinstance(init, dict) or "result" not in init:
            errors.append(f"gateway: initialize failed against {url}")
            return {"probed": True, "ok": False}
        _mcp_post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, headers)
        listing, _ = _mcp_post(
            url, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, headers
        )
    except (urllib.error.URLError, OSError, ValueError) as exc:
        warnings.append(f"gateway: live probe unavailable ({exc.__class__.__name__}: {exc})")
        return {"probed": False}

    tools = ((listing or {}).get("result") or {}).get("tools") or []
    missing = [
        t.get("name", "<unnamed>")
        for t in tools
        if isinstance(t, dict) and not isinstance(t.get("outputSchema"), dict)
    ]
    if missing:
        errors.append(
            f"MissingOutputSchema: {len(missing)} live tool(s) advertise no outputSchema "
            f"(first 10: {missing[:10]})"
        )
    return {
        "probed": True,
        "ok": not missing,
        "tool_count": len(tools),
        "missing": missing,
    }


# ------------------------------------------------------------------------- driver


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-rendered", action="store_true", help="Skip the generated-artifact drift gate.")
    parser.add_argument("--probe-gateway", action="store_true", help="Also run the live tools/list proof.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable summary.")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    summary: dict[str, Any] = {}

    loaded = gate_contract(errors)
    if loaded is None:
        print("FAILED (contract gate)")
        for item in errors:
            print(f"  - {item}")
        return 1
    contract, envelope = loaded

    registry = load(REGISTRY)
    summary["coverage"] = gate_coverage(contract, registry, errors, warnings)
    summary["emitted"] = gate_emitted(contract, envelope, errors)
    gate_wiring(registry, errors, warnings)
    if not args.skip_rendered:
        gate_rendered(registry, errors, warnings)
    if args.probe_gateway:
        summary["gateway"] = gate_gateway(errors, warnings)

    missing_output_schema = len(
        [e for e in errors if e.startswith("MissingOutputSchema")]
    )
    summary["missing_output_schema_findings"] = missing_output_schema
    summary["errors"] = errors
    summary["warnings"] = warnings

    if args.json:
        print(json.dumps(summary, indent=2))
        return 1 if errors else 0

    for item in warnings:
        print(f"NOTICE: {item}")
    if errors:
        print(f"FAILED ({len(errors)} errors, MissingOutputSchema findings={missing_output_schema})")
        for item in errors:
            print(f"  - {item}")
        return 1

    coverage = summary["coverage"]
    sizes = summary["emitted"]["schema_bytes"]
    print("OK: output-schema contract + envelope valid")
    print(
        f"OK: coverage — {len(coverage['exposed_servers'])} profile-exposed server(s), "
        f"{coverage['covered_named_tools']} named tool(s) bound, MissingOutputSchema=0"
    )
    print(
        f"OK: emitted schemas — {len(sizes)} families, "
        f"max {max(sizes.values()) if sizes else 0}B (ceiling "
        f"{(contract.get('defaults') or {}).get('max_output_schema_bytes')}B)"
    )
    if args.probe_gateway and summary.get("gateway", {}).get("probed"):
        print(
            f"OK: live gateway tools/list — {summary['gateway']['tool_count']} tool(s), "
            "0 missing outputSchema"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
