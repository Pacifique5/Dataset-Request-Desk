"use client";

import { Check, Loader2, Play, RotateCcw, Truck, X } from "lucide-react";
import { useState } from "react";

import { ErrorBanner } from "@/components/ui";
import { ApiError, apiFetch } from "@/lib/api";
import type { DatasetRequestDetail, RequestStatus } from "@/lib/types";

const ACTION_ICONS: Partial<Record<RequestStatus, typeof Check>> = {
  in_progress: Play,
  delivered: Truck,
  accepted: Check,
  rejected: X,
};

const ACTION_LABELS: Record<RequestStatus, string> = {
  submitted: "Submit",
  in_progress: "Start work",
  delivered: "Mark delivered",
  accepted: "Accept delivery",
  rejected: "Reject delivery",
};

/**
 * Buttons come from the API's `allowed_transitions`, so the UI never offers a move the
 * server would refuse. (The server still enforces it; this is just good UX.)
 */
export function StatusActions({
  request,
  onChanged,
}: {
  request: DatasetRequestDetail;
  onChanged: () => void;
}) {
  const [pending, setPending] = useState<RequestStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rejecting, setRejecting] = useState(false);
  const [note, setNote] = useState("");

  if (request.allowed_transitions.length === 0) return null;

  // Rework after a rejection is labelled differently for clarity.
  const label = (to: RequestStatus) =>
    to === "in_progress" && request.status === "rejected" ? "Start rework" : ACTION_LABELS[to];

  async function move(to: RequestStatus, withNote?: string) {
    setPending(to);
    setError(null);
    try {
      await apiFetch(`/requests/${request.id}/transitions`, {
        method: "POST",
        body: JSON.stringify({ to_status: to, note: withNote || null }),
      });
      setRejecting(false);
      setNote("");
      onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed");
    } finally {
      setPending(null);
    }
  }

  const short = request.episodes_requested - request.episodes_assigned;
  const hint =
    request.status === "delivered"
      ? "Review the assigned episodes below, then accept the delivery or send it back."
      : request.status === "in_progress"
        ? short > 0
          ? `Assign ${short} more episode(s) below, then mark the request delivered.`
          : "All requested episodes are assigned. Mark the request delivered when ready."
        : "Move this request to the next step.";

  return (
    <section className="card space-y-4 border-brand-100 bg-gradient-to-br from-white to-brand-50/40">
      <div>
        <h2 className="font-semibold text-slate-900">Next step</h2>
        <p className="mt-0.5 text-sm text-slate-500">{hint}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {request.allowed_transitions.map((to) => {
          const Icon =
            to === "in_progress" && request.status === "rejected" ? RotateCcw : ACTION_ICONS[to];
          return (
            <button
              key={to}
              disabled={pending !== null || (to === "delivered" && short > 0)}
              title={
                to === "delivered" && short > 0 ? `${short} more episode(s) needed` : undefined
              }
              className={to === "rejected" ? "btn-danger" : "btn-primary"}
              onClick={() => (to === "rejected" ? setRejecting(true) : move(to))}
            >
              {pending === to ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                Icon && <Icon className="h-4 w-4" />
              )}
              {pending === to ? "Saving…" : label(to)}
            </button>
          );
        })}
      </div>
      {rejecting && (
        <form
          className="space-y-3 rounded-xl border border-rose-100 bg-rose-50/50 p-4"
          onSubmit={(e) => {
            e.preventDefault();
            move("rejected", note);
          }}
        >
          <label className="label" htmlFor="reject-note">
            Why are you rejecting this delivery?
          </label>
          <textarea
            id="reject-note"
            required
            maxLength={2000}
            rows={3}
            className="input"
            placeholder="e.g. several episodes are blurry"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <div className="flex gap-2">
            <button type="submit" className="btn-danger" disabled={pending !== null}>
              Confirm rejection
            </button>
            <button type="button" className="btn-secondary" onClick={() => setRejecting(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}
      <ErrorBanner message={error} />
    </section>
  );
}
