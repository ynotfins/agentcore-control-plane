import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import test from "node:test";
import { createHash } from "node:crypto";

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

// ---------------------------------------------------------------------------
// Deterministic documentation-maintainer regression tests.
// ---------------------------------------------------------------------------

function sha256Hex(buf) {
  return createHash("sha256").update(buf).digest("hex");
}

function deterministicDocDeps(overrides = {}) {
  return {
    generateEdit: async () => {
      throw new Error("deterministic mode must never call generateEdit");
    },
    mergeEdit: async () => {
      throw new Error("deterministic mode must never call mergeEdit");
    },
    reviewDocumentationChange: async () => ({ verdict: "ACCEPT", content: "ok" }),
    ...overrides
  };
}

// --- all-or-none argument validation ---------------------------------------

const partialFieldCases = [
  { label: "only candidateContent", fields: { candidateContent: "# Updated\n" }, missing: "baselineSha256" },
  { label: "only baselineSha256", fields: { baselineSha256: true }, missing: "candidateContent" },
  { label: "only expectedSha256", fields: { expectedSha256: true }, missing: "candidateContent" },
  {
    label: "candidateContent + baselineSha256",
    fields: { candidateContent: "# Updated\n", baselineSha256: true },
    missing: "expectedSha256",
  },
  {
    label: "candidateContent + expectedSha256",
    fields: { candidateContent: "# Updated\n", expectedSha256: true },
    missing: "baselineSha256",
  },
  {
    label: "baselineSha256 + expectedSha256",
    fields: { baselineSha256: true, expectedSha256: true },
    missing: "candidateContent",
  },
];

for (const { label, fields, missing } of partialFieldCases) {
  test(`deterministic doc maintainer rejects missing ${missing} (${label})`, async (t) => {
    const fixture = await makeFixture(t);
    const docPath = path.join(fixture.workspaceRoot, "README.md");
    const original = "# Original\n";
    await writeFile(docPath, original, "utf8");

    const baselineHash = sha256Hex(Buffer.from(original, "utf8"));
    const expectedHash = sha256Hex(Buffer.from("# Updated\n", "utf8"));

    const opts = {
      ...fixture,
      targetPath: docPath,
      instruction: `deterministic update (${label})`,
      model: minimax,
      dryRun: true,
      dependencies: deterministicDocDeps(),
    };

    if (fields.candidateContent !== undefined) opts.candidateContent = fields.candidateContent;
    if (fields.baselineSha256 !== undefined) opts.baselineSha256 = fields.baselineSha256 === true ? baselineHash : fields.baselineSha256;
    if (fields.expectedSha256 !== undefined) opts.expectedSha256 = fields.expectedSha256 === true ? expectedHash : fields.expectedSha256;

    await assert.rejects(
      runGuardedDocumentationEdit(opts),
      new RegExp(missing, "i")
    );
  });
}

// --- invalid 64-hex baseline / expected tests -------------------------------

for (const field of ["baselineSha256", "expectedSha256"]) {
  test(`deterministic doc maintainer rejects invalid 64-hex ${field}`, async (t) => {
    const fixture = await makeFixture(t);
    const docPath = path.join(fixture.workspaceRoot, "README.md");
    const original = "# Original\n";
    const candidate = "# Updated\n";
    await writeFile(docPath, original, "utf8");

    const validHash = sha256Hex(Buffer.from(original, "utf8"));

    const opts = {
      ...fixture,
      targetPath: docPath,
      instruction: `deterministic update invalid ${field}`,
      model: minimax,
      dryRun: true,
      candidateContent: candidate,
      baselineSha256: validHash,
      expectedSha256: sha256Hex(Buffer.from(candidate, "utf8")),
      dependencies: deterministicDocDeps(),
    };

    opts[field] = "not-64-hex-gg"; // invalid hex

    await assert.rejects(
      runGuardedDocumentationEdit(opts),
      /64-character hex|invalid.*hex|hex.*invalid|not a valid.*sha256|sha256.*invalid/i
    );
  });
}

// --- deterministic dry-run with matching hashes -----------------------------

test("deterministic dry-run with matching hashes returns exact unified diff, writes nothing, never calls generateEdit or mergeEdit", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const candidate = "# Updated\n";
  await writeFile(docPath, original, "utf8");

  let generateCalled = false;
  let mergeCalled = false;

  const result = await runGuardedDocumentationEdit({
    ...fixture,
    targetPath: docPath,
    instruction: "deterministic update",
    model: minimax,
    dryRun: true,
    candidateContent: candidate,
    baselineSha256: sha256Hex(Buffer.from(original, "utf8")),
    expectedSha256: sha256Hex(Buffer.from(candidate, "utf8")),
    dependencies: deterministicDocDeps({
      generateEdit: async () => { generateCalled = true; throw new Error("no"); },
      mergeEdit: async () => { mergeCalled = true; throw new Error("no"); }
    })
  });

  assert.equal(generateCalled, false);
  assert.equal(mergeCalled, false);
  assert.equal(result.changed, true);
  assert.equal(result.written, false);
  assert.equal(result.backupPath, null);
  assert.match(result.diff, /^-# Original$/m);
  assert.match(result.diff, /^\+# Updated$/m);
  assert.equal(await readFile(docPath, "utf8"), original);
});

// --- deterministic actual write with matching hashes and internal ACCEPT ---

test("deterministic actual write with matching hashes and internal ACCEPT writes exact candidate bytes, creates backup, returns hashes/diff/guard/backup", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const candidate = "# Updated\n";
  await writeFile(docPath, original, "utf8");

  const baselineHash = sha256Hex(Buffer.from(original, "utf8"));
  const expectedHash = sha256Hex(Buffer.from(candidate, "utf8"));

  const result = await runGuardedDocumentationEdit({
    ...fixture,
    targetPath: docPath,
    instruction: "deterministic update",
    model: minimax,
    dryRun: false,
    candidateContent: candidate,
    baselineSha256: baselineHash,
    expectedSha256: expectedHash,
    dependencies: deterministicDocDeps({
      reviewDocumentationChange: async () => ({ verdict: "ACCEPT", content: "aligned" })
    })
  });

  assert.equal(result.written, true);
  assert.equal(result.changed, true);
  assert.equal(result.baselineSha256, baselineHash);
  assert.equal(result.expectedSha256, expectedHash);
  assert.ok(result.writtenSha256);
  assert.equal(result.writtenSha256, sha256Hex(Buffer.from(candidate, "utf8")));
  assert.ok(result.backupPath);
  assert.equal(await readFile(result.backupPath, "utf8"), original);
  assert.equal(await readFile(docPath, "utf8"), candidate);
  assert.ok(result.diff);
  assert.ok(result.gateEvidence);
  assert.equal(result.gateEvidence.verdict, "ACCEPT");
});

// --- guard BLOCK prevents write ---------------------------------------------

test("deterministic guard BLOCK prevents write", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const candidate = "# Updated\n";
  await writeFile(docPath, original, "utf8");

  await assert.rejects(
    runGuardedDocumentationEdit({
      ...fixture,
      targetPath: docPath,
      instruction: "deterministic update",
      model: minimax,
      dryRun: false,
      candidateContent: candidate,
      baselineSha256: sha256Hex(Buffer.from(original, "utf8")),
      expectedSha256: sha256Hex(Buffer.from(candidate, "utf8")),
      dependencies: deterministicDocDeps({
        reviewDocumentationChange: async () => ({ verdict: "BLOCK", content: "unsafe" })
      })
    }),
    /BLOCK/i
  );

  assert.equal(await readFile(docPath, "utf8"), original);
});

// --- guard REVISE prevents write (treated like BLOCK) -----------------------

test("deterministic guard REVISE prevents write", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const candidate = "# Updated\n";
  await writeFile(docPath, original, "utf8");

  await assert.rejects(
    runGuardedDocumentationEdit({
      ...fixture,
      targetPath: docPath,
      instruction: "deterministic update",
      model: minimax,
      dryRun: false,
      candidateContent: candidate,
      baselineSha256: sha256Hex(Buffer.from(original, "utf8")),
      expectedSha256: sha256Hex(Buffer.from(candidate, "utf8")),
      dependencies: deterministicDocDeps({
        reviewDocumentationChange: async () => ({ verdict: "REVISE", content: "needs work" })
      })
    }),
    /REVISE/i
  );

  assert.equal(await readFile(docPath, "utf8"), original);
});

// --- baseline mismatch prevents guard/backup/write --------------------------

test("deterministic baseline mismatch prevents guard, backup, and write", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const candidate = "# Updated\n";
  await writeFile(docPath, original, "utf8");

  let guardCalled = false;

  await assert.rejects(
    runGuardedDocumentationEdit({
      ...fixture,
      targetPath: docPath,
      instruction: "deterministic update",
      model: minimax,
      dryRun: false,
      candidateContent: candidate,
      baselineSha256: sha256Hex(Buffer.from("# Wrong baseline\n", "utf8")),
      expectedSha256: sha256Hex(Buffer.from(candidate, "utf8")),
      dependencies: deterministicDocDeps({
        reviewDocumentationChange: async () => { guardCalled = true; return { verdict: "ACCEPT", content: "ok" }; }
      })
    }),
    /baseline.*mismatch/i
  );

  assert.equal(guardCalled, false);
  assert.equal(await readFile(docPath, "utf8"), original);
});

// --- candidate hash mismatch prevents guard/backup/write --------------------

test("deterministic candidate hash mismatch prevents guard, backup, and write", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const candidate = "# Updated\n";
  await writeFile(docPath, original, "utf8");

  let guardCalled = false;

  await assert.rejects(
    runGuardedDocumentationEdit({
      ...fixture,
      targetPath: docPath,
      instruction: "deterministic update",
      model: minimax,
      dryRun: false,
      candidateContent: candidate,
      baselineSha256: sha256Hex(Buffer.from(original, "utf8")),
      expectedSha256: sha256Hex(Buffer.from("# Wrong candidate\n", "utf8")),
      dependencies: deterministicDocDeps({
        reviewDocumentationChange: async () => { guardCalled = true; return { verdict: "ACCEPT", content: "ok" }; }
      })
    }),
    /expected hash mismatch|candidate.*hash.*mismatch/i
  );

  assert.equal(guardCalled, false);
  assert.equal(await readFile(docPath, "utf8"), original);
});

// --- pre-write concurrent target mutation is preserved and aborts -----------

test("deterministic pre-write concurrent target mutation is preserved and aborts", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const candidate = "# Updated\n";
  await writeFile(docPath, original, "utf8");

  await assert.rejects(
    runGuardedDocumentationEdit({
      ...fixture,
      targetPath: docPath,
      instruction: "deterministic update",
      model: minimax,
      dryRun: false,
      candidateContent: candidate,
      baselineSha256: sha256Hex(Buffer.from(original, "utf8")),
      expectedSha256: sha256Hex(Buffer.from(candidate, "utf8")),
      dependencies: deterministicDocDeps({
        reviewDocumentationChange: async () => {
          // concurrent mutation between guard and write
          await writeFile(docPath, "# Concurrent\n", "utf8");
          return { verdict: "ACCEPT", content: "ok" };
        }
      })
    }),
    /baseline hash mismatch before write|changed while/i
  );

  assert.equal(await readFile(docPath, "utf8"), "# Concurrent\n");
});

// --- deterministic mode never invokes generative editor or Morph ------------

test("deterministic mode never invokes generateEdit or mergeEdit", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const candidate = "# Updated\n";
  await writeFile(docPath, original, "utf8");

  let generateCalled = false;
  let mergeCalled = false;

  await assert.rejects(
    runGuardedDocumentationEdit({
      ...fixture,
      targetPath: docPath,
      instruction: "deterministic update",
      model: minimax,
      dryRun: false,
      candidateContent: candidate,
      baselineSha256: sha256Hex(Buffer.from(original, "utf8")),
      expectedSha256: sha256Hex(Buffer.from(candidate, "utf8")),
      dependencies: deterministicDocDeps({
        generateEdit: async () => { generateCalled = true; throw new Error("no"); },
        mergeEdit: async () => { mergeCalled = true; throw new Error("no"); },
        reviewDocumentationChange: async () => ({ verdict: "BLOCK", content: "no" })
      })
    }),
    /BLOCK/i
  );

  assert.equal(generateCalled, false);
  assert.equal(mergeCalled, false);
});

// --- byte-preservation tests -----------------------------------------------

const bytePreservationCases = [
  { label: "LF only", content: "line1\nline2\n" },
  { label: "CRLF", content: "line1\r\nline2\r\n" },
  { label: "UTF-8 BOM", content: "\uFEFF# Title\n" },
  { label: "no trailing newline", content: "# No newline" },
  { label: "trailing spaces", content: "# trailing   \n" },
  { label: "non-ASCII", content: "# 日本語ドキュメント\n" },
  { label: "mixed Unicode", content: "# Café résumé\n" },
];

for (const { label, content } of bytePreservationCases) {
  test(`deterministic byte preservation: ${label}`, async (t) => {
    const fixture = await makeFixture(t);
    const docPath = path.join(fixture.workspaceRoot, "README.md");

    const originalBuf = Buffer.from("baseline\n", "utf8");
    const candidateBuf = Buffer.from(content, "utf8");
    const candidateStr = candidateBuf.toString("utf8");

    await writeFile(docPath, originalBuf);
    const baselineHash = sha256Hex(originalBuf);
    const expectedHash = sha256Hex(candidateBuf);

    const result = await runGuardedDocumentationEdit({
      ...fixture,
      targetPath: docPath,
      instruction: `deterministic byte preservation ${label}`,
      model: minimax,
      dryRun: false,
      candidateContent: candidateStr,
      baselineSha256: baselineHash,
      expectedSha256: expectedHash,
      dependencies: deterministicDocDeps({
        reviewDocumentationChange: async () => ({ verdict: "ACCEPT", content: "ok" })
      })
    });

    assert.equal(result.written, true, `${label}: should write`);
    assert.equal(result.writtenSha256, expectedHash, `${label}: written hash mismatch`);

    // Assert raw bytes (no encoding) to prove byte-preservation
    const onDisk = await readFile(docPath);
    assert.ok(Buffer.isBuffer(onDisk), `${label}: readFile without encoding must return Buffer`);
    assert.deepEqual(onDisk, candidateBuf, `${label}: raw bytes mismatch`);
  });
}

// --- no-op deterministic candidate: changed=false, written=false, no guard/write

test("deterministic no-op candidate returns changed=false, written=false without guard or write", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  await writeFile(docPath, original, "utf8");

  let guardCalled = false;

  const result = await runGuardedDocumentationEdit({
    ...fixture,
    targetPath: docPath,
    instruction: "deterministic no-op",
    model: minimax,
    dryRun: false,
    candidateContent: original,
    baselineSha256: sha256Hex(Buffer.from(original, "utf8")),
    expectedSha256: sha256Hex(Buffer.from(original, "utf8")),
    dependencies: deterministicDocDeps({
      reviewDocumentationChange: async () => { guardCalled = true; return { verdict: "ACCEPT", content: "ok" }; }
    })
  });

  assert.equal(result.changed, false);
  assert.equal(result.written, false);
  assert.equal(guardCalled, false);
  assert.equal(await readFile(docPath, "utf8"), original);
});

// --- post-write verification failure with rollback --------------------------

test("post-write verification failure with target matching candidate attempts rollback and verifies restored baseline", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const candidate = "# Updated\n";
  await writeFile(docPath, original, "utf8");

  const baselineHash = sha256Hex(Buffer.from(original, "utf8"));
  const expectedHash = sha256Hex(Buffer.from(candidate, "utf8"));

  // Simulate post-write verification failure: the written content is correct
  // (target == candidate) but verification reports mismatch.
  await assert.rejects(
    runGuardedDocumentationEdit({
      ...fixture,
      targetPath: docPath,
      instruction: "deterministic update",
      model: minimax,
      dryRun: false,
      candidateContent: candidate,
      baselineSha256: baselineHash,
      expectedSha256: expectedHash,
      dependencies: deterministicDocDeps({
        reviewDocumentationChange: async () => ({ verdict: "ACCEPT", content: "ok" }),
        // Simulate post-write verification failure
        verifyWrittenContent: async () => { throw new Error("post-write verification failed"); }
      })
    }),
    /post-write verification/i
  );

  // Rollback should have restored the original baseline
  assert.equal(await readFile(docPath, "utf8"), original);
});

// --- restoration failure reports actual state and rollback path -------------

test("restoration failure reports actual state and rollback path without false recovered claim", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const candidate = "# Updated\n";
  await writeFile(docPath, original, "utf8");

  const baselineHash = sha256Hex(Buffer.from(original, "utf8"));
  const expectedHash = sha256Hex(Buffer.from(candidate, "utf8"));

  let rollbackCalled = false;
  let capturedError;

  try {
    await runGuardedDocumentationEdit({
      ...fixture,
      targetPath: docPath,
      instruction: "deterministic update",
      model: minimax,
      dryRun: false,
      candidateContent: candidate,
      baselineSha256: baselineHash,
      expectedSha256: expectedHash,
      dependencies: deterministicDocDeps({
        reviewDocumentationChange: async () => ({ verdict: "ACCEPT", content: "ok" }),
        verifyWrittenContent: async () => { throw new Error("post-write verification failed"); },
        // Simulate rollback failure
        restoreFile: async () => { rollbackCalled = true; throw new Error("rollback failed"); }
      })
    });
  } catch (err) {
    capturedError = err;
  }

  assert.ok(capturedError, "should have thrown");
  assert.equal(rollbackCalled, true);
  assert.match(capturedError.message, /rollback/i);

  // Assert actual bytes on disk — target still contains the candidate (rollback failed)
  const onDisk = await readFile(docPath);
  assert.ok(Buffer.isBuffer(onDisk));
  assert.deepEqual(onDisk, Buffer.from(candidate, "utf8"));

  // Error must contain rollback path or recovery status
  assert.match(capturedError.message, /rollback|recovery|restore|path/i);
});

// --- external-edit recovery: external bytes preserved -----------------------

test("external-edit recovery preserves exact external bytes and requires external_change_preserved", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const candidate = "# Updated\n";
  const external = "# External mutation\n";
  await writeFile(docPath, original, "utf8");

  const baselineHash = sha256Hex(Buffer.from(original, "utf8"));
  const expectedHash = sha256Hex(Buffer.from(candidate, "utf8"));

  let capturedError;

  try {
    await runGuardedDocumentationEdit({
      ...fixture,
      targetPath: docPath,
      instruction: "deterministic update",
      model: minimax,
      dryRun: false,
      candidateContent: candidate,
      baselineSha256: baselineHash,
      expectedSha256: expectedHash,
      dependencies: deterministicDocDeps({
        reviewDocumentationChange: async () => ({ verdict: "ACCEPT", content: "ok" }),
        verifyWrittenContent: async () => {
          // External actor mutates target to something else entirely
          await writeFile(docPath, external, "utf8");
          throw new Error("post-write verification failed");
        }
      })
    });
  } catch (err) {
    capturedError = err;
  }

  assert.ok(capturedError, "should have thrown");
  assert.match(capturedError.message, /external_change_preserved/i);

  // External bytes must be preserved exactly
  const onDisk = await readFile(docPath);
  assert.ok(Buffer.isBuffer(onDisk));
  assert.deepEqual(onDisk, Buffer.from(external, "utf8"));
});

// --- generated-projections policy enforced on real path ---------------------

test("deterministic doc maintainer rejects projection-worker-only targets", async (t) => {
  const fixture = await makeFixture(t);
  const agentcoreDir = path.join(fixture.workspaceRoot, ".agentcore");
  await mkdir(agentcoreDir, { recursive: true });
  const statePath = path.join(agentcoreDir, "STATE.md");
  const original = "# state\n";
  const candidate = "# updated state\n";
  await writeFile(statePath, original, "utf8");

  await assert.rejects(
    runGuardedDocumentationEdit({
      ...fixture,
      targetPath: statePath,
      instruction: "deterministic state update",
      model: minimax,
      dryRun: true,
      candidateContent: candidate,
      baselineSha256: sha256Hex(Buffer.from(original, "utf8")),
      expectedSha256: sha256Hex(Buffer.from(candidate, "utf8")),
      dependencies: deterministicDocDeps()
    }),
    /projection-worker-only|projection.*worker|projection/i
  );

  assert.equal(await readFile(statePath, "utf8"), original);
});

// --- protected-authorization test using workspace/AGENTS.md -----------------

test("deterministic doc maintainer enforces protected-authorization on AGENTS.md", async (t) => {
  const fixture = await makeFixture(t);
  const agentsPath = path.join(fixture.workspaceRoot, "AGENTS.md");
  const original = "# Agents\n";
  const candidate = "# Agents Updated\n";
  await writeFile(agentsPath, original, "utf8");

  const baselineHash = sha256Hex(Buffer.from(original, "utf8"));
  const expectedHash = sha256Hex(Buffer.from(candidate, "utf8"));

  const previousCapability = process.env.AGENTCORE_AUTHORITY_CAPABILITY;
  const previousApproval = process.env.AGENTCORE_AUTHORITY_APPROVAL_ID;
  t.after(() => {
    if (previousCapability === undefined) delete process.env.AGENTCORE_AUTHORITY_CAPABILITY;
    else process.env.AGENTCORE_AUTHORITY_CAPABILITY = previousCapability;
    if (previousApproval === undefined) delete process.env.AGENTCORE_AUTHORITY_APPROVAL_ID;
    else process.env.AGENTCORE_AUTHORITY_APPROVAL_ID = previousApproval;
  });

  const approvalReference = "AUTH-2026-11-06-DETERMINISTIC-DOCUMENTATION-MAINTAINER";

  process.env.AGENTCORE_AUTHORITY_CAPABILITY = "normal_builder";
  process.env.AGENTCORE_AUTHORITY_APPROVAL_ID = approvalReference;

  await assert.rejects(
    runGuardedDocumentationEdit({
      ...fixture,
      targetPath: agentsPath,
      instruction: "deterministic update AGENTS.md",
      model: minimax,
      dryRun: false,
      candidateContent: candidate,
      baselineSha256: baselineHash,
      expectedSha256: expectedHash,
      approvalReference,
      dependencies: deterministicDocDeps({
        reviewDocumentationChange: async () => ({ verdict: "ACCEPT", content: "ok" })
      })
    }),
    /authority_maintainer/i
  );

  assert.equal(await readFile(agentsPath, "utf8"), original);

  process.env.AGENTCORE_AUTHORITY_CAPABILITY = "authority_maintainer";
  process.env.AGENTCORE_AUTHORITY_APPROVAL_ID = "AUTH-2026-11-06-DIFFERENT-APPROVAL";

  await assert.rejects(
    runGuardedDocumentationEdit({
      ...fixture,
      targetPath: agentsPath,
      instruction: "deterministic update AGENTS.md",
      model: minimax,
      dryRun: false,
      candidateContent: candidate,
      baselineSha256: baselineHash,
      expectedSha256: expectedHash,
      approvalReference,
      dependencies: deterministicDocDeps({
        reviewDocumentationChange: async () => ({ verdict: "ACCEPT", content: "ok" })
      })
    }),
    /approval_reference.*match/i
  );

  assert.equal(await readFile(agentsPath, "utf8"), original);
});

test("deterministic candidate secret safety rejects before guard or write", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const previous = process.env.DETERMINISTIC_WORKER_TEST_SECRET;
  const secret = "deterministic-secret-abcdefghijklmnopqrstuvwxyz";
  const candidate = `# Candidate ${secret}\n`;
  process.env.DETERMINISTIC_WORKER_TEST_SECRET = secret;
  await writeFile(docPath, original, "utf8");
  t.after(() => {
    if (previous === undefined) delete process.env.DETERMINISTIC_WORKER_TEST_SECRET;
    else process.env.DETERMINISTIC_WORKER_TEST_SECRET = previous;
  });

  let guardCalled = false;
  await assert.rejects(
    runGuardedDocumentationEdit({
      ...fixture,
      targetPath: docPath,
      instruction: "deterministic secret candidate",
      model: minimax,
      dryRun: false,
      candidateContent: candidate,
      baselineSha256: sha256Hex(Buffer.from(original, "utf8")),
      expectedSha256: sha256Hex(Buffer.from(candidate, "utf8")),
      dependencies: deterministicDocDeps({
        reviewDocumentationChange: async () => {
          guardCalled = true;
          return { verdict: "ACCEPT", content: "unexpected" };
        }
      })
    }),
    /DETERMINISTIC_WORKER_TEST_SECRET/
  );

  assert.equal(guardCalled, false);
  assert.equal(await readFile(docPath, "utf8"), original);
});

// --- file replacement dependency coherence tests ----------------------------

test("deterministic write uses replaceFile for candidate atomic replacement", async (t) => {
  const fixture = await makeFixture(t);
  const docPath = path.join(fixture.workspaceRoot, "README.md");
  const original = "# Original\n";
  const candidate = "# Updated\n";
  await writeFile(docPath, original, "utf8");

  let replaceCalled = false;

  const result = await runGuardedDocumentationEdit({
    ...fixture,
    targetPath: docPath,
    instruction: "deterministic update",
    model: minimax,
    dryRun: false,
    candidateContent: candidate,
    baselineSha256: sha256Hex(Buffer.from(original, "utf8")),
    expectedSha256: sha256Hex(Buffer.from(candidate, "utf8")),
    dependencies: deterministicDocDeps({
      reviewDocumentationChange: async () => ({ verdict: "ACCEPT", content: "ok" }),
      replaceFile: async (targetPath, content) => {
        replaceCalled = true;
        await writeFile(targetPath, content, "utf8");
      }
    })
  });

  assert.equal(replaceCalled, true);
  assert.equal(result.written, true);
  assert.equal(await readFile(docPath, "utf8"), candidate);
});
