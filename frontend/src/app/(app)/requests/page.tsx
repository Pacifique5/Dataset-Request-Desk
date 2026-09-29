"use client";

import { CheckCircle2, ChevronRight, Clock, Inbox, Plus, Send, Truck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useUser } from "@/components/session";
import {
  EmptyState,
  ErrorBanner,
  PageHeader,
  Progress,
  Spinner,
  StatCard,
  StatusBadge,
  formatDate,
} from "@/components/ui";
import {
  STATUS_LABELS,
  isStaff,
  type DatasetRequest,
  type Page,
  type RequestStatus,
} from "@/lib/types";
import { useApi } from "@/lib/use-api";

const PAGE_SIZE = 20;

/** Totals per status, from the list endpoint's `total` (cheap: limit=1). */
function useStatusTotal(status: RequestStatus) {
  return useApi<Page<DatasetRequest>>(`/requests?status=${status}&limit=1`).data?.total;
}

export default function RequestsPage() {
  const user = useUser();
  const router = useRouter();
  const staff = isStaff(user);
  const [status, setStatus] = useState<RequestStatus | "">("");
  const [offset, setOffset] = useState(0);

  const qs = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
  if (status) qs.set("status", status);
  const { data, error, loading } = useApi<Page<DatasetRequest>>(`/requests?${qs}`);

  const totals = {
    submitted: useStatusTotal("submitted"),
    in_progress: useStatusTotal("in_progress"),
    delivered: useStatusTotal("delivered"),
    accepted: useStatusTotal("accepted"),
  };

  return (
    <>
      <PageHeader
        title={staff ? "All requests" : "My requests"}
        subtitle={
          staff
            ? "Every client request, newest first. Open one to move it forward or assign episodes."
            : "Track your dataset requests and review deliveries."
        }
        actions={
          user.role === "client" && (
            <Link href="/requests/new" className="btn-primary">
              <Plus className="h-4 w-4" /> New request
            </Link>
          )
        }
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Submitted" value={totals.submitted ?? "–"} icon={Send} tone="slate" />
        <StatCard label="In progress" value={totals.in_progress ?? "–"} icon={Clock} tone="amber" />
        <StatCard label="Delivered" value={totals.delivered ?? "–"} icon={Truck} tone="sky" />
        <StatCard
          label="Accepted"
          value={totals.accepted ?? "–"}
          icon={CheckCircle2}
          tone="emerald"
        />
      </div>

      <div className="card overflow-hidden p-0">
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 px-4 py-3">
          {(["", ...Object.keys(STATUS_LABELS)] as (RequestStatus | "")[]).map((s) => (
            <button
              key={s || "all"}
              onClick={() => {
                setStatus(s);
                setOffset(0);
              }}
              className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                status === s
                  ? "bg-brand-600 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {s ? STATUS_LABELS[s] : "All"}
            </button>
          ))}
        </div>

        {error && (
          <div className="p-4">
            <ErrorBanner message={error.message} />
          </div>
        )}
        {!data && !error && <Spinner />}

        {data && data.items.length === 0 && (
          <EmptyState icon={Inbox} title="No requests here">
            {user.role === "client"
              ? "Create your first dataset request to get started."
              : "Nothing matches this filter yet."}
          </EmptyState>
        )}

        {data && data.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className={`w-full text-left text-sm ${loading ? "opacity-60" : ""}`}>
              <thead className="table-head">
                <tr>
                  <th className="px-5 py-3">Request</th>
                  {staff && <th className="px-5 py-3">Client</th>}
                  <th className="px-5 py-3">Episodes</th>
                  <th className="px-5 py-3">Deadline</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="w-8 px-5 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((r) => (
                  <tr
                    key={r.id}
                    onClick={() => router.push(`/requests/${r.id}`)}
                    className="group cursor-pointer transition hover:bg-slate-50/80"
                  >
                    <td className="px-5 py-4">
                      <Link
                        href={`/requests/${r.id}`}
                        className="font-semibold text-slate-900 group-hover:text-brand-700"
                      >
                        #{r.id}
                      </Link>
                      <div className="text-slate-500">{r.task_name}</div>
                    </td>
                    {staff && (
                      <td className="px-5 py-4 text-slate-700">
                        {r.client.organisation ?? r.client.name}
                      </td>
                    )}
                    <td className="px-5 py-4">
                      <Progress done={r.episodes_assigned} total={r.episodes_requested} />
                    </td>
                    <td className="px-5 py-4 text-slate-700">{formatDate(r.deadline)}</td>
                    <td className="px-5 py-4">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="px-5 py-4 text-slate-300 group-hover:text-slate-500">
                      <ChevronRight className="h-4 w-4" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data && data.total > PAGE_SIZE && (
          <div className="flex items-center justify-between border-t border-slate-100 px-5 py-3 text-sm">
            <span className="text-slate-500">
              {offset + 1}–{Math.min(offset + PAGE_SIZE, data.total)} of {data.total}
            </span>
            <div className="flex gap-2">
              <button
                className="btn-secondary px-3 py-1.5"
                disabled={offset === 0 || loading}
                onClick={() => setOffset(offset - PAGE_SIZE)}
              >
                Previous
              </button>
              <button
                className="btn-secondary px-3 py-1.5"
                disabled={offset + PAGE_SIZE >= data.total || loading}
                onClick={() => setOffset(offset + PAGE_SIZE)}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
