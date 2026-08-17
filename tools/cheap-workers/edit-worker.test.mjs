import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";

import {
  atomicReplaceText,
  generateLazyEdit,
  parseDocumentationGuardVerdict,
  parseEditToolCall,
  runGuardedDocumentationEdit,
  runGuardedEdit
} from "./edit-worker.mjs";

async function makeFixture(t) {
  const root = await mkdtemp(path.join(tmpdir(), "cheap-edit-worker-"));
  t.after(async () => {
    await rm(root, { recursive: true, force: true });
  });

  const workspaceRoot = path.join(root, "workspace");
  const backupRoot = path.join(root, "backups");
  const targetPath = path.join(workspaceRoot, "example.js");
  await mkdir(workspaceRoot, { recursive: true });
  await writeFile(targetPath, "const value = 1;\n", "utf8");
  return { backupRoot, targetPath, workspaceRoot };
}

const minimax = {
  id: "minimax/minimax-m3",
  label: "MiniMax M3",
  defaultPurpose: "long-context coding synthesis and sustained agentic implementation work"
};

function editDependencies(overrides = {}) {
  return {
    generateEdit: async () => ({
      instructions: "I will update the value.",
      codeEdit: "const value = 2;"
    }),
    mergeEdit: async () => "const value = 2;\n",
    ...overrides
  };
}

test("dry run returns a diff without changing or backing up the file", async (t) => {
  const fixture = await makeFixture(t);

  const result = await runGuardedEdit({
    ...fixture,
    instruction: "Change the value to 2.",
    model: minimax,
    dryRun: true,
    dependencies: editDependencies()
  });

  assert.equal(await readFile(fixture.targetPath, "utf8"), "const value = 1;\n");
  assert.equal(result.changed, true);
  assert.equal(result.written, false);
  assert.equal(result.backupPath, null);
  assert.match(result.diff, /^-const value = 1;$/m);
  assert.match(result.diff, /^\+const value = 2;$/m);
});

test("write mode creates a backup and applies the merged content", async (t) => {
  const fixture = await makeFixture(t);

  const result = await runGuardedEdit({
    ...fixture,
    instruction: "Change the value to 2.",
    model: minimax,
    dryRun: false,
    dependencies: editDependencies()
  });

  assert.equal(await readFile(fixture.targetPath, "utf8"), "const value = 2;\n");
  assert.equal(result.written, true);
  assert.ok(result.backupPath);
  assert.equal(await readFile(result.backupPath, "utf8"), "const value = 1;\n");
});

test("target paths outside the workspace are rejected before model calls", async (t) => {
  const fixture = await makeFixture(t);
  const outsidePath = path.join(path.dirname(fixture.workspaceRoot), "outside.js");
  await writeFile(outsidePath, "outside\n", "utf8");
  let called = false;

  await assert.rejects(
    runGuardedEdit({
      ...fixture,
      targetPath: outsidePath,
      instruction: "Change the file.",
      model: minimax,
      dryRun: false,
      dependencies: editDependencies({
        generateEdit: async () => {
          called = true;
          throw new Error("must not run");
        }
      })
    }),
    /outside the workspace root/i
  );
  assert.equal(called, false);
  assert.equal(await readFile(outsidePath, "utf8"), "outside\n");
});

test("ordinary edit worker rejects documentation targets before model calls", async (t) => {
  const fixture = await makeFixture(t);
  const documentationPath = path.join(fixture.workspaceRoot, "README.md");
  await writeFile(documentationPath, "# Existing\n", "utf8");
  let called = false;

  await assert.rejects(
    runGuardedEdit({
      ...fixture,
      targetPath: documentationPath,
      instruction: "Update the documentation.",
      model: minimax,
      dryRun: true,
      dependencies: editDependencies({
        generateEdit: async () => {
          called = true;
          throw new Error("must not run");
        }
      })
    }),
    /documentation maintainer/i
  );
  assert.equal(called, false);
});

test("documentation maintainer can propose an accepted routine documentation edit", async (t) => {
  const fixture = await makeFixture(t);
  const documentationPath = path.join(fixture.workspaceRoot, "README.md");
  await writeFile(documentationPath, "# Existing\n", "utf8");

  const result = await runGuardedDocumentationEdit({
    ...fixture,
    targetPath: documentationPath,
    instruction: "Update the heading.",
    model: minimax,
    dryRun: true,
    dependencies: editDependencies({
      mergeEdit: async () => "# Updated\n"
    })
  });

  assert.equal(result.changed, true);
  assert.equal(result.written, false);
  assert.equal(await readFile(documentationPath, "utf8"), "# Existing\n");
});

test("documentation maintainer internally blocks a forged caller verdict", async (t) => {
  const fixture = await makeFixture(t);
  const documentationPath = path.join(fixture.workspaceRoot, "README.md");
  await writeFile(documentationPath, "# Existing\n", "utf8");

  await assert.rejects(
    runGuardedDocumentationEdit({
      ...fixture,
      targetPath: documentationPath,
      instruction: "Update the heading.",
      guardVerdict: "ACCEPT",
      model: minimax,
      dryRun: false,
      dependencies: editDependencies({
        mergeEdit: async () => "# Updated\n",
        reviewDocumentationChange: async () => ({ verdict: "BLOCK", content: "Unsafe drift." })
      })
    }),
    /documentation guard returned BLOCK/i
  );
  assert.equal(await readFile(documentationPath, "utf8"), "# Existing\n");
});

test("documentation maintainer writes only after its internal guard accepts the proposed diff", async (t) => {
  const fixture = await makeFixture(t);
  const documentationPath = path.join(fixture.workspaceRoot, "README.md");
  await writeFile(documentationPath, "# Existing\n", "utf8");

  const result = await runGuardedDocumentationEdit({
    ...fixture,
    targetPath: documentationPath,
    instruction: "Update the heading.",
    guardVerdict: "BLOCK",
    model: minimax,
    dryRun: false,
    dependencies: editDependencies({
      mergeEdit: async () => "# Updated\n",
      reviewDocumentationChange: async () => ({ verdict: "ACCEPT", content: "Aligned." })
    })
  });

  assert.equal(result.written, true);
  assert.equal(result.gateEvidence.verdict, "ACCEPT");
  assert.equal(await readFile(documentationPath, "utf8"), "# Updated\n");
});

test("oversized files are rejected before model or Morph calls", async (t) => {
  const fixture = await makeFixture(t);
  let called = false;

  await assert.rejects(
    runGuardedEdit({
      ...fixture,
      instruction: "Change the file.",
      model: minimax,
      maxFileBytes: 8,
      dependencies: editDependencies({
        generateEdit: async () => {
          called = true;
          throw new Error("must not run");
        }
      })
    }),
    /exceeds the edit-worker size limit/i
  );
  assert.equal(called, false);
  assert.equal(await readFile(fixture.targetPath, "utf8"), "const value = 1;\n");
});

test("files containing active secrets are rejected before external calls", async (t) => {
  const fixture = await makeFixture(t);
  const previous = process.env.WORKER_TEST_SECRET;
  const secret = "local-test-secret-abcdefghijklmnopqrstuvwxyz";
  process.env.WORKER_TEST_SECRET = secret;
  await writeFile(fixture.targetPath, `const credential = "${secret}";\n`, "utf8");
  let called = false;
  t.after(() => {
    if (previous === undefined) delete process.env.WORKER_TEST_SECRET;
    else process.env.WORKER_TEST_SECRET = previous;
  });

  await assert.rejects(
    runGuardedEdit({
      ...fixture,
      instruction: "Change the file.",
      model: minimax,
      dependencies: editDependencies({
        generateEdit: async () => {
          called = true;
          throw new Error("must not run");
        }
      })
    }),
    /WORKER_TEST_SECRET/
  );
  assert.equal(called, false);
});

test("atomic replacement preserves the original and removes its temporary file on rename failure", async (t) => {
  const fixture = await makeFixture(t);

  await assert.rejects(
    atomicReplaceText(fixture.targetPath, "const value = 2;\n", {
      renameFile: async () => {
        throw new Error("simulated rename failure");
      }
    }),
    /simulated rename failure/
  );

  assert.equal(await readFile(fixture.targetPath, "utf8"), "const value = 1;\n");
  assert.deepEqual(await readdir(fixture.workspaceRoot), ["example.js"]);
});

test("atomic replacement swaps the file and leaves no temporary file", async (t) => {
  const fixture = await makeFixture(t);

  await atomicReplaceText(fixture.targetPath, "const value = 2;\n");

  assert.equal(await readFile(fixture.targetPath, "utf8"), "const value = 2;\n");
  assert.deepEqual(await readdir(fixture.workspaceRoot), ["example.js"]);
});

test("a concurrent file change is preserved and aborts the worker write", async (t) => {
  const fixture = await makeFixture(t);
  const dependencies = editDependencies({
    mergeEdit: async () => {
      await writeFile(fixture.targetPath, "const value = 99;\n", "utf8");
      return "const value = 2;\n";
    }
  });

  await assert.rejects(
    runGuardedEdit({
      ...fixture,
      instruction: "Change the value to 2.",
      model: minimax,
      dryRun: false,
      dependencies
    }),
    /changed while the edit was being prepared/i
  );
  assert.equal(await readFile(fixture.targetPath, "utf8"), "const value = 99;\n");
});

test("a second edit against the same canonical path is rejected while the first is in flight", async (t) => {
  const fixture = await makeFixture(t);
  let releaseFirst;
  let markStarted;
  const firstStarted = new Promise((resolve) => {
    markStarted = resolve;
  });
  const holdFirst = new Promise((resolve) => {
    releaseFirst = resolve;
  });
  const firstDependencies = editDependencies({
    generateEdit: async () => {
      markStarted();
      await holdFirst;
      return {
        instructions: "I will update the value.",
        codeEdit: "const value = 2;"
      };
    }
  });

  const firstEdit = runGuardedEdit({
    ...fixture,
    instruction: "Change the value to 2.",
    model: minimax,
    dryRun: true,
    dependencies: firstDependencies
  });
  await firstStarted;

  await assert.rejects(
    runGuardedEdit({
      ...fixture,
      instruction: "Also change the value.",
      model: minimax,
      dryRun: true,
      dependencies: editDependencies()
    }),
    /already being edited/i
  );

  releaseFirst();
  await firstEdit;
});

test("forced OpenRouter edit tool calls are parsed into lazy-edit fields", () => {
  const response = {
    choices: [{
      message: {
        tool_calls: [{
          function: {
            name: "edit_file",
            arguments: JSON.stringify({
              instructions: "I will update the value.",
              code_edit: "const value = 2;"
            })
          }
        }]
      }
    }]
  };

  assert.deepEqual(parseEditToolCall(response), {
    instructions: "I will update the value.",
    codeEdit: "const value = 2;"
  });
});

test("documentation guard parsing uses the final explicit verdict", () => {
  assert.equal(
    parseDocumentationGuardVerdict("ACCEPT is discussed above.\nFinal Verdict: **BLOCK**"),
    "BLOCK"
  );
  assert.throws(
    () => parseDocumentationGuardVerdict("The proposal seems acceptable."),
    /did not include a final/i
  );
});

test("lazy edit generation validates and returns the provider-reported model", async (t) => {
  const previousKey = process.env.OPENROUTER_CODEX_API_KEY;
  process.env.OPENROUTER_CODEX_API_KEY = "test-key";
  t.after(() => {
    if (previousKey === undefined) delete process.env.OPENROUTER_CODEX_API_KEY;
    else process.env.OPENROUTER_CODEX_API_KEY = previousKey;
  });

  const result = await generateLazyEdit({
    model: minimax,
    targetPath: "C:\\workspace\\example.js",
    instruction: "Change the value.",
    originalCode: "const value = 1;\n",
    fetchImpl: async () => ({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({
        model: "minimax/minimax-m3",
        choices: [{
          message: {
            tool_calls: [{
              function: {
                name: "edit_file",
                arguments: JSON.stringify({
                  instructions: "I will update the value.",
                  code_edit: "const value = 2;"
                })
              }
            }]
          }
        }]
      })
    })
  });

  assert.equal(result.providerModel, "minimax/minimax-m3");
});
