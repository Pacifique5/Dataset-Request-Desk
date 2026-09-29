import { redirect } from "next/navigation";

import { AppShell } from "@/components/app-shell";
import { LiveProvider } from "@/components/live";
import { SessionProvider } from "@/components/session";
import { getCurrentUser } from "@/lib/server-api";

/** Every page under (app) requires a valid session, verified against the API. */
export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  return (
    <SessionProvider user={user}>
      <LiveProvider>
        <AppShell>{children}</AppShell>
      </LiveProvider>
    </SessionProvider>
  );
}
