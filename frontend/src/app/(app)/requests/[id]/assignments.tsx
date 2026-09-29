"use client";

import { Film, Loader2, Search, Trash2 } from "lucide-react";
import { useState } from "react";

import { useUser } from "@/components/session";
import { EmptyState, ErrorBanner, formatDateTime } from "@/components/ui";
import { ApiError, apiFetch } from "@/lib/api";
import {
  isStaff,
  type AssignmentList,
  type DatasetRequestDetail,
  type Episode,
  type Page,
} from "@/lib/types";
import { useApi } from "@/lib/use-api";

const PAGE_SIZE = 25;

/** Assigned episodes (everyone who can see the request) + the episode picker (staff). */
export function Assignments({
  request,
  onChanged,
}: {
  request: DatasetRequestDetail;
  onChanged: () => void;
}) {
  const user = useUser();
  const editable = isStaff(user) && request.status === "in_progress";
  const assigned = useApi<AssignmentList>(`/requests/${request.id}/assignments`);
  const [error, setError] = useState<string | null>(null);

  async function mutate(action: () => Promise<unknown>) {
    setError(null);
    try {
      await action();
      assigned.reload();
      onChanged();
      return true;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed");
      return false;
    }
  }

  const unassign = (episodeId: string) =>
    mutate(() =>
      apiFetch(`/requests/${request.id}/assignments/${encodeURIComponent(episodeId)}`, {
        method: "DELETE",
      }),
    );

  const assign = (ids: string[]) =>
    mutate(() =>
      apiFetch(`/requests/${request.id}/assignments`, {
        method: "POST",
        body: JSON.stringify({ episode_ids: ids }),
      }),
    );

  const items = assigned.data?.items ?? [];
  if (!editable && items.length === 0) return null;

  return (
    <>
      <section className="card overflow-hidden p-0">
        <div className="flex items-center justify-between px-6 pt-5 pb-4">
          <h2 className="font-semibold text-slate-900">
            Assigned episodes ({items.length}/{request.episodes_requested})
          </h2>
        </div>
        <div className="px-6">
          <ErrorBanner message={error ?? assigned.error?.message} />
        </div>
        {items.length > 0 ? (
          <EpisodeTable
            episodes={items.map((a) => a.episode)}
            action={editable ? { label: "Remove", run: (e) => unassign(e.episode_id) } : undefined}
          />
        ) : (
          <EmptyState icon={Film} title="No episodes assigned yet">
            Pick episodes from the list below.
          </EmptyState>
        )}
      </section>
      {editable && <EpisodePicker defaultTask={request.task_name} onAssign={assign} />}
    </>
  );
}

function EpisodePicker({
  defaultTask,
  onAssign,
}: {
  defaultTask: string;
  onAssign: (ids: string[]) => Promise<boolean>;
}) {
  const [task, setTask] = useState(defaultTask);
  const [quality, setQuality] = useState("");
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [pending, setPending] = useState(false);

  const qs = new URLSearchParams({
    available: "true",
    limit: String(PAGE_SIZE),
    offset: String(offset),
  });
  if (task.trim()) qs.set("task_name", task.trim());
  if (quality) qs.set("quality", quality);
  const { data, error, reload } = useApi<Page<Episode>>(`/episodes?${qs}`);

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function submit() {
    setPending(true);
    if (await onAssign([...selected])) {
      setSelected(new Set());
      reload();
    }
    setPending(false);
  }

  return (
    <section className="card overflow-hidden p-0">
      <div className="flex flex-wrap items-end gap-3 px-6 pt-5 pb-4">
        <div className="mr-auto">
          <h2 className="font-semibold text-slate-900">Available episodes</h2>
          <p className="text-sm text-slate-500">Good or usable, not assigned to any request.</p>
        </div>
        <label className="text-sm">
          <span className="label">Task</span>
          <span className="relative block">
            <Search className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              className="input w-52 pl-9"
              value={task}
              onChange={(e) => {
                setTask(e.target.value);
                setOffset(0);
              }}
            />
          </span>
        </label>
        <label className="text-sm">
          <span className="label">Quality</span>
          <select
            className="input w-40"
            value={quality}
            onChange={(e) => {
              setQuality(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">Good + usable</option>
            <option value="good">Good</option>
            <option value="usable">Usable</option>
          </select>
        </label>
        <button className="btn-primary" disabled={selected.size === 0 || pending} onClick={submit}>
          {pending && <Loader2 className="h-4 w-4 animate-spin" />}
          {pending ? "Assigning…" : `Assign selected (${selected.size})`}
        </button>
      </div>
      {error && (
        <div className="px-6 pb-4">
          <ErrorBanner message={error.message} />
        </div>
      )}
      {data && (
        <>
          {data.total === 0 ? (
            <EmptyState icon={Film} title="No matching episodes">
              Try another task name or quality filter.
            </EmptyState>
          ) : (
            <EpisodeTable episodes={data.items} selected={selected} onToggle={toggle} />
          )}
          <div className="flex items-center justify-end gap-3 border-t border-slate-100 px-6 py-3 text-sm text-slate-500">
            {data.total > 0 &&
              `${offset + 1}–${Math.min(offset + PAGE_SIZE, data.total)} of ${data.total}`}
            <button
              className="btn-secondary px-3 py-1.5"
              disabled={offset === 0}
              onClick={() => setOffset(offset - PAGE_SIZE)}
            >
              Previous
            </button>
            <button
              className="btn-secondary px-3 py-1.5"
              disabled={offset + PAGE_SIZE >= data.total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </section>
  );
}

const QUALITY_STYLES: Record<Episode["quality"], string> = {
  good: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  usable: "bg-amber-50 text-amber-700 ring-amber-200",
  bad: "bg-rose-50 text-rose-700 ring-rose-200",
};

function EpisodeTable({
  episodes,
  selected,
  onToggle,
  action,
}: {
  episodes: Episode[];
  selected?: Set<string>;
  onToggle?: (id: string) => void;
  action?: { label: string; run: (e: Episode) => void };
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="table-head">
          <tr>
            {onToggle && <th className="w-12 py-3 pr-3 pl-6" />}
            <th className={`py-3 ${onToggle ? "" : "pl-6"}`}>Episode</th>
            <th className="py-3">Robot</th>
            <th className="py-3">Task</th>
            <th className="py-3">Recorded</th>
            <th className="py-3">Duration</th>
            <th className="py-3">Quality</th>
            {action && <th className="py-3 pr-6" />}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {episodes.map((e) => {
            const isSelected = selected?.has(e.episode_id) ?? false;
            return (
              <tr
                key={e.episode_id}
                onClick={onToggle ? () => onToggle(e.episode_id) : undefined}
                className={`transition ${onToggle ? "cursor-pointer hover:bg-slate-50" : ""} ${
                  isSelected ? "bg-brand-50/60" : ""
                }`}
              >
                {onToggle && (
                  <td className="py-2.5 pr-3 pl-6">
                    <input
                      type="checkbox"
                      aria-label={`Select ${e.episode_id}`}
                      className="h-4 w-4 rounded border-slate-300 accent-brand-600"
                      checked={isSelected}
                      onClick={(ev) => ev.stopPropagation()}
                      onChange={() => onToggle(e.episode_id)}
                    />
                  </td>
                )}
                <td
                  className={`py-2.5 font-mono text-xs font-medium text-slate-800 ${onToggle ? "" : "pl-6"}`}
                >
                  {e.episode_id}
                </td>
                <td className="py-2.5 text-slate-600">{e.robot_id}</td>
                <td className="py-2.5 text-slate-600">{e.task_name}</td>
                <td className="py-2.5 text-slate-600">{formatDateTime(e.recorded_at)}</td>
                <td className="py-2.5 text-slate-600 tabular-nums">{e.duration_seconds}s</td>
                <td className="py-2.5">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ring-1 ring-inset ${QUALITY_STYLES[e.quality]}`}
                  >
                    {e.quality}
                  </span>
                </td>
                {action && (
                  <td className="py-2.5 pr-6 text-right">
                    <button
                      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-rose-600 hover:bg-rose-50"
                      onClick={() => action.run(e)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      {action.label}
                    </button>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
