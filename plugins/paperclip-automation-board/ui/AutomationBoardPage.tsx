import { useMemo, useState } from "react";
import type { PluginPageProps } from "@paperclipai/plugin-sdk/ui";
import { usePluginAction, usePluginData } from "@paperclipai/plugin-sdk/ui";

type TaskRow = {
  task_name: string;
  task_path?: string | null;
  purpose?: string | null;
  schedule_class?: string | null;
  last_run?: string | null;
  silent_ok?: boolean | null;
  silent_reason?: string | null;
  make_silent_allowed?: boolean;
  disable_allowed?: boolean;
  critical?: boolean;
  enabled?: boolean | null;
  state?: string | null;
};

type CatalogPayload = { tasks: TaskRow[]; exported_at_utc?: string };

function formatWhen(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return d.toLocaleString();
}

export function AutomationBoardPage(_props: PluginPageProps) {
  // Use the SDK bridge rather than the scoped HTTP route. The bridge carries the
  // host's company context, which the scoped route cannot resolve for a board
  // actor without a companyResolution declaration (it answers 400).
  const { data: catalog, loading, error: loadError, refresh } = usePluginData<CatalogPayload>("catalog");
  const repairSilent = usePluginAction("repair-silent");
  const repairDisable = usePluginAction("repair-disable");
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  const rows = useMemo(() => catalog?.tasks ?? [], [catalog]);

  async function postRepair(path: string, row: TaskRow, label: string) {
    const ok = window.confirm(`Confirm: ${label} for task "${row.task_name}"?`);
    if (!ok) return;
    const key = `${path}:${row.task_name}`;
    setBusyKey(key);
    setError(null);
    try {
      const action = path === "/repair/silent" ? repairSilent : repairDisable;
      await action({ task_name: row.task_name, task_path: row.task_path ?? undefined });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusyKey(null);
    }
  }

  return (
    <div style={{ padding: 24, display: "grid", gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22 }}>AgentCore Automations</h1>
          <p style={{ margin: "6px 0 0", opacity: 0.75 }}>Silent scheduled-task health for this PC.</p>
        </div>
        <button type="button" onClick={() => void refresh()} disabled={loading}>Refresh</button>
      </div>
      {loadError ? <div style={{ color: "#dc2626" }}>catalog: {loadError.message}</div> : null}
      {error ? <div style={{ color: "#dc2626" }}>{error}</div> : null}
      {loading && !catalog ? <div>Loading catalog…</div> : null}
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
          <thead>
            <tr>
              <th align="left">Purpose</th>
              <th align="left">Schedule</th>
              <th align="left">Last run</th>
              <th align="left">Silent status</th>
              <th align="left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const failed = row.silent_ok === false;
              const silentLabel = row.silent_ok === false
                ? `Not silent${row.silent_reason ? `: ${row.silent_reason}` : ""}`
                : row.silent_ok === true
                  ? "Silent OK"
                  : row.state === "Missing"
                    ? "Missing task"
                    : "Unknown";
              return (
                <tr key={`${row.task_path ?? ""}:${row.task_name}`} style={{ borderTop: "1px solid rgba(127,127,127,0.25)" }}>
                  <td style={{ padding: "10px 8px" }}>
                    <div style={{ fontWeight: 600 }}>{row.purpose ?? row.task_name}</div>
                    <div style={{ fontSize: 12, opacity: 0.7 }}>{row.task_name}{row.critical ? " · critical" : ""}</div>
                  </td>
                  <td style={{ padding: "10px 8px" }}>{row.schedule_class ?? "—"}</td>
                  <td style={{ padding: "10px 8px" }}>{formatWhen(row.last_run)}</td>
                  <td style={{ padding: "10px 8px", color: failed ? "#dc2626" : undefined, fontWeight: failed ? 600 : undefined }}>{silentLabel}</td>
                  <td style={{ padding: "10px 8px", display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {row.make_silent_allowed ? (
                      <button
                        type="button"
                        disabled={busyKey != null}
                        onClick={() => void postRepair("/repair/silent", row, "Make silent again")}
                      >
                        Make silent again
                      </button>
                    ) : null}
                    {row.disable_allowed ? (
                      <button
                        type="button"
                        disabled={busyKey != null}
                        onClick={() => void postRepair("/repair/disable", row, "Disable task")}
                      >
                        Disable
                      </button>
                    ) : null}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
