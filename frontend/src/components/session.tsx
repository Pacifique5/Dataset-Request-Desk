"use client";

import { createContext, useContext } from "react";

import type { User } from "@/lib/types";

const SessionContext = createContext<User | null>(null);

export function SessionProvider({ user, children }: { user: User; children: React.ReactNode }) {
  return <SessionContext.Provider value={user}>{children}</SessionContext.Provider>;
}

/** The authenticated user. Only usable under the (app) layout, which guarantees one. */
export function useUser(): User {
  const user = useContext(SessionContext);
  if (!user) throw new Error("useUser must be used inside <SessionProvider>");
  return user;
}
