"use client";

import { Film, Gauge, Inbox, Timer } from "lucide-react";
import { useState } from "react";

import { RoleGate } from "@/components/role-gate";
import { EmptyState, ErrorBanner, PageHeader, StatCard, StatusBadge } from "@/components/ui";
import { STATUS_LABELS, type RequestStatus } from "@/lib/types";
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

const PRESETS = [
  { label: "7 days", days: 6 },
  { label: "30 days", days: 29 },
  { label: "90 days", days: 89 },
];

export default function AnalyticsPage() {
  const [from, setFrom] = useState(isoDaysAgo(89));
  const [to, setTo] = useState(isoDaysAgo(0));
  const { data, error } = useApi<Analytics>(`/analytics?from=${from}&to=${to}`);

  // Pivot rows into a day × robot grid (the API returns long format).
  const rows = data?.episodes_per_day_per_robot ?? [];
  const robots = [...new Set(rows.map((r) => r.robot_id))].sort();
  const days = new Map<string, Record<string, number>>();
  for (const r of rows) days.set(r.day, { ...days.get(r.day), [r.robot_id]: r.episodes });
  const maxCell = Math.max(1, ...rows.map((r) => r.episodes));
  const totalEpisodes = rows.reduce((n, r) => n + r.episodes, 0);
  const totalRequests = data
    ? Object.values(data.fulfilment.requests_by_status).reduce((a, b) => a + b, 0)
    : 0;
  const maxTask = Math.max(
    1,
    ...(data?.top_tasks_by_good_episodes.map((t) => t.good_episodes) ?? []),
  );

  return (
    <RoleGate roles={["operator", "admin"]}>
      <PageHeader
        title="Analytics"
        subtitle="Recording volume, request fulfilment and the best-covered tasks. Dates are inclusive (UTC)."
        actions={
          <>
            <div className="flex rounded-lg bg-slate-100 p-1">
              {PRESETS.map((p) => {
                const active = from === isoDaysAgo(p.days) && to === isoDaysAgo(0);
                return (
                  <button
                    key={p.label}
                    onClick={() => {
                      setFrom(isoDaysAgo(p.days));
                      setTo(isoDaysAgo(0));
                    }}
                    className={`rounded-md px-3 py-1 text-xs font-semibold transition ${
                      active
                        ? "bg-white text-slate-900 shadow-sm"
                        : "text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    {p.label}
                  </button>
                );
              })}
            </div>
            <input
              type="date"
              aria-label="From"
              className="input w-40"
              value={from}
              max={to}
              onChange={(e) => setFrom(e.target.value)}
            />
            <span className="text-slate-400">→</span>
            <input
              type="date"
              aria-label="To"
              className="input w-40"
              value={to}
              min={from}
              onChange={(e) => setTo(e.target.value)}
            />
          </>
        }
      />
      <ErrorBanner message={error?.message} />

      {data && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Episodes recorded" value={totalEpisodes} icon={Film} />
            <StatCard label="Requests created" value={totalRequests} icon={Inbox} tone="sky" />
            <StatCard
              label="Median time to deliver"
              value={formatDuration(data.fulfilment.median_submitted_to_delivered_seconds)}
              icon={Timer}
              tone="amber"
              hint={`from ${data.fulfilment.delivered_sample_size} delivered request(s)`}
            />
            <StatCard
              label="Accepted"
              value={data.fulfilment.requests_by_status.accepted}
              icon={Gauge}
              tone="emerald"
              hint="requests signed off by clients"
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="card">
              <h2 className="font-semibold text-slate-900">Request fulfilment</h2>
              <p className="text-sm text-slate-500">Requests created in this range, by status.</p>
              <ul className="mt-5 space-y-3">
                {(Object.keys(STATUS_LABELS) as RequestStatus[]).map((s) => {
                  const n = data.fulfilment.requests_by_status[s];
                  return (
                    <li key={s} className="flex items-center gap-3 text-sm">
                      <span className="w-28">
                        <StatusBadge status={s} />
                      </span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-brand-500"
                          style={{ width: `${totalRequests ? (n / totalRequests) * 100 : 0}%` }}
                        />
                      </div>
                      <span className="w-8 text-right font-semibold tabular-nums">{n}</span>
                    </li>
                  );
                })}
              </ul>
            </section>

            <section className="card">
              <h2 className="font-semibold text-slate-900">Top tasks by good episodes</h2>
              <p className="text-sm text-slate-500">Where we have the most high-quality data.</p>
              {data.top_tasks_by_good_episodes.length === 0 ? (
                <EmptyState icon={Film} title="No good episodes in this range" />
              ) : (
                <ol className="mt-5 space-y-3">
                  {data.top_tasks_by_good_episodes.map((t, i) => (
                    <li key={t.task_name} className="text-sm">
                      <div className="mb-1 flex justify-between">
                        <span className="font-medium text-slate-700 capitalize">
                          <span className="mr-2 text-slate-400">{i + 1}.</span>
                          {t.task_name}
                        </span>
                        <b className="tabular-nums">{t.good_episodes}</b>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-brand-500 to-fuchsia-500"
                          style={{ width: `${(t.good_episodes / maxTask) * 100}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </section>
          </div>

          <section className="card overflow-hidden p-0">
            <div className="px-6 pt-5 pb-4">
              <h2 className="font-semibold text-slate-900">Episodes recorded per day, per robot</h2>
              <p className="text-sm text-slate-500">Darker cells mean more episodes that day.</p>
            </div>
            {days.size === 0 ? (
              <EmptyState icon={Film} title="No episodes in this range" />
            ) : (
              <div className="max-h-[32rem] overflow-auto">
                <table className="w-full text-left text-sm">
                  <thead className="table-head sticky top-0">
                    <tr>
                      <th className="py-3 pl-6">Day</th>
                      {robots.map((r) => (
                        <th key={r} className="px-2 py-3 text-center">
                          {r}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[...days.entries()].map(([day, counts]) => (
                      <tr key={day}>
                        <td className="py-1 pl-6 whitespace-nowrap text-slate-600 tabular-nums">
                          {day}
                        </td>
                        {robots.map((r) => {
                          const n = counts[r] ?? 0;
                          return (
                            <td key={r} className="px-2 py-1">
                              <div
                                className="grid h-7 place-items-center rounded-md text-xs font-semibold tabular-nums"
                                style={{
                                  backgroundColor: n
                                    ? `rgba(79, 70, 229, ${0.12 + 0.78 * (n / maxCell)})`
                                    : "#f8fafc",
                                  color: n / maxCell > 0.5 ? "white" : n ? "#312e81" : "#cbd5e1",
                                }}
                              >
                                {n}
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      )}
    </RoleGate>
  );
}
