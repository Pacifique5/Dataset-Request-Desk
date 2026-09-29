"use client";

import { useState } from "react";

import { RoleGate } from "@/components/role-gate";
import { useUser } from "@/components/session";
import { ErrorBanner } from "@/components/ui";
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
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Users</h1>
        <ErrorBanner message={actionError ?? error?.message} />
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-slate-500">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Organisation</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {users?.map((u) => {
                const self = u.id === me.id; // the API also refuses self-lockout
                return (
                  <tr key={u.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-3">{u.name}</td>
                    <td className="px-4 py-3">{u.email}</td>
                    <td className="px-4 py-3">{u.organisation ?? "—"}</td>
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
                    <td className="px-4 py-3">
                      <button
                        className="btn-secondary"
                        disabled={self}
                        onClick={() => update(u.id, { is_active: !u.is_active })}
                      >
                        {u.is_active ? "Deactivate" : "Reactivate"}
                      </button>
                      {!u.is_active && <span className="ml-2 text-rose-600">inactive</span>}
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
      <h2 className="font-semibold">Add user</h2>
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
          {pending ? "Creating…" : "Create user"}
        </button>
      </div>
      <ErrorBanner message={error} />
    </form>
  );
}
