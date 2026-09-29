"use client";

import Link from "next/link";
import { useState } from "react";

import { useUser } from "@/components/session";
import { ErrorBanner, Progress, StatusBadge } from "@/components/ui";
import {
  STATUS_LABELS,
  isStaff,
  type DatasetRequest,
  type Page,
  type RequestStatus,
} from "@/lib/types";
import { useApi } from "@/lib/use-api";

const PAGE_SIZE = 20;

export default function RequestsPage() {
  const user = useUser();
  const [status, setStatus] = useState<RequestStatus | "">("");
  const [offset, setOffset] = useState(0);

  const qs = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
  if (status) qs.set("status", status);
  const { data, error, loading } = useApi<Page<DatasetRequest>>(`/requests?${qs}`);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <h1 className="text-2xl font-semibold">{isStaff(user) ? "All requests" : "My requests"}</h1>
        <select
          aria-label="Filter by status"
          className="input ml-auto w-44"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value as RequestStatus | "");
            setOffset(0);
          }}
        >
          <option value="">All statuses</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        {user.role === "client" && (
          <Link href="/requests/new" className="btn-primary">
            New request
          </Link>
        )}
      </div>

      <ErrorBanner message={error?.message} />

      <div className="card overflow-x-auto p-0">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-slate-500">
            <tr>
              <th className="px-4 py-3">#</th>
              <th className="px-4 py-3">Task</th>
              {isStaff(user) && <th className="px-4 py-3">Client</th>}
              <th className="px-4 py-3">Episodes</th>
              <th className="px-4 py-3">Deadline</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((r) => (
              <tr key={r.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                <td className="px-4 py-3">
                  <Link
                    href={`/requests/${r.id}`}
                    className="font-medium underline-offset-2 hover:underline"
                  >
                    #{r.id}
                  </Link>
                </td>
                <td className="px-4 py-3">{r.task_name}</td>
                {isStaff(user) && (
                  <td className="px-4 py-3">{r.client.organisation ?? r.client.name}</td>
                )}
                <td className="px-4 py-3">
                  <Progress done={r.episodes_assigned} total={r.episodes_requested} />
                </td>
                <td className="px-4 py-3">{r.deadline}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={r.status} />
                </td>
              </tr>
            ))}
            {data?.items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  No requests yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {data && data.total > PAGE_SIZE && (
        <div className="flex items-center justify-end gap-3 text-sm">
          <span className="text-slate-500">
            {offset + 1}–{Math.min(offset + PAGE_SIZE, data.total)} of {data.total}
          </span>
          <button
            className="btn-secondary"
            disabled={offset === 0 || loading}
            onClick={() => setOffset(offset - PAGE_SIZE)}
          >
            Previous
          </button>
          <button
            className="btn-secondary"
            disabled={offset + PAGE_SIZE >= data.total || loading}
            onClick={() => setOffset(offset + PAGE_SIZE)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
