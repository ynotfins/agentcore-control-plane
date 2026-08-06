const MODE_CONTRACTS = Object.freeze({
  "read-only": [
    "Mode: read-only analysis worker; you must not edit files or claim to run tools.",
    "Return concise evidence, file and line references when supplied, assumptions, risks, and an actionable conclusion."
  ],
  edit: [
    "Mode: implementation worker for one bounded existing-file change.",
    "Return a lazy edit through the required edit_file call, preserve unrelated code, and do not claim tests passed."
  ],
  critique: [
    "Mode: read-only adversarial critic; you must not edit files or silently repair the work.",
    "Return findings ordered by severity, missing verification, assumptions, and a final verdict of BLOCK, REVISE, or ACCEPT."
  ],
  documentation: [
    "Mode: documentation maintainer for one bounded existing documentation-file change.",
    "Preserve the operator goal and the supplied authority chain; you must not create architecture authority or silently change product intent.",
    "Return a lazy edit through the required edit_file call, preserve unrelated text, and do not claim tests passed.",
    "Never edit generated state projections; those remain owned by their authoritative projection worker."
  ]
});

export function assertProviderModel(model, providerModel) {
  const reported = typeof providerModel === "string" ? providerModel.trim() : "";
  const isAlias = model?.id?.startsWith("~");
  const aliasFamily = isAlias
    ? model.id.slice(1).replace(/-latest$/, "")
    : null;
  const matches = isAlias
    ? reported === model.id || reported.startsWith(aliasFamily)
    : reported === model?.id;

  if (!matches) {
    throw new Error(`Provider model mismatch: requested ${model?.id ?? "unknown"}, received ${reported || "missing"}.`);
  }
  return reported;
}

export function buildWorkerSystemPrompt({ model, mode, basePrompt }) {
  if (!model?.id || !model?.label || !model?.defaultPurpose) {
    throw new Error("Worker model identity, label, and specialty are required.");
  }
  const contract = MODE_CONTRACTS[mode];
  if (!contract) {
    throw new Error(`Unsupported worker mode: ${mode}`);
  }

  return [
    basePrompt,
    "",
    `Identity: You are ${model.label} (${model.id}).`,
    "When stating your identity, reproduce the exact label and ID above verbatim; do not normalize, rename, or infer a provider.",
    `Primary specialty: ${model.defaultPurpose}.`,
    "Authority: Codex owns the master plan and final verification. Complete only the bounded assignment and report back to Codex.",
    ...contract,
    "Safety: Never request, reveal, or reproduce secrets. Work only from sanitized context supplied by Codex."
  ].join("\n");
}
