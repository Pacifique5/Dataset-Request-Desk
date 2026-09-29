import { Check, RotateCcw } from "lucide-react";

import type { RequestStatus } from "@/lib/types";

const STEPS: { key: RequestStatus; label: string }[] = [
  { key: "submitted", label: "Submitted" },
  { key: "in_progress", label: "In progress" },
  { key: "delivered", label: "Delivered" },
  { key: "accepted", label: "Accepted" },
];

/** Visual position of a request in the workflow; `rejected` sits on the delivery step. */
export function WorkflowStepper({ status }: { status: RequestStatus }) {
  const rejected = status === "rejected";
  const current = rejected ? 2 : STEPS.findIndex((s) => s.key === status);

  return (
    <ol className="grid grid-cols-4 gap-2">
      {STEPS.map((step, i) => {
        const done = i < current || status === "accepted";
        const active = i === current && status !== "accepted";
        const failed = rejected && i === 2;
        return (
          <li key={step.key} className="flex flex-col gap-2">
            <div
              className={`h-1.5 rounded-full ${
                failed ? "bg-rose-400" : done || active ? "bg-brand-500" : "bg-slate-100"
              }`}
            />
            <div className="flex items-center gap-2 text-xs font-medium sm:text-sm">
              <span
                className={`grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs ${
                  failed
                    ? "bg-rose-100 text-rose-600"
                    : done
                      ? "bg-brand-600 text-white"
                      : active
                        ? "bg-brand-100 text-brand-700 ring-2 ring-brand-500"
                        : "bg-slate-100 text-slate-400"
                }`}
              >
                {failed ? (
                  <RotateCcw className="h-3.5 w-3.5" />
                ) : done ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  i + 1
                )}
              </span>
              <span
                className={
                  failed ? "text-rose-700" : done || active ? "text-slate-900" : "text-slate-400"
                }
              >
                {failed ? "Rejected · rework" : step.label}
              </span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
