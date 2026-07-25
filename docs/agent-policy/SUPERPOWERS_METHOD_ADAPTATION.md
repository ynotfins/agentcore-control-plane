# Superpowers Method Adaptation — AgentCore Control Plane

**Policy Authority:** `PROJECT_ANCHOR.md` §0 / `BLUEPRINT.md` §7 / `contracts/global-agent-policy.yaml`  
**Provenance:** Adapted from Superpowers (MIT License, Copyright (c) Anthropic / Superpowers Contributors)  
**Status:** Active AgentCore-Owned Behaviors (No Superpowers plugin reactivated; zero extra active skills added)

---

## 1. Overview and Boundary Rules

AgentCore adapts core software engineering workflows from the Superpowers methodology directly into AgentCore-owned system behaviors, subagent roles, and hook gates.

- **Plugin Status:** The Superpowers plugin is **NOT** activated in Cursor.
- **Skill Surface:** Zero additional active skills are added to the Cursor skill catalog (`C:\Users\ynotf\.cursor\skills`).
- **Execution Authority:** Behaviors are executed natively by AgentCore gateway tools, subagent definitions, and hook dispatchers.

---

## 2. Adaptation Matrix

| Superpowers Method | AgentCore Adapted Behavior | Implementation Path |
|---|---|---|
| **brainstorming** | Thinker / Plan | Plan Mode + `sequential-thinking` via gateway |
| **systematic-debugging** | Debug / Worker | Systematic root-cause investigation before code changes |
| **test-driven-development** | Test Writer | `test-writer` custom agent + red-green-refactor workflow |
| **verification-before-completion** | Stop Review | 8-axis final review in AgentCore `stop` hook |
| **requesting/receiving-code-review** | Code Reviewer | `code-reviewer` custom agent (read-only subagent) |
| **using-git-worktrees** | Isolated Multiagent Writes | Worktree-isolated subagents for parallel / task isolation |

---

## 3. Detailed Method Specifications

### 3.1 Brainstorming → Thinker / Plan Mode
- **Behavior:** Explore architectural options, trade-offs, and failure modes before writing code.
- **AgentCore Mapping:** Activated during Plan Mode and multi-file architecture tasks using `sequential-thinking` through `agentcore-gateway`.

### 3.2 Systematic Debugging → Debug / Worker
- **Behavior:** Hypothesize root causes from logs/evidence, verify hypotheses with tests, apply minimal fix.
- **AgentCore Mapping:** Embedded into worker nodes and debugging workflows.

### 3.3 Test-Driven Development → Test Writer
- **Behavior:** Write high-value tests for branching, transactions, side effects, and edge cases before or alongside implementation.
- **AgentCore Mapping:** Executed by `test-writer` subagent definition (`.cursor/agents/test-writer.md`).

### 3.4 Verification Before Completion → Stop Review
- **Behavior:** Validate all acceptance criteria, run deterministic tests, and perform final review before closing a task.
- **AgentCore Mapping:** Executed deterministically by `handle_stop` in `scripts/agentcore_cursor/hooks.py` (8-axis review stored in `session-scope.json`).

### 3.5 Requesting/Receiving Code Review → Code Reviewer
- **Behavior:** Perform read-only code review checking security, correctness, minimality, wiring, and AgentCore rules.
- **AgentCore Mapping:** Executed by `code-reviewer` custom agent definition (`.cursor/agents/code-reviewer.md`).

### 3.6 Using Git Worktrees → Isolated Multiagent Writes
- **Behavior:** Isolate parallel workstreams and subagents into separate Git worktrees under `D:\github\`.
- **AgentCore Mapping:** Enforced by project router and `agentcore.project_worktrees` in PostgreSQL.

---

## 4. Provenance and License Notice

```text
Adapted from Superpowers skill collection.
Original license: MIT License
Copyright (c) Superpowers Contributors / Anthropic

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom it is furnished to do so.
```
