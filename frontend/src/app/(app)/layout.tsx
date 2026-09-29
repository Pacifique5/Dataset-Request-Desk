import { redirect } from "next/navigation";

import { Nav } from "@/components/nav";
import { SessionProvider } from "@/components/session";
import { getCurrentUser } from "@/lib/server-api";

/** Every page under (app) requires a valid session, verified against the API. */
export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  return (
    <SessionProvider user={user}>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </SessionProvider>
  );
}
