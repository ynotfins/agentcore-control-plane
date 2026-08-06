import assert from "node:assert/strict";
import test from "node:test";

import {
  assertCodeWorkerTarget,
  assertDocumentationWorkerTarget
} from "./documentation-policy.mjs";

test("ordinary edit workers cannot edit documentation files", () => {
  assert.throws(
    () => assertCodeWorkerTarget("D:\\repo\\README.md"),
    /documentation maintainer/i
  );
});

test("documentation worker accepts routine docs with an accepted guard verdict", () => {
  assert.doesNotThrow(() => assertDocumentationWorkerTarget({
    targetPath: "D:\\repo\\docs\\operations\\RUNBOOK.md",
    dryRun: false,
    guardVerdict: "ACCEPT"
  }));
});

test("documentation worker requires live authority capability and approval for protected docs", () => {
  const previousCapability = process.env.AGENTCORE_AUTHORITY_CAPABILITY;
  const previousApproval = process.env.AGENTCORE_AUTHORITY_APPROVAL_ID;
  assert.throws(
    () => assertDocumentationWorkerTarget({
      targetPath: "D:\\repo\\BLUEPRINT.md",
      dryRun: false,
      guardVerdict: "ACCEPT"
    }),
    /approval_reference/i
  );

  try {
    process.env.AGENTCORE_AUTHORITY_CAPABILITY = "normal_builder";
    process.env.AGENTCORE_AUTHORITY_APPROVAL_ID = "AUTH-2026-08-06-DOCUMENTATION_GUARD";
    assert.throws(
      () => assertDocumentationWorkerTarget({
        targetPath: "D:\\repo\\BLUEPRINT.md",
        dryRun: false,
        approvalReference: "AUTH-2026-08-06-DOCUMENTATION_GUARD"
      }),
      /authority_maintainer/
    );

    process.env.AGENTCORE_AUTHORITY_CAPABILITY = "authority_maintainer";
    assert.doesNotThrow(() => assertDocumentationWorkerTarget({
      targetPath: "D:\\repo\\BLUEPRINT.md",
      dryRun: false,
      approvalReference: "AUTH-2026-08-06-DOCUMENTATION_GUARD"
    }));
  } finally {
    if (previousCapability === undefined) delete process.env.AGENTCORE_AUTHORITY_CAPABILITY;
    else process.env.AGENTCORE_AUTHORITY_CAPABILITY = previousCapability;
    if (previousApproval === undefined) delete process.env.AGENTCORE_AUTHORITY_APPROVAL_ID;
    else process.env.AGENTCORE_AUTHORITY_APPROVAL_ID = previousApproval;
  }
});

test("documentation dry runs remain available without write authorization", () => {
  assert.doesNotThrow(() => assertDocumentationWorkerTarget({
    targetPath: "D:\\repo\\docs\\README.md",
    dryRun: true
  }));
});

test("generated state projections remain projection-worker-only", () => {
  assert.throws(
    () => assertDocumentationWorkerTarget({
      targetPath: "D:\\repo\\.agentcore\\STATE.md",
      dryRun: false,
      guardVerdict: "ACCEPT"
    }),
    /projection-worker-only/i
  );
});

test("documentation worker rejects source code targets", () => {
  assert.throws(
    () => assertDocumentationWorkerTarget({
      targetPath: "D:\\repo\\src\\server.mjs",
      dryRun: true
    }),
    /documentation file/i
  );
});
