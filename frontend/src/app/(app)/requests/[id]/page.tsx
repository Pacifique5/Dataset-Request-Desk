"use client";

import { useParams } from "next/navigation";

import { ErrorBanner, Progress, StatusBadge, formatDateTime } from "@/components/ui";
import type { DatasetRequestDetail } from "@/lib/types";
import { useApi } from "@/lib/use-api";

import { StatusActions } from "./status-actions";

export default function RequestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: req, error, reload } = useApi<DatasetRequestDetail>(`/requests/${id}`);

  if (error)
    return <ErrorBanner message={error.status === 404 ? "Request not found." : error.message} />;
  if (!req) return <p className="text-slate-500">Loading…</p>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold">
          #{req.id} · {req.task_name}
        </h1>
        <StatusBadge status={req.status} />
      </div>

      <section className="card grid gap-4 text-sm sm:grid-cols-4">
        <Field label="Client">{req.client.organisation ?? req.client.name}</Field>
        <Field label="Episodes">
          <Progress done={req.episodes_assigned} total={req.episodes_requested} />
        </Field>
        <Field label="Deadline">{req.deadline}</Field>
        <Field label="Created">{formatDateTime(req.created_at)}</Field>
        {req.notes && (
          <div className="sm:col-span-4">
            <Field label="Notes">{req.notes}</Field>
          </div>
        )}
      </section>

      <StatusActions request={req} onChanged={reload} />

      <section className="card">
        <h2 className="mb-4 font-semibold">History</h2>
        <ol className="space-y-3 text-sm">
          {req.events.map((e, i) => (
            <li key={i} className="flex flex-wrap items-center gap-2">
              <span className="w-44 text-slate-500">{formatDateTime(e.changed_at)}</span>
              {e.from_status && (
                <>
                  <StatusBadge status={e.from_status} />→
                </>
              )}
              <StatusBadge status={e.to_status} />
              <span className="text-slate-600">by {e.changed_by.name}</span>
              {e.note && <span className="italic text-slate-500">“{e.note}”</span>}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-1">{children}</div>
    </div>
  );
}
