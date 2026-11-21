import { useCallback, useEffect, useMemo, useState } from "react";
import type { PluginPageProps } from "@paperclipai/plugin-sdk/ui";
import { PLUGIN_ID } from "./constants.js";

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
  const apiBase = `/api/plugins/${PLUGIN_ID}/api`;
  const [catalog, setCatalog] = useState<CatalogPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/catalog`, { credentials: "include" });
      if (!res.ok) throw new Error(`catalog HTTP ${res.status}`);
      setCatalog((await res.json()) as CatalogPayload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load catalog");
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const rows = useMemo(() => catalog?.tasks ?? [], [catalog]);

  async function postRepair(path: string, row: TaskRow, label: string) {
    const ok = window.confirm(`Confirm: ${label} for task "${row.task_name}"?`);
    if (!ok) return;
    const key = `${path}:${row.task_name}`;
    setBusyKey(key);
    setError(null);
    try {
      const res = await fetch(`${apiBase}${path}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_name: row.task_name, task_path: row.task_path ?? undefined }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body?.error ? String(body.error) : `HTTP ${res.status}`);
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
