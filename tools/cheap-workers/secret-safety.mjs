const SECRET_ENV_NAME = /(?:KEY|TOKEN|SECRET|PASSWORD)$/i;
const MIN_SECRET_LENGTH = 8;

const CREDENTIAL_PATTERNS = Object.freeze([
  { label: "OpenRouter credential pattern", pattern: /\bsk-or-v1-[A-Za-z0-9_-]{20,}\b/ },
  { label: "GitHub credential pattern", pattern: /\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b/ },
  { label: "Morph credential pattern", pattern: /\bmorph-[A-Za-z0-9_-]{20,}\b/ },
  { label: "private key pattern", pattern: /-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----/ }
]);

export function assertSafeOutboundText(parts) {
  const values = Array.isArray(parts) ? parts : [parts];
  const text = values
    .filter((value) => value !== undefined && value !== null)
    .map((value) => typeof value === "string" ? value : JSON.stringify(value))
    .join("\n");

  for (const [name, value] of Object.entries(process.env)) {
    if (!SECRET_ENV_NAME.test(name) || typeof value !== "string" || value.length < MIN_SECRET_LENGTH) {
      continue;
    }
    if (text.includes(value)) {
      throw new Error(`Outbound worker content contains the active Windows environment secret ${name}.`);
    }
  }

  for (const { label, pattern } of CREDENTIAL_PATTERNS) {
    if (pattern.test(text)) {
      throw new Error(`Outbound worker content contains a ${label}.`);
    }
  }
}
