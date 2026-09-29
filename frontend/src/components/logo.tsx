/** Product mark: three stacked "episode" frames forming a dataset. */
export function LogoMark({ className = "h-9 w-9" }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden>
      <rect width="40" height="40" rx="10" className="fill-brand-600" />
      <rect x="9" y="11" width="22" height="5" rx="2.5" fill="white" opacity="0.45" />
      <rect x="9" y="18" width="22" height="5" rx="2.5" fill="white" opacity="0.7" />
      <rect x="9" y="25" width="14" height="5" rx="2.5" fill="white" />
      <circle cx="28" cy="27.5" r="3" fill="white" />
    </svg>
  );
}

export function Logo({ inverted = false }: { inverted?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <LogoMark />
      <div className="leading-tight">
        <div className={`text-sm font-bold ${inverted ? "text-white" : "text-slate-900"}`}>
          Dataset Request Desk
        </div>
        <div className={`text-xs ${inverted ? "text-indigo-200" : "text-slate-500"}`}>
          Robotics data operations
        </div>
      </div>
    </div>
  );
}
