"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { isStaff } from "@/lib/types";

import { useUser } from "./session";

export function Nav() {
  const user = useUser();
  const pathname = usePathname();
  const router = useRouter();

  const links = [
    { href: "/requests", label: "Requests", show: true },
    { href: "/episodes/import", label: "Import", show: isStaff(user) },
    { href: "/analytics", label: "Analytics", show: isStaff(user) },
    { href: "/admin/users", label: "Users", show: user.role === "admin" },
  ].filter((l) => l.show);

  async function logout() {
    await apiFetch("/auth/logout", { method: "POST" }).catch(() => undefined);
    router.replace("/login");
    router.refresh();
  }

  return (
    <header className="border-b border-slate-200 bg-white">
      <nav className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-3 text-sm">
        <span className="font-semibold">Dataset Request Desk</span>
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={
              pathname.startsWith(l.href)
                ? "font-medium text-slate-900"
                : "text-slate-500 hover:text-slate-900"
            }
          >
            {l.label}
          </Link>
        ))}
        <span className="ml-auto text-slate-500">
          {user.name} · <span className="capitalize">{user.role}</span>
        </span>
        <button
          onClick={logout}
          className="rounded-md border border-slate-300 px-3 py-1 hover:bg-slate-50"
        >
          Log out
        </button>
      </nav>
    </header>
  );
}
