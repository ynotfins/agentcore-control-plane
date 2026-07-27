# Authority Lock — AgentCore Control Plane

This repository is the authority for AgentCore only.

`AUTHORITY_LOCK.md` and `contracts/authority-lock.yaml` define which files are operator-locked, governed mutable, generated read-only, or normal workstream files.

AgentCore may keep a minimal pointer to the Swarm ecosystem, but it must not own Swarm runtime facts, databases, services, credentials, prompts, backups, or lifecycle decisions.

Operator-locked files require an authority-maintainer capability, an explicit approval identifier, rollback evidence, validators, and independent review.

Generated projections are read-only to ordinary agents and may be written only by their authoritative generator.
