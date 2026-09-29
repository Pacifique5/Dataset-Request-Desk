"use client";

import { useState } from "react";

import { useUser } from "@/components/session";
import { ErrorBanner, formatDateTime } from "@/components/ui";
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
      <section className="card space-y-4">
        <h2 className="font-semibold">
          Assigned episodes ({items.length}/{request.episodes_requested})
        </h2>
        <ErrorBanner message={error ?? assigned.error?.message} />
        {items.length > 0 && (
          <EpisodeTable
            episodes={items.map((a) => a.episode)}
            action={editable ? { label: "Remove", run: (e) => unassign(e.episode_id) } : undefined}
          />
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
    <section className="card space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <h2 className="mr-auto font-semibold">Available episodes</h2>
        <label className="text-sm">
          Task
          <input
            className="input mt-1 w-48"
            value={task}
            onChange={(e) => {
              setTask(e.target.value);
              setOffset(0);
            }}
          />
        </label>
        <label className="text-sm">
          Quality
          <select
            className="input mt-1 w-36"
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
          {pending ? "Assigning…" : `Assign selected (${selected.size})`}
        </button>
      </div>
      <ErrorBanner message={error?.message} />
      {data && (
        <>
          <EpisodeTable episodes={data.items} selected={selected} onToggle={toggle} />
          <div className="flex items-center justify-end gap-3 text-sm text-slate-500">
            {data.total === 0
              ? "No matching episodes."
              : `${offset + 1}–${Math.min(offset + PAGE_SIZE, data.total)} of ${data.total}`}
            <button
              className="btn-secondary"
              disabled={offset === 0}
              onClick={() => setOffset(offset - PAGE_SIZE)}
            >
              Previous
            </button>
            <button
              className="btn-secondary"
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
        <thead className="border-b border-slate-200 text-slate-500">
          <tr>
            {onToggle && <th className="w-8 py-2" />}
            <th className="py-2">Episode</th>
            <th className="py-2">Robot</th>
            <th className="py-2">Task</th>
            <th className="py-2">Recorded</th>
            <th className="py-2">Duration</th>
            <th className="py-2">Quality</th>
            {action && <th className="py-2" />}
          </tr>
        </thead>
        <tbody>
          {episodes.map((e) => (
            <tr key={e.episode_id} className="border-b border-slate-100 last:border-0">
              {onToggle && (
                <td className="py-2">
                  <input
                    type="checkbox"
                    aria-label={`Select ${e.episode_id}`}
                    checked={selected?.has(e.episode_id) ?? false}
                    onChange={() => onToggle(e.episode_id)}
                  />
                </td>
              )}
              <td className="py-2 font-mono text-xs">{e.episode_id}</td>
              <td className="py-2">{e.robot_id}</td>
              <td className="py-2">{e.task_name}</td>
              <td className="py-2">{formatDateTime(e.recorded_at)}</td>
              <td className="py-2">{e.duration_seconds}s</td>
              <td className="py-2 capitalize">{e.quality}</td>
              {action && (
                <td className="py-2 text-right">
                  <button className="text-rose-600 hover:underline" onClick={() => action.run(e)}>
                    {action.label}
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
