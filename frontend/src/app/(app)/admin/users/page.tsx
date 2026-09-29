"use client";

import { Loader2, UserPlus } from "lucide-react";
import { useState } from "react";

import { RoleGate } from "@/components/role-gate";
import { useUser } from "@/components/session";
import { Avatar, ErrorBanner, PageHeader } from "@/components/ui";
import { ApiError, apiFetch } from "@/lib/api";
import type { Role, User } from "@/lib/types";
import { useApi } from "@/lib/use-api";

const ROLES: Role[] = ["client", "operator", "admin"];

export default function UsersPage() {
  const me = useUser();
  const { data: users, error, reload } = useApi<User[]>("/users");
  const [actionError, setActionError] = useState<string | null>(null);

  async function update(id: number, patch: Partial<Pick<User, "role" | "is_active">>) {
    setActionError(null);
    try {
      await apiFetch(`/users/${id}`, { method: "PATCH", body: JSON.stringify(patch) });
      reload();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Update failed");
    }
  }

  return (
    <RoleGate roles={["admin"]}>
      <PageHeader
        title="Users"
        subtitle="Create accounts, change roles and deactivate access. Changes apply immediately."
      />
      <div className="space-y-6">
        <ErrorBanner message={actionError ?? error?.message} />
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="table-head">
              <tr>
                <th className="px-6 py-3">User</th>
                <th className="px-4 py-3">Organisation</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-6 py-3 text-right">Access</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users?.map((u) => {
                const self = u.id === me.id; // the API also refuses self-lockout
                return (
                  <tr key={u.id} className={u.is_active ? "" : "bg-slate-50/70"}>
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-3">
                        <Avatar name={u.name} />
                        <div>
                          <div className="font-medium text-slate-900">
                            {u.name}
                            {self && <span className="ml-2 text-xs text-slate-400">(you)</span>}
                          </div>
                          <div className="text-slate-500">{u.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{u.organisation ?? "—"}</td>
                    <td className="px-4 py-3">
                      <select
                        aria-label={`Role for ${u.email}`}
                        className="input w-32"
                        value={u.role}
                        disabled={self}
                        onChange={(e) => update(u.id, { role: e.target.value as Role })}
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>
                            {r}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-6 py-3 text-right">
                      {!u.is_active && (
                        <span className="mr-3 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700 ring-1 ring-rose-200 ring-inset">
                          inactive
                        </span>
                      )}
                      <button
                        className={
                          u.is_active ? "btn-danger px-3 py-1.5" : "btn-secondary px-3 py-1.5"
                        }
                        disabled={self}
                        onClick={() => update(u.id, { is_active: !u.is_active })}
                      >
                        {u.is_active ? "Deactivate" : "Reactivate"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <CreateUser onCreated={reload} />
      </div>
    </RoleGate>
  );
}

function CreateUser({ onCreated }: { onCreated: () => void }) {
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const f = new FormData(form);
    setPending(true);
    setError(null);
    try {
      await apiFetch("/users", {
        method: "POST",
        body: JSON.stringify({
          name: f.get("name"),
          email: f.get("email"),
          password: f.get("password"),
          role: f.get("role"),
          organisation: (f.get("organisation") as string) || null,
        }),
      });
      form.reset();
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create user");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="card space-y-4">
      <div className="flex items-center gap-3">
        <div className="grid h-9 w-9 place-items-center rounded-lg bg-brand-50 text-brand-600">
          <UserPlus className="h-4 w-4" />
        </div>
        <div>
          <h2 className="font-semibold text-slate-900">Add user</h2>
          <p className="text-sm text-slate-500">Clients should have an organisation.</p>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <input name="name" required maxLength={120} placeholder="Name" className="input" />
        <input name="email" type="email" required placeholder="Email" className="input" />
        <input
          name="password"
          type="password"
          required
          minLength={8}
          placeholder="Password (min 8)"
          className="input"
        />
        <select name="role" defaultValue="client" className="input">
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <input
          name="organisation"
          maxLength={120}
          placeholder="Organisation (clients)"
          className="input"
        />
        <button className="btn-primary" disabled={pending}>
          {pending && <Loader2 className="h-4 w-4 animate-spin" />}
          {pending ? "Creating…" : "Create user"}
        </button>
      </div>
      <ErrorBanner message={error} />
    </form>
  );
}
