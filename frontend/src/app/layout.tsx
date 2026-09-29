import type { Metadata } from "next";

// Self-hosted from npm (no network needed at build time, no third-party font requests).
import "@fontsource-variable/inter";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dataset Request Desk",
  description: "Internal platform for robotics dataset requests",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans antialiased">{children}</body>
    </html>
  );
}
