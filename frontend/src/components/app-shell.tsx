"use client";

import { BarChart3, FileUp, Inbox, LogOut, Users } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { isStaff } from "@/lib/types";

import { Logo } from "./logo";
import { useUser } from "./session";
import { Avatar } from "./ui";

export function AppShell({ children }: { children: React.ReactNode }) {
  const user = useUser();
  const pathname = usePathname();
  const router = useRouter();

  const links = [
    { href: "/requests", label: "Requests", icon: Inbox, show: true },
    { href: "/episodes/import", label: "Import", icon: FileUp, show: isStaff(user) },
    { href: "/analytics", label: "Analytics", icon: BarChart3, show: isStaff(user) },
    { href: "/admin/users", label: "Users", icon: Users, show: user.role === "admin" },
  ].filter((l) => l.show);

  async function logout() {
    await apiFetch("/auth/logout", { method: "POST" }).catch(() => undefined);
    router.replace("/login");
    router.refresh();
  }

  return (
    <div className="min-h-screen lg:flex">
      <aside className="border-b border-slate-200 bg-white lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-64 lg:shrink-0 lg:flex-col lg:border-r lg:border-b-0">
        <div className="flex items-center justify-between px-5 py-4 lg:py-6">
          <Logo />
        </div>
        <nav className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-1 lg:flex-col lg:pb-0">
          {links.map(({ href, label, icon: Icon }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium whitespace-nowrap transition ${
                  active
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="hidden border-t border-slate-100 p-4 lg:block">
          <div className="flex items-center gap-3">
            <Avatar name={user.name} />
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold text-slate-900">{user.name}</div>
              <div className="text-xs text-slate-500 capitalize">{user.role}</div>
            </div>
            <button
              onClick={logout}
              aria-label="Log out"
              title="Log out"
              className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        {/* Compact user bar on small screens (the sidebar footer is hidden there). */}
        <div className="flex items-center justify-end gap-3 px-6 pt-4 lg:hidden">
          <span className="text-sm text-slate-600">
            {user.name} · <span className="capitalize">{user.role}</span>
          </span>
          <button onClick={logout} className="btn-secondary px-3 py-1.5 text-xs">
            Log out
          </button>
        </div>
        <main className="mx-auto max-w-6xl px-6 py-8 lg:px-10 lg:py-10">{children}</main>
      </div>
    </div>
  );
}
