import "server-only";

import { cookies } from "next/headers";

import type { User } from "./types";

const API_URL = process.env.API_URL ?? "http://localhost:8000";

/** Resolve the logged-in user on the server by forwarding the auth cookie to the API. */
export async function getCurrentUser(): Promise<User | null> {
  const cookieHeader = (await cookies()).toString();
  if (!cookieHeader) return null;
  try {
    const res = await fetch(`${API_URL}/auth/me`, {
      headers: { cookie: cookieHeader },
      cache: "no-store",
    });
    return res.ok ? ((await res.json()) as User) : null;
  } catch {
    return null;
  }
}
