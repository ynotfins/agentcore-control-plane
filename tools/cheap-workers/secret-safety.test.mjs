import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { assertSafeOutboundText } from "./secret-safety.mjs";

test("outbound preflight rejects an active environment secret without echoing it", () => {
  const previous = process.env.WORKER_TEST_API_KEY;
  const secret = "sk-test-active-secret-1234567890";
  process.env.WORKER_TEST_API_KEY = secret;

  try {
    assert.throws(
      () => assertSafeOutboundText(["prefix", `payload ${secret} suffix`]),
      (error) => {
        assert.match(error.message, /WORKER_TEST_API_KEY/);
        assert.doesNotMatch(error.message, new RegExp(secret));
        return true;
      }
    );
  } finally {
    if (previous === undefined) delete process.env.WORKER_TEST_API_KEY;
    else process.env.WORKER_TEST_API_KEY = previous;
  }
});

test("outbound preflight rejects short active environment secrets", () => {
  const previous = process.env.WORKER_SHORT_TOKEN;
  process.env.WORKER_SHORT_TOKEN = "aB3dE5gH9";

  try {
    assert.throws(
      () => assertSafeOutboundText(["payload aB3dE5gH9 suffix"]),
      /WORKER_SHORT_TOKEN/
    );
  } finally {
    if (previous === undefined) delete process.env.WORKER_SHORT_TOKEN;
    else process.env.WORKER_SHORT_TOKEN = previous;
  }
});

test("outbound preflight rejects high-confidence credential formats", () => {
  assert.throws(
    () => assertSafeOutboundText(["const token = 'sk-or-v1-abcdefghijklmnopqrstuvwxyz123456';"]),
    /OpenRouter credential pattern/
  );
});

test("outbound preflight rejects a private-key block", () => {
  assert.throws(
    () => assertSafeOutboundText(["-----BEGIN PRIVATE KEY-----\nredacted-material"]),
    /private key pattern/i
  );
});

test("cheap workers require the dedicated Codex OpenRouter key", async () => {
  for (const relativePath of ["server.mjs", "edit-worker.mjs"]) {
    const source = await readFile(new URL(relativePath, import.meta.url), "utf8");
    assert.match(source, /process\.env\.OPENROUTER_CODEX_API_KEY/);
    assert.doesNotMatch(source, /process\.env\.OPENROUTER_API_KEY/);
    assert.match(source, /OPENROUTER_CODEX_API_KEY is not set in the environment/);
  }
});

test("outbound preflight permits environment variable names and obvious placeholders", () => {
  assert.doesNotThrow(() => assertSafeOutboundText([
    "Read OPENROUTER_CODEX_API_KEY from Windows environment variables.",
    "Authorization: Bearer <token>",
    "apiKey: YOUR_API_KEY"
  ]));
});
