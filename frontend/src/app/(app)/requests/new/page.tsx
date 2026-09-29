"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useUser } from "@/components/session";
import { ErrorBanner } from "@/components/ui";
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
    <form onSubmit={onSubmit} className="card max-w-lg space-y-4">
      <h1 className="text-xl font-semibold">New dataset request</h1>
      <label className="block text-sm">
        Task
        <input
          name="task_name"
          list="tasks"
          required
          maxLength={120}
          className="input mt-1"
          placeholder="e.g. pick cup"
        />
        <datalist id="tasks">
          {TASKS.map((t) => (
            <option key={t} value={t} />
          ))}
        </datalist>
      </label>
      <label className="block text-sm">
        Episodes requested
        <input
          name="episodes_requested"
          type="number"
          min={1}
          max={100000}
          required
          className="input mt-1"
        />
      </label>
      <label className="block text-sm">
        Deadline
        <input name="deadline" type="date" min={today} required className="input mt-1" />
      </label>
      <label className="block text-sm">
        Notes
        <textarea name="notes" maxLength={2000} rows={3} className="input mt-1" />
      </label>
      <ErrorBanner message={error} />
      <button type="submit" disabled={pending} className="btn-primary">
        {pending ? "Submitting…" : "Submit request"}
      </button>
    </form>
  );
}
