"use client";

import { ArrowRight, Eye, EyeOff, Loader2, Lock, Mail } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Logo } from "@/components/logo";
import { ApiError, apiFetch } from "@/lib/api";
import type { User } from "@/lib/types";

// Seed accounts are shown for local demos only (NEXT_PUBLIC_DEMO_LOGINS=true).
const DEMO_ACCOUNTS =
  process.env.NEXT_PUBLIC_DEMO_LOGINS === "true"
    ? [
        { label: "Client", email: "client-a@example.com", password: "client123" },
        { label: "Operator", email: "ops1@example.com", password: "ops123" },
        { label: "Admin", email: "admin@example.com", password: "admin123" },
      ]
    : [];

const HIGHLIGHTS = [
  "Request episodes by task, count and deadline",
  "Operators assign quality-checked episodes",
  "Clients review, accept or send back for rework",
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPending(true);
    setError(null);
    try {
      await apiFetch<User>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      router.replace("/requests");
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the server");
      setPending(false);
    }
  }

  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      {/* Brand panel */}
      <section className="relative hidden overflow-hidden bg-brand-900 p-12 text-white lg:flex lg:flex-col">
        <div
          aria-hidden
          className="absolute inset-0 opacity-[0.15] [background-image:linear-gradient(to_right,white_1px,transparent_1px),linear-gradient(to_bottom,white_1px,transparent_1px)] [background-size:40px_40px]"
        />
        <div
          aria-hidden
          className="absolute -top-40 -right-40 h-[32rem] w-[32rem] rounded-full bg-brand-500 opacity-40 blur-3xl"
        />
        <div
          aria-hidden
          className="absolute -bottom-48 -left-24 h-[28rem] w-[28rem] rounded-full bg-fuchsia-500 opacity-20 blur-3xl"
        />
        <div className="relative">
          <Logo inverted />
        </div>
        <div className="relative my-auto max-w-md">
          <h1 className="text-4xl leading-tight font-bold tracking-tight">
            From teleoperation sessions to delivered datasets.
          </h1>
          <p className="mt-4 text-indigo-200">
            One place for clients and operations to track every dataset request, end to end.
          </p>
          <ul className="mt-8 space-y-3">
            {HIGHLIGHTS.map((h) => (
              <li key={h} className="flex items-center gap-3 text-sm text-indigo-100">
                <span className="grid h-6 w-6 place-items-center rounded-full bg-white/10 ring-1 ring-white/20">
                  <ArrowRight className="h-3.5 w-3.5" />
                </span>
                {h}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-xs text-indigo-300">Internal use only</p>
      </section>

      {/* Form */}
      <section className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-10 lg:hidden">
            <Logo />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Welcome back</h2>
          <p className="mt-1 text-sm text-slate-500">Sign in to your account to continue.</p>

          <form onSubmit={onSubmit} className="mt-8 space-y-5">
            <div>
              <label htmlFor="email" className="label">
                Email
              </label>
              <div className="relative">
                <Mail className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  autoComplete="username"
                  placeholder="you@company.com"
                  className="input pl-9"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="input px-9"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute top-1/2 right-2.5 -translate-y-1/2 rounded p-0.5 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {error && (
              <p
                role="alert"
                className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
              >
                {error}
              </p>
            )}

            <button type="submit" disabled={pending} className="btn-primary w-full py-2.5">
              {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {pending ? "Signing in…" : "Sign in"}
            </button>
          </form>

          {DEMO_ACCOUNTS.length > 0 && (
            <div className="mt-10">
              <div className="flex items-center gap-3 text-xs font-medium tracking-wide text-slate-400 uppercase">
                <span className="h-px flex-1 bg-slate-200" />
                Demo accounts
                <span className="h-px flex-1 bg-slate-200" />
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2">
                {DEMO_ACCOUNTS.map((a) => (
                  <button
                    key={a.email}
                    type="button"
                    className="btn-secondary px-2 text-xs"
                    onClick={() => {
                      setEmail(a.email);
                      setPassword(a.password);
                    }}
                  >
                    {a.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
