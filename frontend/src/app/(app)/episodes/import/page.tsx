"use client";

import { CheckCircle2, FileSpreadsheet, FileUp, Loader2, Rows3, SkipForward } from "lucide-react";
import { useState } from "react";

import { RoleGate } from "@/components/role-gate";
import { ErrorBanner, PageHeader, StatCard } from "@/components/ui";
import { ApiError, apiFetch } from "@/lib/api";

interface ImportReport {
  rows_read: number;
  imported: number;
  skipped: number;
  skipped_by_reason: Record<string, number>;
  errors: { line: number; episode_id: string | null; reason: string; detail: string }[];
  errors_truncated: boolean;
}

const humanize = (reason: string) => reason.replaceAll("_", " ");

export default function ImportPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [report, setReport] = useState<ImportReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function upload() {
    if (!file) return;
    const body = new FormData();
    body.append("file", file);
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
      <PageHeader
        title="Import episodes"
        subtitle="Upload a CSV export from the recording system. Re-uploading the same file is safe: existing episodes are skipped, never duplicated."
      />

      <div className="card space-y-4">
        <label
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            setFile(e.dataTransfer.files[0] ?? null);
          }}
          className={`flex cursor-pointer flex-col items-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition ${
            dragging
              ? "border-brand-500 bg-brand-50"
              : "border-slate-200 hover:border-brand-300 hover:bg-slate-50"
          }`}
        >
          <div className="grid h-12 w-12 place-items-center rounded-full bg-brand-50 text-brand-600">
            {file ? <FileSpreadsheet className="h-6 w-6" /> : <FileUp className="h-6 w-6" />}
          </div>
          <p className="mt-3 text-sm font-semibold text-slate-900">
            {file ? file.name : "Drop a CSV here, or click to browse"}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {file
              ? `${(file.size / 1024).toFixed(1)} KB`
              : "Columns: episode_id, robot_id, task_name, recorded_at, duration_seconds, operator_name, quality"}
          </p>
          <input
            name="file"
            type="file"
            accept=".csv,text/csv"
            className="sr-only"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>
        <div className="flex justify-end">
          <button className="btn-primary" disabled={!file || pending} onClick={upload}>
            {pending && <Loader2 className="h-4 w-4 animate-spin" />}
            {pending ? "Importing…" : "Upload CSV"}
          </button>
        </div>
        <ErrorBanner message={error} />
      </div>

      {report && (
        <div className="mt-8 space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard label="Rows read" value={report.rows_read} icon={Rows3} tone="slate" />
            <StatCard label="Imported" value={report.imported} icon={CheckCircle2} tone="emerald" />
            <StatCard label="Skipped" value={report.skipped} icon={SkipForward} tone="amber" />
          </div>

          {report.errors.length > 0 && (
            <section className="card overflow-hidden p-0">
              <div className="flex flex-wrap items-center gap-2 px-6 py-4">
                <h2 className="mr-auto font-semibold text-slate-900">Skipped rows</h2>
                {Object.entries(report.skipped_by_reason).map(([reason, n]) => (
                  <span
                    key={reason}
                    className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700"
                  >
                    {humanize(reason)} · {n}
                  </span>
                ))}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="table-head">
                    <tr>
                      <th className="py-3 pl-6">Line</th>
                      <th className="py-3">Episode</th>
                      <th className="py-3">Reason</th>
                      <th className="py-3 pr-6">Detail</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {report.errors.map((err) => (
                      <tr key={`${err.line}-${err.reason}`}>
                        <td className="py-2.5 pl-6 text-slate-500 tabular-nums">{err.line}</td>
                        <td className="py-2.5 font-mono text-xs">{err.episode_id ?? "—"}</td>
                        <td className="py-2.5 capitalize">{humanize(err.reason)}</td>
                        <td className="py-2.5 pr-6 text-slate-500">{err.detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {report.errors_truncated && (
                <p className="border-t border-slate-100 px-6 py-3 text-sm text-slate-500">
                  Only the first rows are listed.
                </p>
              )}
            </section>
          )}
        </div>
      )}
    </RoleGate>
  );
}
