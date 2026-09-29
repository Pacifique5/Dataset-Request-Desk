"use client";

import { useState } from "react";

import { RoleGate } from "@/components/role-gate";
import { ErrorBanner } from "@/components/ui";
import { ApiError, apiFetch } from "@/lib/api";

interface ImportReport {
  rows_read: number;
  imported: number;
  skipped: number;
  skipped_by_reason: Record<string, number>;
  errors: { line: number; episode_id: string | null; reason: string; detail: string }[];
  errors_truncated: boolean;
}

export default function ImportPage() {
  const [report, setReport] = useState<ImportReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const body = new FormData(e.currentTarget);
    setPending(true);
    setError(null);
    try {
      setReport(await apiFetch<ImportReport>("/episodes/import", { method: "POST", body }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setPending(false);
    }
  }

  return (
    <RoleGate roles={["operator", "admin"]}>
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Import episodes</h1>
        <form onSubmit={onSubmit} className="card flex flex-wrap items-center gap-4">
          <input name="file" type="file" accept=".csv,text/csv" required className="text-sm" />
          <button className="btn-primary" disabled={pending}>
            {pending ? "Importing…" : "Upload CSV"}
          </button>
          <p className="w-full text-sm text-slate-500">
            Safe to re-run: episodes that already exist are skipped, never duplicated.
          </p>
        </form>
        <ErrorBanner message={error} />

        {report && (
          <section className="card space-y-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <Stat label="Rows read" value={report.rows_read} />
              <Stat label="Imported" value={report.imported} />
              <Stat label="Skipped" value={report.skipped} />
            </div>
            {Object.keys(report.skipped_by_reason).length > 0 && (
              <div className="flex flex-wrap gap-2 text-sm">
                {Object.entries(report.skipped_by_reason).map(([reason, n]) => (
                  <span key={reason} className="rounded-full bg-slate-100 px-3 py-1">
                    {reason.replaceAll("_", " ")}: <b>{n}</b>
                  </span>
                ))}
              </div>
            )}
            {report.errors.length > 0 && (
              <table className="w-full text-left text-sm">
                <thead className="border-b border-slate-200 text-slate-500">
                  <tr>
                    <th className="py-2">Line</th>
                    <th className="py-2">Episode</th>
                    <th className="py-2">Reason</th>
                    <th className="py-2">Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {report.errors.map((err) => (
                    <tr key={err.line} className="border-b border-slate-100 last:border-0">
                      <td className="py-1.5">{err.line}</td>
                      <td className="py-1.5 font-mono text-xs">{err.episode_id ?? "—"}</td>
                      <td className="py-1.5">{err.reason.replaceAll("_", " ")}</td>
                      <td className="py-1.5 text-slate-600">{err.detail}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {report.errors_truncated && (
              <p className="text-sm text-slate-500">Only the first rows are listed.</p>
            )}
          </section>
        )}
      </div>
    </RoleGate>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="text-2xl font-semibold">{value}</div>
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
    </div>
  );
}
