import { createHash, randomUUID } from "node:crypto";
import { constants as fsConstants } from "node:fs";
import { copyFile, mkdir, open, readFile, realpath, rename, stat, unlink } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { createTwoFilesPatch } from "diff";
import { assertCodeWorkerTarget, assertDocumentationWorkerTarget } from "./documentation-policy.mjs";
import { assertSafeOutboundText } from "./secret-safety.mjs";
import { assertProviderModel, buildWorkerSystemPrompt } from "./worker-prompts.mjs";

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
const MORPH_URL = "https://api.morphllm.com/v1/chat/completions";
const DEFAULT_MAX_FILE_BYTES = 2 * 1024 * 1024;
const DOCUMENTATION_GUARD_MODEL = Object.freeze({
  id: "deepseek/deepseek-v4-pro",
  label: "DeepSeek V4 Pro",
  defaultPurpose: "independent documentation drift and authority review"
});
const inFlightEditPaths = new Set();

const EDIT_TOOL = {
  type: "function",
  function: {
    name: "edit_file",
    description: "Return a lazy edit containing only the changed sections of the supplied file.",
    parameters: {
      type: "object",
      properties: {
        instructions: {
          type: "string",
          description: "A brief first-person sentence describing the edit."
        },
        code_edit: {
          type: "string",
          description: "Only changed sections, with // ... existing code ... for unchanged regions."
        }
      },
      required: ["instructions", "code_edit"],
      additionalProperties: false
    }
  }
};

function hashText(value) {
  return createHash("sha256").update(value).digest("hex");
}

function nonEmptyString(value, name) {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${name} must be a non-empty string.`);
  }
  return value;
}

async function requestJson(url, apiKey, body, fetchImpl) {
  const response = await fetchImpl(url, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      "HTTP-Referer": "https://codex.local/cheap-workers",
      "X-Title": "Codex Cheap Edit Workers MCP"
    },
    body: JSON.stringify(body)
  });

  const text = await response.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    throw new Error(`API returned non-JSON HTTP ${response.status}: ${text.slice(0, 500)}`);
  }

  if (!response.ok) {
    const message = json?.error?.message || JSON.stringify(json).slice(0, 500);
    throw new Error(`API HTTP ${response.status}: ${message}`);
  }
  return json;
}

export function parseEditToolCall(response) {
  const toolCalls = response?.choices?.[0]?.message?.tool_calls;
  const editCall = Array.isArray(toolCalls)
    ? toolCalls.find((call) => call?.function?.name === "edit_file")
    : null;
  if (!editCall) {
    throw new Error("OpenRouter response did not include the forced edit_file tool call.");
  }

  let args;
  try {
    args = typeof editCall.function.arguments === "string"
      ? JSON.parse(editCall.function.arguments)
      : editCall.function.arguments;
  } catch {
    throw new Error("OpenRouter edit_file arguments were not valid JSON.");
  }

  return {
    instructions: nonEmptyString(args?.instructions, "edit_file.instructions"),
    codeEdit: nonEmptyString(args?.code_edit, "edit_file.code_edit")
  };
}

export async function generateLazyEdit({
  model,
  targetPath,
  instruction,
  originalCode,
  context,
  maxTokens = 8000,
  temperature = 0.1,
  workerMode = "edit",
  basePrompt,
  fetchImpl = fetch
}) {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error("OPENROUTER_API_KEY is not set in the environment.");
  }

  const contextBlock = context ? `\n\nAdditional context:\n${context}` : "";
  const response = await requestJson(OPENROUTER_URL, apiKey, {
    model: model.id,
    messages: [
      {
        role: "system",
        content: buildWorkerSystemPrompt({
          model,
          mode: workerMode,
          basePrompt: basePrompt ?? [
            "Make only the bounded change requested in the single supplied file.",
            "Call edit_file exactly once. Emit only changed sections and use // ... existing code ... for unchanged regions.",
            "Do not choose a path, claim to run tests, or make unrelated changes."
          ].join(" ")
        })
      },
      {
        role: "user",
        content: `Task:\n${instruction}${contextBlock}\n\nFile: ${targetPath}\n\n<code>\n${originalCode}\n</code>`
      }
    ],
    tools: [EDIT_TOOL],
    tool_choice: { type: "function", function: { name: "edit_file" } },
    temperature,
    max_tokens: maxTokens
  }, fetchImpl);

  return {
    ...parseEditToolCall(response),
    providerModel: assertProviderModel(model, response.model),
    usage: response.usage ?? null
  };
}

export async function mergeWithMorph({ instructions, originalCode, codeEdit, fetchImpl = fetch }) {
  const apiKey = process.env.MORPH_API_KEY;
  if (!apiKey) {
    throw new Error("MORPH_API_KEY is not set in the environment.");
  }

  const response = await requestJson(MORPH_URL, apiKey, {
    model: "morph-v3-fast",
    messages: [{
      role: "user",
      content: `<instruction>${instructions}</instruction>\n<code>${originalCode}</code>\n<update>${codeEdit}</update>`
    }]
  }, fetchImpl);

  return nonEmptyString(
    response?.choices?.[0]?.message?.content,
    "Morph merged content"
  );
}

export function parseDocumentationGuardVerdict(content) {
  const matches = [...content.matchAll(/(?:final\s+)?verdict\s*:\s*\*{0,2}(BLOCK|REVISE|ACCEPT)\b/gi)];
  if (!matches.length) {
    throw new Error("Documentation guard response did not include a final BLOCK, REVISE, or ACCEPT verdict.");
  }
  return matches.at(-1)[1].toUpperCase();
}

export async function reviewDocumentationChange({
  targetPath,
  instruction,
  context,
  approvalReference,
  diff,
  fetchImpl = fetch
}) {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error("OPENROUTER_API_KEY is not set in the environment.");
  }
  assertSafeOutboundText([targetPath, instruction, context, diff]);

  const response = await requestJson(OPENROUTER_URL, apiKey, {
    model: DOCUMENTATION_GUARD_MODEL.id,
    messages: [
      {
        role: "system",
        content: buildWorkerSystemPrompt({
          model: DOCUMENTATION_GUARD_MODEL,
          mode: "critique",
          basePrompt: [
            "You are the independent documentation guard.",
            "Review the actual proposed diff against the supplied operator intent, authority, evidence, and approval reference.",
            "Detect factual drift, authority inversion, unsupported completion claims, weakened safeguards, and generated-state edits.",
            "End with exactly Final Verdict: BLOCK, Final Verdict: REVISE, or Final Verdict: ACCEPT."
          ].join(" ")
        })
      },
      {
        role: "user",
        content: `Target: ${targetPath}\nApproval: ${approvalReference ?? "routine-documentation"}\nInstruction: ${instruction}\n\nAuthority and evidence:\n${context ?? "No additional context supplied."}\n\nProposed diff:\n${diff}`
      }
    ],
    temperature: 0,
    max_tokens: 5000
  }, fetchImpl);

  const content = nonEmptyString(response?.choices?.[0]?.message?.content, "Documentation guard content");
  return {
    verdict: parseDocumentationGuardVerdict(content),
    content,
    providerModel: assertProviderModel(DOCUMENTATION_GUARD_MODEL, response.model),
    usage: response.usage ?? null
  };
}

export async function atomicReplaceText(targetPath, content, dependencies = {}) {
  const openFile = dependencies.openFile ?? open;
  const renameFile = dependencies.renameFile ?? rename;
  const removeFile = dependencies.removeFile ?? unlink;
  const temporaryPath = path.join(
    path.dirname(targetPath),
    `.${path.basename(targetPath)}.codex-worker-${randomUUID()}.tmp`
  );
  let handle;
  let temporaryExists = false;

  try {
    handle = await openFile(temporaryPath, "wx");
    temporaryExists = true;
    await handle.writeFile(content, "utf8");
    await handle.sync();
    await handle.close();
    handle = undefined;
    await renameFile(temporaryPath, targetPath);
    temporaryExists = false;
  } finally {
    if (handle) {
      await handle.close().catch(() => {});
    }
    if (temporaryExists) {
      await removeFile(temporaryPath).catch((error) => {
        if (error?.code !== "ENOENT") throw error;
      });
    }
  }
}

async function resolveEditableFile(workspaceRoot, targetPath, maxFileBytes, targetPolicy) {
  if (!path.isAbsolute(workspaceRoot) || !path.isAbsolute(targetPath)) {
    throw new Error("workspace_root and path must both be absolute paths.");
  }

  const resolvedRoot = await realpath(workspaceRoot);
  const resolvedTarget = await realpath(targetPath);
  targetPolicy(resolvedTarget);
  const relative = path.relative(resolvedRoot, resolvedTarget);
  if (!relative || relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("Target path is outside the workspace root.");
  }

  const targetStat = await stat(resolvedTarget);
  if (!targetStat.isFile()) {
    throw new Error("Target path must identify an existing file.");
  }
  if (!Number.isInteger(maxFileBytes) || maxFileBytes < 1) {
    throw new Error("maxFileBytes must be a positive integer.");
  }
  if (targetStat.size > maxFileBytes) {
    throw new Error(`Target file exceeds the edit-worker size limit of ${maxFileBytes} bytes.`);
  }
  return { resolvedTarget, relative };
}

function normalizeMergedText(originalCode, mergedCode) {
  const hadBom = originalCode.startsWith("\uFEFF");
  let normalized = mergedCode.replace(/^\uFEFF/, "");
  if (originalCode.includes("\r\n")) {
    normalized = normalized.replace(/\r?\n/g, "\r\n");
  }
  return hadBom ? `\uFEFF${normalized}` : normalized;
}

async function createBackup(backupRoot, targetPath, relativePath, originalHash) {
  const safeName = relativePath.replace(/[\\/:*?"<>|]/g, "__");
  const backupPath = path.join(
    backupRoot,
    `${Date.now()}-${originalHash.slice(0, 12)}-${randomUUID()}-${safeName}.bak`
  );
  await mkdir(backupRoot, { recursive: true });
  await copyFile(targetPath, backupPath, fsConstants.COPYFILE_EXCL);
  return backupPath;
}

export async function runGuardedEdit({
  workspaceRoot,
  targetPath,
  instruction,
  context,
  model,
  dryRun = false,
  maxTokens,
  maxFileBytes,
  temperature,
  backupRoot = path.join(os.homedir(), ".codex", "backups", "cheap-workers", "edits"),
  dependencies = {}
}) {
  nonEmptyString(instruction, "instruction");
  if (!model?.id || !model?.label) {
    throw new Error("A fixed edit-worker model is required.");
  }

  const editable = await resolveEditableFile(
    workspaceRoot,
    targetPath,
    maxFileBytes ?? DEFAULT_MAX_FILE_BYTES,
    dependencies.targetPolicy ?? assertCodeWorkerTarget
  );
  const lockKey = process.platform === "win32"
    ? editable.resolvedTarget.toLowerCase()
    : editable.resolvedTarget;
  if (inFlightEditPaths.has(lockKey)) {
    throw new Error("Target file is already being edited by another worker.");
  }
  inFlightEditPaths.add(lockKey);

  try {
    const originalBuffer = await readFile(editable.resolvedTarget);
    if (originalBuffer.includes(0)) {
      throw new Error("Binary files are not supported by edit workers.");
    }
    const originalCode = originalBuffer.toString("utf8");
    const originalHash = hashText(originalCode);
    assertSafeOutboundText([instruction, context, originalCode]);

    const generateEdit = dependencies.generateEdit ?? generateLazyEdit;
    const mergeEdit = dependencies.mergeEdit ?? mergeWithMorph;
    const lazyEdit = await generateEdit({
      model,
      targetPath: editable.resolvedTarget,
      instruction,
      originalCode,
      context,
      maxTokens,
      temperature,
      workerMode: dependencies.workerMode,
      basePrompt: dependencies.basePrompt
    });
    assertSafeOutboundText([lazyEdit.instructions, lazyEdit.codeEdit]);
    const mergedCode = normalizeMergedText(originalCode, await mergeEdit({
      instructions: nonEmptyString(lazyEdit.instructions, "edit instructions"),
      originalCode,
      codeEdit: nonEmptyString(lazyEdit.codeEdit, "code edit")
    }));
    assertSafeOutboundText([mergedCode]);

    const currentCode = await readFile(editable.resolvedTarget, "utf8");
    if (hashText(currentCode) !== originalHash) {
      throw new Error("Target file changed while the edit was being prepared; no worker output was written.");
    }

    const changed = mergedCode !== originalCode;
    const diff = changed
      ? createTwoFilesPatch(editable.relative, editable.relative, originalCode, mergedCode, "before", "after")
      : "";
    if (!changed || dryRun) {
      return {
        model: model.id,
        providerModel: lazyEdit.providerModel ?? null,
        changed,
        written: false,
        backupPath: null,
        diff,
        gateEvidence: null,
        usage: lazyEdit.usage ?? null
      };
    }

    const gateEvidence = dependencies.beforeWrite
      ? await dependencies.beforeWrite({
        targetPath: editable.resolvedTarget,
        instruction,
        context,
        originalCode,
        mergedCode,
        diff
      })
      : null;

    const backupPath = await createBackup(
      backupRoot,
      editable.resolvedTarget,
      editable.relative,
      originalHash
    );
    const preWriteCode = await readFile(editable.resolvedTarget, "utf8");
    if (hashText(preWriteCode) !== originalHash) {
      throw new Error("Target file changed before the atomic replacement; no worker output was written.");
    }
    const replaceFile = dependencies.replaceFile ?? atomicReplaceText;
    await replaceFile(editable.resolvedTarget, mergedCode);
    const writtenCode = await readFile(editable.resolvedTarget, "utf8");
    if (hashText(writtenCode) !== hashText(mergedCode)) {
      throw new Error(`Worker write verification failed. Original backup: ${backupPath}`);
    }

    return {
      model: model.id,
      providerModel: lazyEdit.providerModel ?? null,
      changed: true,
      written: true,
      backupPath,
      diff,
      gateEvidence,
      usage: lazyEdit.usage ?? null
    };
  } finally {
    inFlightEditPaths.delete(lockKey);
  }
}

export async function runGuardedDocumentationEdit({
  approvalReference,
  ...editArgs
}) {
  const reviewChange = editArgs.dependencies?.reviewDocumentationChange ?? reviewDocumentationChange;
  return runGuardedEdit({
    ...editArgs,
    dependencies: {
      ...(editArgs.dependencies ?? {}),
      targetPolicy: (resolvedTarget) => assertDocumentationWorkerTarget({
        targetPath: resolvedTarget,
        dryRun: editArgs.dryRun ?? false,
        approvalReference
      }),
      beforeWrite: async ({ targetPath, instruction, context, diff }) => {
        const evidence = await reviewChange({
          targetPath,
          instruction,
          context,
          approvalReference,
          diff
        });
        const verdict = String(evidence?.verdict ?? "").toUpperCase();
        if (verdict !== "ACCEPT") {
          throw new Error(`Documentation guard returned ${verdict || "an invalid verdict"}; no documentation was written.`);
        }
        return { ...evidence, verdict };
      },
      workerMode: "documentation",
      basePrompt: [
        "Update only the supplied documentation file according to the bounded instruction and authority context.",
        "Call edit_file exactly once. Emit only changed sections and use // ... existing content ... for unchanged regions.",
        "Do not alter the operator goal, invent facts, weaken locks, or edit generated state."
      ].join(" ")
    }
  });
}
