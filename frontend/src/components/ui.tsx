import { STATUS_LABELS, type RequestStatus } from "@/lib/types";

const STATUS_STYLES: Record<RequestStatus, string> = {
  submitted: "bg-slate-100 text-slate-700",
  in_progress: "bg-amber-100 text-amber-800",
  delivered: "bg-sky-100 text-sky-800",
  accepted: "bg-emerald-100 text-emerald-800",
  rejected: "bg-rose-100 text-rose-800",
};

export function StatusBadge({ status }: { status: RequestStatus }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  );
}

export function ErrorBanner({ message }: { message: string | null | undefined }) {
  if (!message) return null;
  return (
    <p
      role="alert"
      className="rounded-md border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700"
    >
      {message}
    </p>
  );
}

export function Progress({ done, total }: { done: number; total: number }) {
  const pct = Math.min(100, Math.round((done / Math.max(total, 1)) * 100));
  return (
    <div className="flex items-center gap-2 text-sm text-slate-600">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full bg-slate-800" style={{ width: `${pct}%` }} />
      </div>
      {done}/{total}
    </div>
  );
}

export const formatDateTime = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
