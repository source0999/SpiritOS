import "./globals.css";
import type { Viewport } from "next";
import { AppShell } from "@/components/AppShell";
import { logDebugSession } from "@/lib/debugSessionLog";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  // #region agent log
  logDebugSession({
    hypothesisId: "D",
    location: "app/layout.tsx:RootLayout",
    message: "RootLayout render (server)",
    data: { childType: typeof children },
  });
  // #endregion
  return (
    <html lang="en" className="dark">
      <AppShell>{children}</AppShell>
    </html>
  );
}
