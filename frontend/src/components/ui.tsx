import { AlertCircle, Loader2, type LucideIcon } from "lucide-react";

import { STATUS_LABELS, type RequestStatus } from "@/lib/types";

const STATUS_STYLES: Record<RequestStatus, { pill: string; dot: string }> = {
  submitted: { pill: "bg-slate-100 text-slate-700 ring-slate-200", dot: "bg-slate-400" },
  in_progress: { pill: "bg-amber-50 text-amber-800 ring-amber-200", dot: "bg-amber-500" },
  delivered: { pill: "bg-sky-50 text-sky-800 ring-sky-200", dot: "bg-sky-500" },
  accepted: { pill: "bg-emerald-50 text-emerald-800 ring-emerald-200", dot: "bg-emerald-500" },
  rejected: { pill: "bg-rose-50 text-rose-800 ring-rose-200", dot: "bg-rose-500" },
};

export function StatusBadge({ status }: { status: RequestStatus }) {
  const s = STATUS_STYLES[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ring-1 ring-inset ${s.pill}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
      {STATUS_LABELS[status]}
    </span>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-3">{actions}</div>}
    </div>
  );
}

export function ErrorBanner({ message }: { message: string | null | undefined }) {
  if (!message) return null;
  return (
    <p
      role="alert"
      className="flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700"
    >
      <AlertCircle className="h-4 w-4 shrink-0" />
      {message}
    </p>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  children,
}: {
  icon: LucideIcon;
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center px-6 py-14 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-full bg-brand-50 text-brand-600">
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="mt-4 text-sm font-semibold text-slate-900">{title}</h3>
      {children && <div className="mt-1 max-w-sm text-sm text-slate-500">{children}</div>}
    </div>
  );
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-10 text-sm text-slate-500">
      <Loader2 className="h-4 w-4 animate-spin" /> {label}
    </div>
  );
}

export function StatCard({
  label,
  value,
  icon: Icon,
  tone = "brand",
  hint,
}: {
  label: string;
  value: React.ReactNode;
  icon?: LucideIcon;
  tone?: "brand" | "amber" | "sky" | "emerald" | "rose" | "slate";
  hint?: React.ReactNode;
}) {
  const tones = {
    brand: "bg-brand-50 text-brand-600",
    amber: "bg-amber-50 text-amber-600",
    sky: "bg-sky-50 text-sky-600",
    emerald: "bg-emerald-50 text-emerald-600",
    rose: "bg-rose-50 text-rose-600",
    slate: "bg-slate-100 text-slate-600",
  };
  return (
    <div className="card flex items-start gap-4 p-5">
      {Icon && (
        <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${tones[tone]}`}>
          <Icon className="h-5 w-5" />
        </div>
      )}
      <div className="min-w-0">
        <div className="text-xs font-medium tracking-wide text-slate-500 uppercase">{label}</div>
        <div className="mt-1 text-2xl font-bold tracking-tight text-slate-900 tabular-nums">
          {value}
        </div>
        {hint && <div className="mt-0.5 text-xs text-slate-400">{hint}</div>}
      </div>
    </div>
  );
}

export function Progress({ done, total }: { done: number; total: number }) {
  const pct = Math.min(100, Math.round((done / Math.max(total, 1)) * 100));
  const complete = done >= total;
  return (
    <div className="flex items-center gap-2.5 text-sm text-slate-600">
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full transition-all ${complete ? "bg-emerald-500" : "bg-brand-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="tabular-nums">
        {done}/{total}
      </span>
    </div>
  );
}

export function Avatar({ name, size = "md" }: { name: string; size?: "sm" | "md" }) {
  const initials = name
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
  return (
    <span
      className={`grid shrink-0 place-items-center rounded-full bg-gradient-to-br from-brand-500 to-fuchsia-500 font-bold text-white ${
        size === "sm" ? "h-6 w-6 text-[10px]" : "h-9 w-9 text-xs"
      }`}
    >
      {initials}
    </span>
  );
}

export const formatDateTime = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });

export const formatDate = (isoDate: string) =>
  new Date(`${isoDate}T00:00:00`).toLocaleDateString(undefined, { dateStyle: "medium" });
