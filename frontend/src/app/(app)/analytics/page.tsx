"use client";

import { useState } from "react";

import { RoleGate } from "@/components/role-gate";
import { ErrorBanner, StatusBadge } from "@/components/ui";
import type { RequestStatus } from "@/lib/types";
import { useApi } from "@/lib/use-api";

interface Analytics {
  date_from: string;
  date_to: string;
  episodes_per_day_per_robot: { day: string; robot_id: string; episodes: number }[];
  fulfilment: {
    requests_by_status: Record<RequestStatus, number>;
    delivered_sample_size: number;
    median_submitted_to_delivered_seconds: number | null;
  };
  top_tasks_by_good_episodes: { task_name: string; good_episodes: number }[];
}

const isoDaysAgo = (days: number) =>
  new Date(Date.now() - days * 86_400_000).toISOString().slice(0, 10);

function formatDuration(seconds: number | null) {
  if (seconds === null) return "—";
  if (seconds < 3600) return `${Math.max(1, Math.round(seconds / 60))} min`;
  const h = seconds / 3600;
  return h < 48 ? `${h.toFixed(1)} h` : `${(h / 24).toFixed(1)} days`;
}

export default function AnalyticsPage() {
  const [from, setFrom] = useState(isoDaysAgo(60));
  const [to, setTo] = useState(isoDaysAgo(0));
  const { data, error } = useApi<Analytics>(`/analytics?from=${from}&to=${to}`);

  // Pivot rows into a day x robot table (the API returns long format).
  const robots = [...new Set(data?.episodes_per_day_per_robot.map((r) => r.robot_id))].sort();
  const days = new Map<string, Record<string, number>>();
  for (const r of data?.episodes_per_day_per_robot ?? []) {
    days.set(r.day, { ...days.get(r.day), [r.robot_id]: r.episodes });
  }

  return (
    <RoleGate roles={["operator", "admin"]}>
      <div className="space-y-6">
        <div className="flex flex-wrap items-end gap-3">
          <h1 className="mr-auto text-2xl font-semibold">Analytics</h1>
          <label className="text-sm">
            From
            <input
              type="date"
              className="input mt-1"
              value={from}
              max={to}
              onChange={(e) => setFrom(e.target.value)}
            />
          </label>
          <label className="text-sm">
            To
            <input
              type="date"
              className="input mt-1"
              value={to}
              min={from}
              onChange={(e) => setTo(e.target.value)}
            />
          </label>
        </div>
        <ErrorBanner message={error?.message} />

        {data && (
          <>
            <div className="grid gap-6 md:grid-cols-2">
              <section className="card space-y-3">
                <h2 className="font-semibold">Request fulfilment</h2>
                <div className="flex flex-wrap gap-3 text-sm">
                  {Object.entries(data.fulfilment.requests_by_status).map(([s, n]) => (
                    <span key={s} className="flex items-center gap-1.5">
                      <StatusBadge status={s as RequestStatus} /> {n}
                    </span>
                  ))}
                </div>
                <p className="text-sm text-slate-600">
                  Median submitted → delivered:{" "}
                  <b>{formatDuration(data.fulfilment.median_submitted_to_delivered_seconds)}</b>{" "}
                  <span className="text-slate-400">
                    (n = {data.fulfilment.delivered_sample_size})
                  </span>
                </p>
              </section>
              <section className="card">
                <h2 className="mb-3 font-semibold">Top tasks by good episodes</h2>
                <ol className="space-y-1 text-sm">
                  {data.top_tasks_by_good_episodes.map((t) => (
                    <li key={t.task_name} className="flex justify-between">
                      <span>{t.task_name}</span>
                      <b>{t.good_episodes}</b>
                    </li>
                  ))}
                  {data.top_tasks_by_good_episodes.length === 0 && (
                    <li className="text-slate-500">No data.</li>
                  )}
                </ol>
              </section>
            </div>

            <section className="card overflow-x-auto">
              <h2 className="mb-3 font-semibold">Episodes recorded per day, per robot</h2>
              {days.size === 0 ? (
                <p className="text-sm text-slate-500">No episodes in this range.</p>
              ) : (
                <table className="w-full text-left text-sm">
                  <thead className="border-b border-slate-200 text-slate-500">
                    <tr>
                      <th className="py-2">Day</th>
                      {robots.map((r) => (
                        <th key={r} className="py-2 text-right">
                          {r}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[...days.entries()].map(([day, counts]) => (
                      <tr key={day} className="border-b border-slate-100 last:border-0">
                        <td className="py-1.5">{day}</td>
                        {robots.map((r) => (
                          <td key={r} className="py-1.5 text-right tabular-nums">
                            {counts[r] ?? 0}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </>
        )}
      </div>
    </RoleGate>
  );
}
