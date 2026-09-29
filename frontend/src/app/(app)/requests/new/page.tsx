"use client";

import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useUser } from "@/components/session";
import { ErrorBanner, PageHeader } from "@/components/ui";
import { ApiError, apiFetch } from "@/lib/api";
import type { DatasetRequestDetail } from "@/lib/types";

const TASKS = [
  "pick cup",
  "place cup on shelf",
  "open drawer",
  "fold towel",
  "pour water",
  "stack blocks",
  "wipe table",
];

export default function NewRequestPage() {
  const user = useUser();
  const router = useRouter();
  const [task, setTask] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const today = new Date().toISOString().slice(0, 10);

  if (user.role !== "client") {
    return <ErrorBanner message="Only clients can create dataset requests." />;
  }

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setPending(true);
    setError(null);
    try {
      const created = await apiFetch<DatasetRequestDetail>("/requests", {
        method: "POST",
        body: JSON.stringify({
          task_name: f.get("task_name"),
          episodes_requested: Number(f.get("episodes_requested")),
          deadline: f.get("deadline"),
          notes: (f.get("notes") as string) || null,
        }),
      });
      router.push(`/requests/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the request");
      setPending(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <Link
        href="/requests"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800"
      >
        <ArrowLeft className="h-4 w-4" /> Back to requests
      </Link>
      <PageHeader
        title="New dataset request"
        subtitle="Tell operations what you need. You can track progress and review the delivery here."
      />
      <form onSubmit={onSubmit} className="card space-y-6">
        <div>
          <label htmlFor="task_name" className="label">
            Task
          </label>
          <input
            id="task_name"
            name="task_name"
            required
            maxLength={120}
            className="input"
            placeholder="e.g. pick cup"
            value={task}
            onChange={(e) => setTask(e.target.value)}
          />
          <div className="mt-2 flex flex-wrap gap-1.5">
            {TASKS.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTask(t)}
                className={`rounded-full px-2.5 py-1 text-xs font-medium transition ${
                  task === t
                    ? "bg-brand-600 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
        <div className="grid gap-6 sm:grid-cols-2">
          <div>
            <label htmlFor="episodes_requested" className="label">
              Episodes requested
            </label>
            <input
              id="episodes_requested"
              name="episodes_requested"
              type="number"
              min={1}
              max={100000}
              required
              placeholder="200"
              className="input"
            />
          </div>
          <div>
            <label htmlFor="deadline" className="label">
              Deadline
            </label>
            <input
              id="deadline"
              name="deadline"
              type="date"
              min={today}
              required
              className="input"
            />
          </div>
        </div>
        <div>
          <label htmlFor="notes" className="label">
            Notes <span className="font-normal text-slate-400">(optional)</span>
          </label>
          <textarea
            id="notes"
            name="notes"
            maxLength={2000}
            rows={4}
            className="input"
            placeholder="Anything operations should know: camera angles, objects, lighting…"
          />
        </div>
        <ErrorBanner message={error} />
        <div className="flex justify-end gap-3 border-t border-slate-100 pt-6">
          <Link href="/requests" className="btn-secondary">
            Cancel
          </Link>
          <button type="submit" disabled={pending} className="btn-primary">
            {pending && <Loader2 className="h-4 w-4 animate-spin" />}
            {pending ? "Submitting…" : "Submit request"}
          </button>
        </div>
      </form>
    </div>
  );
}
