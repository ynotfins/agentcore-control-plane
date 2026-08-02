"""AgentCore M6 — optional Langfuse tracing and prompt management.

Operator opt-in only. Langfuse exports workflow/deep-agent telemetry when
``AGENTCORE_LANGFUSE_TRACING=true`` and Langfuse API credentials are present
in Windows User-scope environment variables (never ``.env`` files).

Prompt management is similarly gated by ``AGENTCORE_LANGFUSE_PROMPTS=true``.
When disabled or unreachable, embedded fallback templates are used so worker
behavior is unchanged.

Authority: docs/operations/LANGFUSE_TRACING_AND_PROMPTS.md
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

# ─────────────────────────────────────────────────────────────────────────────
# Prompt names (Langfuse project)
# ─────────────────────────────────────────────────────────────────────────────

PROMPT_BUILDER = "agentcore-da-builder"
PROMPT_CRITIC = "agentcore-da-critic"
PROMPT_LABEL = "production"

BUILDER_CONTEXT_MAX_CHARS = 4000
CRITIC_CONTEXT_MAX_CHARS = 2000

BUILDER_PROMPT_TEMPLATE = """You are a focused builder agent. You have been delegated ONE micro-step.
Work only within your assigned worktree: {{worktree}}

## AgentCore Project Context (read-only; do not modify this context)
{{agentcore_context}}

## Your task
{{task}}

## Strict rules
- Work ONLY within the assigned worktree above.
- Do NOT read or write files outside that path.
- Do NOT call any network API, send emails, push to git, or deploy.
- Do NOT output credentials, secrets, or environment variable values.
- Do NOT install new packages or modify lock files.
- Do NOT create AGENTS.md, .env, or conversation_history archives.
- Write clear, testable code. Run tests if they exist.
- Stop after completing the task; do not over-engineer.
- Your output will be captured by the AgentCore platform; do not create
  separate memory files or AGENTS.md files.
"""

CRITIC_PROMPT_TEMPLATE = """You are a focused code reviewer. You may only READ files.
Assigned worktree: {{worktree}}

## AgentCore Project Context
{{agentcore_context}}

## Review task
{{task}}{{rubric_section}}

## Strict rules
- Read ONLY. You may NOT write, edit, delete, or execute anything.
- Produce a structured critique with: PASSED (yes/no), SCORE (0.0-1.0),
  and FINDINGS (list of specific issues or confirmations).
- Format your final response as JSON:
  {{"passed": true/false, "score": 0.0-1.0, "findings": ["..."]}}
"""

PROMPT_DEFINITIONS: dict[str, dict[str, Any]] = {
    PROMPT_BUILDER: {
        "type": "text",
        "prompt": BUILDER_PROMPT_TEMPLATE,
        "labels": [PROMPT_LABEL],
    },
    PROMPT_CRITIC: {
        "type": "text",
        "prompt": CRITIC_PROMPT_TEMPLATE,
        "labels": [PROMPT_LABEL],
    },
}


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def normalize_langfuse_env() -> None:
    """Align LANGFUSE_HOST and LANGFUSE_BASE_URL without printing secrets."""
    base = os.environ.get("LANGFUSE_BASE_URL", "").strip()
    host = os.environ.get("LANGFUSE_HOST", "").strip()
    if base and not host:
        os.environ["LANGFUSE_HOST"] = base
    elif host and not base:
        os.environ["LANGFUSE_BASE_URL"] = host


def has_langfuse_credentials() -> bool:
    normalize_langfuse_env()
    return bool(
        os.environ.get("LANGFUSE_PUBLIC_KEY", "").strip()
        and os.environ.get("LANGFUSE_SECRET_KEY", "").strip()
        and (
            os.environ.get("LANGFUSE_BASE_URL", "").strip()
            or os.environ.get("LANGFUSE_HOST", "").strip()
        )
    )


def is_tracing_enabled() -> bool:
    return _truthy("AGENTCORE_LANGFUSE_TRACING") and has_langfuse_credentials()


def is_prompt_management_enabled() -> bool:
    return _truthy("AGENTCORE_LANGFUSE_PROMPTS") and has_langfuse_credentials()


def _import_langfuse():
    from langfuse import get_client

    return get_client()


def get_callback_handler():
    """Return a Langfuse LangChain CallbackHandler, or None when tracing is off."""
    if not is_tracing_enabled():
        return None
    try:
        from langfuse.langchain import CallbackHandler

        _import_langfuse()
        return CallbackHandler()
    except Exception:
        return None


def merge_invoke_config(
    base: dict[str, Any] | None = None,
    *,
    handler: Any | None = None,
) -> dict[str, Any]:
    """Merge Langfuse callbacks into a LangGraph/LangChain invoke config."""
    config: dict[str, Any] = dict(base or {})
    if handler is None:
        handler = get_callback_handler()
    if handler is not None:
        existing = list(config.get("callbacks") or [])
        if handler not in existing:
            existing.append(handler)
        config["callbacks"] = existing
    return config


@contextmanager
def workflow_trace_context(
    *,
    project_id: str,
    project_key: str,
    thread_uuid: str,
    milestone_key: str,
) -> Iterator[Any | None]:
    """Optional outer span + attribute propagation for a workflow run."""
    if not is_tracing_enabled():
        yield None
        return

    try:
        from langfuse import get_client, propagate_attributes

        langfuse = get_client()
        tags = ["agentcore", "m6-workflow", milestone_key]
        with langfuse.start_as_current_observation(
            as_type="span",
            name="agentcore-workflow-run",
        ) as span:
            span.update(
                input={
                    "project_key": project_key,
                    "milestone_key": milestone_key,
                    "thread_uuid": thread_uuid,
                }
            )
            with propagate_attributes(
                session_id=thread_uuid,
                user_id=project_id,
                tags=tags,
            ):
                yield span
    except Exception:
        yield None


@contextmanager
def worker_prompt_context(prompt_obj: Any | None) -> Iterator[None]:
    """Link a Langfuse prompt object to nested generations when supported."""
    if prompt_obj is None or not is_tracing_enabled():
        yield
        return
    try:
        from langfuse import propagate_attributes

        with propagate_attributes(prompt=prompt_obj):
            yield
    except Exception:
        yield


def _compile_fallback(template: str, **variables: str) -> str:
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    # Unescape remaining Jinja-style braces left for literal JSON examples.
    return rendered.replace("{{", "{").replace("}}", "}")


def _fetch_and_compile_prompt(name: str, **variables: str) -> tuple[str, Any | None]:
    if not is_prompt_management_enabled():
        definition = PROMPT_DEFINITIONS.get(name, {})
        template = definition.get("prompt", "")
        return _compile_fallback(template, **variables), None

    try:
        langfuse = _import_langfuse()
        prompt = langfuse.get_prompt(name, label=PROMPT_LABEL)
        compiled = prompt.compile(**variables)
        return compiled, prompt
    except Exception:
        definition = PROMPT_DEFINITIONS.get(name, {})
        template = definition.get("prompt", "")
        return _compile_fallback(template, **variables), None


def compile_builder_system_prompt(
    *,
    worktree: str,
    agentcore_context: str,
    task: str,
) -> tuple[str, Any | None]:
    context = agentcore_context[:BUILDER_CONTEXT_MAX_CHARS]
    return _fetch_and_compile_prompt(
        PROMPT_BUILDER,
        worktree=str(worktree),
        agentcore_context=context,
        task=task,
    )


def compile_critic_system_prompt(
    *,
    worktree: str,
    agentcore_context: str,
    task: str,
    rubric: str = "",
) -> tuple[str, Any | None]:
    context = agentcore_context[:CRITIC_CONTEXT_MAX_CHARS]
    rubric_section = f"\n## Rubric\n{rubric}" if rubric else ""
    return _fetch_and_compile_prompt(
        PROMPT_CRITIC,
        worktree=str(worktree),
        agentcore_context=context,
        task=task,
        rubric_section=rubric_section,
    )


def bootstrap_prompts(*, dry_run: bool = False) -> dict[str, str]:
    """Create or version AgentCore prompts in Langfuse (operator script)."""
    if not has_langfuse_credentials():
        raise RuntimeError(
            "Langfuse credentials missing. Set LANGFUSE_PUBLIC_KEY, "
            "LANGFUSE_SECRET_KEY, and LANGFUSE_BASE_URL in Windows User env."
        )

    langfuse = _import_langfuse()
    results: dict[str, str] = {}
    for name, spec in PROMPT_DEFINITIONS.items():
        if dry_run:
            results[name] = "dry-run"
            continue
        langfuse.create_prompt(
            name=name,
            type=spec["type"],
            prompt=spec["prompt"],
            labels=spec.get("labels", [PROMPT_LABEL]),
        )
        results[name] = "created"
    return results


def flush_langfuse() -> None:
    if not is_tracing_enabled():
        return
    try:
        _import_langfuse().flush()
    except Exception:
        pass


def shutdown_langfuse() -> None:
    if not is_tracing_enabled():
        return
    try:
        _import_langfuse().shutdown()
    except Exception:
        pass
