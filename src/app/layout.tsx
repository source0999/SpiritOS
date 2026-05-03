import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// ── Fonts: Inter is boring on purpose — it’s legible, neutral, survives PM2 glare. ─
// > Serif/display cosplay belonged in Pinterest, not in your terminal OS shell.
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Spirit OS • Dark Node",
  description: "Sovereign cybernetic extension of the Source",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      data-scroll-behavior="smooth"
      className={`${inter.variable} ${jetbrainsMono.variable}`}
      style={{ backgroundColor: "#090a0f" }}
    >
      <body
        className="min-h-[100dvh] min-h-dvh antialiased"
        style={{ backgroundColor: "#090a0f" }}
      >
        {children}
      </body>
    </html>
  );
}
