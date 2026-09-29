import { apiFetch } from "@/lib/api";
import type { HealthResponse } from "@/lib/types";

async function getHealth(): Promise<HealthResponse | null> {
  try {
    return await apiFetch<HealthResponse>("/health");
  } catch {
    return null;
  }
}

export default async function Home() {
  const health = await getHealth();
  const ok = health?.status === "ok";

  return (
    <main className="mx-auto flex max-w-xl flex-col gap-6 px-6 py-24">
      <h1 className="text-3xl font-semibold tracking-tight">Dataset Request Desk</h1>
      <p className="text-slate-600">
        Internal platform for managing robotics dataset requests and episode deliveries.
      </p>
      <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm">
        <span
          aria-hidden
          className={`h-2.5 w-2.5 rounded-full ${ok ? "bg-emerald-500" : "bg-rose-500"}`}
        />
        API: {health ? `${health.status} (database ${health.database})` : "unreachable"}
      </div>
    </main>
  );
}
