import "./globals.css";
import type { Viewport } from "next";
import { AppShell } from "@/components/AppShell";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <AppShell>{children}</AppShell>
    </html>
  );
}
