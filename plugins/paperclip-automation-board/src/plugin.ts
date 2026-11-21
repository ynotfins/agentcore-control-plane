import { spawnSync } from "node:child_process";
import { definePlugin } from "@paperclipai/plugin-sdk";
import type { PluginApiRequestInput, PluginApiResponse } from "@paperclipai/plugin-sdk";
import { OPS } from "./constants.js";

type RepairBody = { task_name?: string; task_path?: string };

function runPwshFile(file: string, scriptArgs: string[]) {
  const result = spawnSync(
    "pwsh.exe",
    ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", file, ...scriptArgs],
    { encoding: "utf8", windowsHide: true, maxBuffer: 16 * 1024 * 1024 },
  );
  return {
    ok: result.status === 0,
    exitCode: result.status,
    stdout: (result.stdout ?? "").trim(),
    stderr: (result.stderr ?? "").trim(),
  };
}

function redactOutput(text: string): string {
  return text
    .split(/\r?\n/)
    .filter((line) => !/(password|secret|token|apikey|bearer)/i.test(line))
    .join('\n')
    .slice(0, 4000);
}

function asBody(input: unknown): RepairBody {
  if (input && typeof input === "object") return input as RepairBody;
  return {};
}

function loadCatalog() {
  const run = runPwshFile(OPS.exportCatalog, []);
  if (!run.ok) {
    throw new Error(redactOutput(run.stderr || run.stdout) || "catalog_export_failed");
  }
  return JSON.parse(run.stdout);
}

function runRepair(script: string, body: RepairBody) {
  const taskName = String(body.task_name ?? "").trim();
  if (!taskName) throw new Error("task_name_required");
  const args = ["-TaskName", taskName];
  const taskPath = body.task_path != null ? String(body.task_path).trim() : "";
  if (taskPath) args.push("-TaskPath", taskPath);
  const run = runPwshFile(script, args);
  if (!run.ok) throw new Error(redactOutput(run.stderr || run.stdout) || "repair_failed");
  return { ok: true, message: redactOutput(run.stdout) };
}

const plugin = definePlugin({
  async setup(ctx) {
    ctx.data.register("catalog", async () => loadCatalog());
    ctx.actions.register("repair-silent", async (params) => runRepair(OPS.repairSilent, asBody(params)));
    ctx.actions.register("repair-disable", async (params) => runRepair(OPS.repairDisable, asBody(params)));
    ctx.logger.info("AgentCore automation board worker ready");
  },
  async onApiRequest(input: PluginApiRequestInput): Promise<PluginApiResponse> {
    if (input.routeKey === "catalog" && input.method === "GET") {
      try {
        return { status: 200, body: loadCatalog() };
      } catch (err) {
        const message = err instanceof Error ? err.message : "catalog_failed";
        return { status: 500, body: { ok: false, error: message } };
      }
    }
    if (input.routeKey === "repair-silent" && input.method === "POST") {
      try {
        return { status: 200, body: runRepair(OPS.repairSilent, asBody(input.body)) };
      } catch (err) {
        const message = err instanceof Error ? err.message : "repair_failed";
        return { status: 400, body: { ok: false, error: message } };
      }
    }
    if (input.routeKey === "repair-disable" && input.method === "POST") {
      try {
        return { status: 200, body: runRepair(OPS.repairDisable, asBody(input.body)) };
      } catch (err) {
        const message = err instanceof Error ? err.message : "disable_failed";
        return { status: 400, body: { ok: false, error: message } };
      }
    }
    return { status: 404, body: { ok: false, error: "route_not_found" } };
  },
});

export default plugin;
