import assert from "node:assert/strict";
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

test("outbound preflight permits environment variable names and obvious placeholders", () => {
  assert.doesNotThrow(() => assertSafeOutboundText([
    "Read OPENROUTER_API_KEY from Windows environment variables.",
    "Authorization: Bearer <token>",
    "apiKey: YOUR_API_KEY"
  ]));
});
