import assert from "node:assert/strict";
import test from "node:test";

import { assertProviderModel, buildWorkerSystemPrompt } from "./worker-prompts.mjs";

const models = {
  flash: {
    id: "~deepseek/deepseek-v4-flash-latest",
    label: "DeepSeek V4 Flash Latest",
    defaultPurpose: "rapid repository scouting, triage, and concise first-pass coding analysis"
  },
  minimax: {
    id: "minimax/minimax-m3",
    label: "MiniMax M3",
    defaultPurpose: "long-context coding synthesis and sustained agentic implementation work"
  },
  pro: {
    id: "deepseek/deepseek-v4-pro",
    label: "DeepSeek V4 Pro",
    defaultPurpose: "complex reasoning, architecture, difficult debugging, and rigorous critique"
  }
};

test("read-only workers receive exact identity, specialty, authority, and safety boundaries", () => {
  const prompt = buildWorkerSystemPrompt({
    model: models.flash,
    mode: "read-only",
    basePrompt: "Do the bounded job."
  });

  assert.match(prompt, /DeepSeek V4 Flash Latest/);
  assert.match(prompt, /~deepseek\/deepseek-v4-flash-latest/);
  assert.match(prompt, /rapid repository scouting/);
  assert.match(prompt, /Codex owns the master plan and final verification/);
  assert.match(prompt, /reproduce the exact label and ID above verbatim/);
  assert.match(prompt, /Never request, reveal, or reproduce secrets/);
  assert.match(prompt, /must not edit files/i);
});

test("edit workers receive the implementation contract and model-specific specialty", () => {
  const prompt = buildWorkerSystemPrompt({
    model: models.minimax,
    mode: "edit",
    basePrompt: "Call edit_file exactly once."
  });

  assert.match(prompt, /MiniMax M3 \(minimax\/minimax-m3\)/);
  assert.match(prompt, /long-context coding synthesis/);
  assert.match(prompt, /one bounded existing-file change/i);
  assert.match(prompt, /return a lazy edit/i);
  assert.match(prompt, /Codex owns the master plan and final verification/);
});

test("critique workers receive a findings-first adversarial review contract", () => {
  const prompt = buildWorkerSystemPrompt({
    model: models.pro,
    mode: "critique",
    basePrompt: "Review supplied evidence."
  });

  assert.match(prompt, /DeepSeek V4 Pro \(deepseek\/deepseek-v4-pro\)/);
  assert.match(prompt, /complex reasoning, architecture, difficult debugging, and rigorous critique/);
  assert.match(prompt, /findings ordered by severity/i);
  assert.match(prompt, /BLOCK, REVISE, or ACCEPT/);
  assert.match(prompt, /must not edit files/i);
});

test("documentation maintainers are bounded by authority and cannot rewrite generated state", () => {
  const prompt = buildWorkerSystemPrompt({
    model: models.pro,
    mode: "documentation",
    basePrompt: "Maintain one documentation file."
  });

  assert.match(prompt, /documentation maintainer/i);
  assert.match(prompt, /operator goal/i);
  assert.match(prompt, /generated state/i);
  assert.match(prompt, /must not create architecture authority/i);
});

test("provider model validation enforces fixed routes and permits only the Flash alias family", () => {
  assert.equal(
    assertProviderModel(models.pro, "deepseek/deepseek-v4-pro"),
    "deepseek/deepseek-v4-pro"
  );
  assert.equal(
    assertProviderModel(models.flash, "deepseek/deepseek-v4-flash-20260801"),
    "deepseek/deepseek-v4-flash-20260801"
  );
  assert.throws(
    () => assertProviderModel(models.pro, "minimax/minimax-m3"),
    /provider model mismatch/i
  );
  assert.throws(
    () => assertProviderModel(models.flash, "deepseek/deepseek-v4-pro"),
    /provider model mismatch/i
  );
});
