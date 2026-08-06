import path from "node:path";

const DOCUMENTATION_EXTENSIONS = new Set([".adoc", ".md", ".mdx", ".rst", ".txt"]);
const DOCUMENTATION_BASENAMES = new Set(["agents", "changelog", "claude", "contributing", "license", "readme"]);
const PROTECTED_BASENAMES = new Set([
  "agents.md",
  "authority_lock.md",
  "blueprint.md",
  "claude.md",
  "context_block.md",
  "doc_authority.md",
  "master_config_and_prompt.md",
  "milestones.md",
  "project_anchor.md"
]);
const APPROVAL_PATTERN = /^AUTH-[0-9]{4}-[0-9]{2}-[0-9]{2}-[A-Z0-9_-]+$/;

function normalizedPath(targetPath) {
  if (typeof targetPath !== "string" || !targetPath.trim()) {
    throw new Error("A target documentation path is required.");
  }
  return targetPath.replaceAll("/", "\\").toLowerCase();
}

function isDocumentationPath(targetPath) {
  const extension = path.extname(targetPath).toLowerCase();
  const basename = path.basename(targetPath, extension).toLowerCase();
  return DOCUMENTATION_EXTENSIONS.has(extension)
    || (!extension && DOCUMENTATION_BASENAMES.has(basename));
}

export function assertCodeWorkerTarget(targetPath) {
  if (isDocumentationPath(targetPath)) {
    throw new Error("Documentation files may be edited only through the documentation maintainer worker.");
  }
}

export function assertDocumentationWorkerTarget({
  targetPath,
  dryRun,
  approvalReference
}) {
  const normalized = normalizedPath(targetPath);
  if (!isDocumentationPath(targetPath)) {
    throw new Error("The documentation maintainer worker requires a documentation file target.");
  }
  if (/(?:^|\\)\.agentcore\\(?:state|decisions|context_index)\.md$/.test(normalized)
      || normalized.endsWith("\\global_state.md")) {
    throw new Error("Generated state projections are projection-worker-only and cannot be edited by the documentation maintainer.");
  }
  if (dryRun) return;

  const basename = path.basename(normalized);
  if (PROTECTED_BASENAMES.has(basename)) {
    if (!APPROVAL_PATTERN.test(approvalReference ?? "")) {
      throw new Error("Protected documentation writes require a valid approval_reference.");
    }
    if (process.env.AGENTCORE_AUTHORITY_CAPABILITY !== "authority_maintainer") {
      throw new Error("Protected documentation writes require the live authority_maintainer capability.");
    }
    if (process.env.AGENTCORE_AUTHORITY_APPROVAL_ID !== approvalReference) {
      throw new Error("Protected documentation approval_reference must match the live authority approval identifier.");
    }
  }
}
