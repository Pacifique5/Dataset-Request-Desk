"use client";

import type { Role } from "@/lib/types";

import { useUser } from "./session";
import { ErrorBanner } from "./ui";

/** UI-only convenience: the API enforces the same rule and returns 403 regardless. */
export function RoleGate({ roles, children }: { roles: Role[]; children: React.ReactNode }) {
  const user = useUser();
  if (!roles.includes(user.role))
    return <ErrorBanner message="You don't have access to this page." />;
  return <>{children}</>;
}
