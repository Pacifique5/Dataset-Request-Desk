"use client";

import { useState } from "react";

import { ErrorBanner } from "@/components/ui";
import { ApiError, apiFetch } from "@/lib/api";
import type { DatasetRequestDetail, RequestStatus } from "@/lib/types";

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

  return (
    <section className="card space-y-3">
      <div className="flex flex-wrap gap-2">
        {request.allowed_transitions.map((to) => (
          <button
            key={to}
            disabled={pending !== null}
            className={to === "rejected" ? "btn-secondary" : "btn-primary"}
            onClick={() => (to === "rejected" ? setRejecting(true) : move(to))}
          >
            {pending === to ? "Saving…" : label(to)}
          </button>
        ))}
      </div>
      {rejecting && (
        <form
          className="space-y-2"
          onSubmit={(e) => {
            e.preventDefault();
            move("rejected", note);
          }}
        >
          <label className="block text-sm">
            Why are you rejecting this delivery?
            <textarea
              required
              maxLength={2000}
              rows={2}
              className="input mt-1"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
          <div className="flex gap-2">
            <button type="submit" className="btn-primary" disabled={pending !== null}>
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
