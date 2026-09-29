"use client";

import { ArrowLeft, CalendarDays, Building2, Clock3, Layers } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { LiveIndicator, useLiveEvents } from "@/components/live";

import {
  Avatar,
  ErrorBanner,
  Progress,
  Spinner,
  StatusBadge,
  formatDate,
  formatDateTime,
} from "@/components/ui";
import type { DatasetRequestDetail } from "@/lib/types";
import { useApi } from "@/lib/use-api";

import { Assignments } from "./assignments";
import { StatusActions } from "./status-actions";
import { WorkflowStepper } from "./workflow-stepper";

export default function RequestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [version, setVersion] = useState(0);
  // Someone else moved this request or changed its episodes: refetch.
  useLiveEvents(() => setVersion((v) => v + 1), Number(id));
  const { data: req, error, reload } = useApi<DatasetRequestDetail>(`/requests/${id}?v=${version}`);

  if (error)
    return <ErrorBanner message={error.status === 404 ? "Request not found." : error.message} />;
  if (!req) return <Spinner />;

  return (
    <div className="space-y-6">
      <Link
        href="/requests"
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800"
      >
        <ArrowLeft className="h-4 w-4" /> All requests
      </Link>

      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          #{req.id} · <span className="capitalize">{req.task_name}</span>
        </h1>
        <StatusBadge status={req.status} />
        <span className="ml-auto">
          <LiveIndicator />
        </span>
      </div>

      <section className="card">
        <WorkflowStepper status={req.status} />
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Info icon={Building2} label="Client">
          {req.client.organisation ?? req.client.name}
        </Info>
        <Info icon={Layers} label="Episodes">
          <Progress done={req.episodes_assigned} total={req.episodes_requested} />
        </Info>
        <Info icon={CalendarDays} label="Deadline">
          {formatDate(req.deadline)}
        </Info>
        <Info icon={Clock3} label="Created">
          {formatDateTime(req.created_at)}
        </Info>
      </section>

      {req.notes && (
        <section className="card">
          <h2 className="text-xs font-semibold tracking-wide text-slate-500 uppercase">Notes</h2>
          <p className="mt-2 text-sm whitespace-pre-line text-slate-700">{req.notes}</p>
        </section>
      )}

      <StatusActions request={req} onChanged={reload} />

      <Assignments request={req} onChanged={reload} version={version} />

      <section className="card">
        <h2 className="mb-5 font-semibold text-slate-900">History</h2>
        <ol className="relative space-y-6 border-l border-slate-200 pl-6">
          {req.events.map((e, i) => (
            <li key={i} className="relative">
              <span className="absolute top-1 -left-[31px] h-3 w-3 rounded-full border-2 border-white bg-brand-500 ring-2 ring-brand-100" />
              <div className="flex flex-wrap items-center gap-2 text-sm">
                {e.from_status && (
                  <>
                    <StatusBadge status={e.from_status} />
                    <span className="text-slate-400">→</span>
                  </>
                )}
                <StatusBadge status={e.to_status} />
              </div>
              <div className="mt-2 flex items-center gap-2 text-sm text-slate-600">
                <Avatar name={e.changed_by.name} size="sm" />
                <span>
                  <span className="font-medium text-slate-800">{e.changed_by.name}</span>
                  <span className="text-slate-400"> · {formatDateTime(e.changed_at)}</span>
                </span>
              </div>
              {e.note && (
                <blockquote className="mt-2 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600 italic">
                  “{e.note}”
                </blockquote>
              )}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function Info({
  icon: Icon,
  label,
  children,
}: {
  icon: typeof Clock3;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card flex items-start gap-3 p-5">
      <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-500">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0">
        <div className="text-xs font-medium tracking-wide text-slate-500 uppercase">{label}</div>
        <div className="mt-1 text-sm font-medium text-slate-900">{children}</div>
      </div>
    </div>
  );
}
