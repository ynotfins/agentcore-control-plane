#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { runGuardedDocumentationEdit, runGuardedEdit } from "./edit-worker.mjs";
import { assertSafeOutboundText } from "./secret-safety.mjs";
import { assertProviderModel, buildWorkerSystemPrompt } from "./worker-prompts.mjs";

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

const MODELS = Object.freeze({
  pro: {
    id: "deepseek/deepseek-v4-pro",
    label: "DeepSeek V4 Pro",
    defaultPurpose: "complex reasoning, architecture, difficult debugging, and rigorous critique",
    defaultMaxTokens: 7000
  },
  minimax: {
    id: "minimax/minimax-m3",
    label: "MiniMax M3",
    requestedAlias: "deepseek/MiniMax-M3",
    defaultPurpose: "long-context coding synthesis and sustained agentic implementation work",
    defaultMaxTokens: 4000
  },
  flash: {
    id: "~deepseek/deepseek-v4-flash-latest",
    label: "DeepSeek V4 Flash Latest",
    defaultPurpose: "rapid repository scouting, triage, and concise first-pass coding analysis",
    defaultMaxTokens: 1800
  }
});

const WORKER_SYSTEM = `
You are a low-cost worker called by Codex. Codex is the orchestrator.

Rules:
- Do the assigned bounded job only.
- Do not claim you edited files or ran tools.
- Prefer file paths, line references, concrete evidence, and concise conclusions.
- If asked to draft code, provide a lazy edit or patch plan; do not invent unverified surrounding code.
- Separate facts from assumptions.
- Return output that Codex can review quickly.
`.trim();

const CRITIQUE_SYSTEM = `
You are the dedicated critique worker for Codex. Codex owns the master plan, implementation authority, and final decision.

Review only the supplied plan, diff, code, logs, or test evidence. Do not draft an implementation unless Codex explicitly asks for a correction sketch.

Return:
1. Findings ordered by severity, with concrete evidence.
2. Missing tests or verification gaps.
3. Assumptions and uncertainty.
4. A final verdict: BLOCK, REVISE, or ACCEPT.

Never claim you edited files, ran commands, or verified evidence you were not given.
`.trim();

const DOCUMENTATION_GUARD_SYSTEM = `
You are the documentation guard for Codex. Codex owns the operator goal, architecture authority, and final decision.

Compare only the supplied proposed documentation change against the supplied authority chain, current milestone, code/test evidence, and locked decisions. Detect stale facts, contradictions, missing evidence, unauthorized scope changes, and weakened safeguards.

Return:
1. Drift findings ordered by severity with exact evidence.
2. Required corrections and missing validation.
3. A final verdict: BLOCK, REVISE, or ACCEPT.

You are read-only. Do not author replacement architecture, edit files, or treat your own output as authority.
`.trim();

const workerSchema = {
  task: z.string().min(1).describe("The bounded job for the worker."),
  context: z.string().optional().describe("Relevant context, snippets, logs, paths, or prior findings."),
  role: z.string().optional().describe("Optional worker role, such as scout, reviewer, patch drafter, or test analyst."),
  max_tokens: z.number().int().min(128).max(12000).optional().describe("Maximum output tokens. Model defaults: Flash 1800, MiniMax 4000, Pro 7000."),
  temperature: z.number().min(0).max(1).optional().describe("Sampling temperature. Defaults to 0.2.")
};

const routeSchema = {
  task: workerSchema.task,
  context: workerSchema.context,
  priority: z.enum(["fast", "balanced", "hard"]).optional().describe("fast=flash, balanced=MiniMax M3, hard=DeepSeek Pro."),
  role: workerSchema.role,
  max_tokens: workerSchema.max_tokens,
  temperature: workerSchema.temperature
};

const editWorkerSchema = {
  workspace_root: z.string().min(1).describe("Absolute root directory that contains the target file."),
  path: z.string().min(1).describe("Absolute path to one existing text file beneath workspace_root."),
  instruction: z.string().min(1).describe("The bounded implementation change Codex wants made in this file."),
  context: z.string().optional().describe("Relevant plan details, constraints, or acceptance criteria from Codex."),
  dry_run: z.boolean().optional().describe("When true, return the proposed diff without writing. Defaults to false."),
  max_tokens: z.number().int().min(256).max(16000).optional().describe("Maximum editor-model output tokens. Defaults to 8000."),
  temperature: z.number().min(0).max(1).optional().describe("Editor-model temperature. Defaults to 0.1.")
};

const documentationEditSchema = {
  ...editWorkerSchema,
  approval_reference: z.string().optional().describe("Authority approval identifier required for protected documentation, for example AUTH-2026-08-06-DOCUMENTATION_GUARD.")
};

function selectModel(priority = "balanced") {
  if (priority === "fast") return MODELS.flash;
  if (priority === "hard") return MODELS.pro;
  return MODELS.minimax;
}

function formatUserMessage({ task, context, role }) {
  const lines = [];
  if (role) lines.push(`Worker role: ${role}`);
  lines.push(`Task:\n${task}`);
  if (context) lines.push(`Context:\n${context}`);
  return lines.join("\n\n");
}

async function callOpenRouter(model, args, systemPrompt = WORKER_SYSTEM, mode = "read-only") {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error("OPENROUTER_API_KEY is not set in the environment.");
  }
  assertSafeOutboundText([args.task, args.context, args.role]);

  const response = await fetch(OPENROUTER_URL, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      "HTTP-Referer": "https://codex.local/cheap-workers",
      "X-Title": "Codex Cheap Workers MCP"
    },
    body: JSON.stringify({
      model: model.id,
      messages: [
        {
          role: "system",
          content: buildWorkerSystemPrompt({ model, mode, basePrompt: systemPrompt })
        },
        { role: "user", content: formatUserMessage(args) }
      ],
      temperature: args.temperature ?? 0.2,
      max_tokens: args.max_tokens ?? model.defaultMaxTokens
    })
  });

  const text = await response.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    throw new Error(`OpenRouter returned non-JSON HTTP ${response.status}: ${text.slice(0, 500)}`);
  }

  if (!response.ok) {
    const message = json?.error?.message || JSON.stringify(json).slice(0, 500);
    throw new Error(`OpenRouter HTTP ${response.status}: ${message}`);
  }

  const content = json?.choices?.[0]?.message?.content;
  if (!content) {
    if (json?.choices?.[0]?.finish_reason === "length" && json?.choices?.[0]?.message?.reasoning) {
      throw new Error(`OpenRouter exhausted max_tokens in reasoning for ${model.id}; retry with a larger max_tokens budget.`);
    }
    throw new Error(`OpenRouter response did not include message content: ${JSON.stringify(json).slice(0, 500)}`);
  }

  const providerModel = assertProviderModel(model, json.model);

  return {
    model: model.id,
    providerModel,
    label: model.label,
    content,
    usage: json.usage ?? null
  };
}

function resultText(result) {
  const usage = result.usage ? `\n\nUsage: ${JSON.stringify(result.usage)}` : "";
  return `Model route: ${result.label} (${result.model})\nProvider response model: ${result.providerModel}\n\n${result.content}${usage}`;
}

const server = new McpServer({
  name: "codex-cheap-workers",
  version: "0.4.0"
});

function registerWorkerTool(name, description, model, systemPrompt = WORKER_SYSTEM, mode = "read-only") {
  server.tool(name, description, workerSchema, async (args) => {
    const result = await callOpenRouter(model, args, systemPrompt, mode);
    return {
      content: [{ type: "text", text: resultText(result) }]
    };
  });
}

function registerEditWorkerTool(name, description, model) {
  server.tool(name, description, editWorkerSchema, async (args) => {
    const result = await runGuardedEdit({
      workspaceRoot: args.workspace_root,
      targetPath: args.path,
      instruction: args.instruction,
      context: args.context,
      model,
      dryRun: args.dry_run ?? false,
      maxTokens: args.max_tokens,
      temperature: args.temperature
    });
    const usage = result.usage ? `\nUsage: ${JSON.stringify(result.usage)}` : "";
    const backup = result.backupPath ? `\nBackup: ${result.backupPath}` : "";
    const diff = result.diff ? `\n\nDiff:\n${result.diff}` : "\n\nNo file changes were produced.";
    return {
      content: [{
        type: "text",
        text: `Model route: ${model.label} (${model.id})\nProvider response model: ${result.providerModel}\nChanged: ${result.changed}\nWritten: ${result.written}${backup}${usage}${diff}`
      }]
    };
  });
}

registerWorkerTool(
  "deepseek_pro_worker",
  "Delegate a bounded hard reasoning, planning, or review job to DeepSeek V4 Pro through OpenRouter. Read-only worker.",
  MODELS.pro
);

registerWorkerTool(
  "documentation_guard_worker",
  "DOCUMENTATION GUARD. Independently compare a proposed documentation change with the supplied authority and evidence, detect drift, and return BLOCK, REVISE, or ACCEPT. Read-only.",
  MODELS.pro,
  DOCUMENTATION_GUARD_SYSTEM,
  "critique"
);

server.tool(
  "documentation_maintainer_edit_worker",
  "DOCUMENTATION MAINTAINER. The only cheap-worker write path for documentation. It edits one existing documentation file, internally submits the actual proposed diff to the independent guard, blocks non-ACCEPT verdicts and generated projections, requires live authority approval for protected files, uses crash-safe replacement, and returns the exact diff for Codex review.",
  documentationEditSchema,
  async (args) => {
    const result = await runGuardedDocumentationEdit({
      workspaceRoot: args.workspace_root,
      targetPath: args.path,
      instruction: args.instruction,
      context: args.context,
      approvalReference: args.approval_reference,
      model: MODELS.pro,
      dryRun: args.dry_run ?? true,
      maxTokens: args.max_tokens,
      temperature: args.temperature
    });
    const usage = result.usage ? `\nUsage: ${JSON.stringify(result.usage)}` : "";
    const backup = result.backupPath ? `\nBackup: ${result.backupPath}` : "";
    const diff = result.diff ? `\n\nDiff:\n${result.diff}` : "\n\nNo file changes were produced.";
    return {
      content: [{
        type: "text",
        text: `Role: documentation maintainer\nModel route: ${MODELS.pro.label} (${MODELS.pro.id})\nProvider response model: ${result.providerModel}\nChanged: ${result.changed}\nWritten: ${result.written}${backup}${usage}${diff}`
      }]
    };
  }
);

registerWorkerTool(
  "minimax_m3_worker",
  "Delegate a bounded broad drafting or long-context synthesis job to MiniMax M3 through OpenRouter. Read-only worker.",
  MODELS.minimax
);

registerWorkerTool(
  "deepseek_flash_worker",
  "Delegate a bounded fast scouting, summarization, or triage job to DeepSeek V4 Flash Latest through OpenRouter. Read-only worker.",
  MODELS.flash
);

registerEditWorkerTool(
  "minimax_m3_edit_worker",
  "EDIT WORKER. After Codex creates the master plan, delegate one bounded existing-file implementation change to MiniMax M3 through OpenRouter. Morph Fast Apply merges the lazy edit, a backup is created before writes, and the exact diff is returned to Codex for review.",
  MODELS.minimax
);

registerEditWorkerTool(
  "deepseek_pro_edit_worker",
  "EDIT WORKER. After Codex creates the master plan, delegate one difficult bounded existing-file implementation change to DeepSeek V4 Pro through OpenRouter. Morph Fast Apply merges the lazy edit, a backup is created before writes, and the exact diff is returned to Codex for review.",
  MODELS.pro
);

registerWorkerTool(
  "deepseek_pro_critique_worker",
  "CRITIQUE WORKER. Give Codex an independent findings-first review of a plan, proposed change, diff, or test evidence using DeepSeek V4 Pro through OpenRouter. Read-only and returns a BLOCK, REVISE, or ACCEPT verdict.",
  MODELS.pro,
  CRITIQUE_SYSTEM,
  "critique"
);

server.tool(
  "cheap_worker_route",
  "Route a bounded worker job to one of the configured cheaper models: fast=Flash, balanced=MiniMax M3, hard=DeepSeek Pro. Read-only worker.",
  routeSchema,
  async (args) => {
    const model = selectModel(args.priority);
    const result = await callOpenRouter(model, args);
    return {
      content: [{ type: "text", text: resultText(result) }]
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
