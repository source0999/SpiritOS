"use client";

// ── DashboardDemoV4FloatingNav - app rail + mobile pill: Dashboard · Chat · Oracle ─────
// > The palette control opens the existing SpiritOS themes without a modal.

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Code2, LayoutDashboard, MessageSquare, Palette, Sparkles } from "lucide-react";

import { DashboardDemoV4ThemePicker } from "@/components/dashboard/demo-v4/DashboardDemoV4ThemePicker";
import { cn } from "@/lib/cn";
import { SPIRIT_PALETTES } from "@/theme/spiritPalettes";
import { useSpiritTheme } from "@/theme/useSpiritTheme";

type NavSpec = {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  match: (pathname: string) => boolean;
};

const NAV: readonly NavSpec[] = [
  {
    href: "/",
    label: "Dashboard",
    icon: LayoutDashboard,
    match: (p) => p === "/" || p === "",
  },
  {
    href: "/chat",
    label: "Chat",
    icon: MessageSquare,
    match: (p) => p === "/chat" || p.startsWith("/chat/"),
  },
  {
    href: "/coding",
    label: "Source",
    icon: Code2,
    match: (p) => p === "/coding" || p.startsWith("/coding/"),
  },
  {
    href: "/oracle",
    label: "Oracle",
    icon: Sparkles,
    match: (p) => p === "/oracle" || p.startsWith("/oracle/"),
  },
];

export type DashboardDemoV4FloatingNavProps = {
  desktopVariant?: "floating" | "full-height";
};

export function DashboardDemoV4FloatingNav({
  desktopVariant = "full-height",
}: DashboardDemoV4FloatingNavProps) {
  const pathname = usePathname() ?? "";
  const { theme } = useSpiritTheme();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const activePaletteIndex = Math.max(
    0,
    SPIRIT_PALETTES.findIndex((palette) => palette.id === theme),
  );
  const activePalette = SPIRIT_PALETTES[activePaletteIndex] ?? SPIRIT_PALETTES[0];
  const activeGradient = activePalette.colors.map((color) => color.hex).join(", ");

  const renderPaletteButton = (surface: "desktop" | "mobile") => (
    <button
      type="button"
      className={cn(
        "dashboard-demo-v4-theme-picker",
        surface === "desktop" && "dashboard-demo-v4-desktop-theme-picker",
        paletteOpen && "dashboard-demo-v4-theme-picker-open",
      )}
      onClick={() => setPaletteOpen(true)}
      title={`Theme: ${activePalette.label}`}
      aria-label={`Open interface theme picker. Current theme: ${activePalette.label}`}
      aria-expanded={paletteOpen}
      aria-haspopup="dialog"
    >
      <span
        className="dashboard-demo-v4-theme-picker-swatch"
        style={{ background: `linear-gradient(135deg, ${activeGradient})` }}
        aria-hidden
      />
      <Palette className="dashboard-demo-v4-theme-picker-icon" aria-hidden />
    </button>
  );

  return (
    <>
      <nav
        className={cn(
          "dashboard-demo-v4-desktop-rail",
          desktopVariant === "full-height" &&
            "dashboard-demo-v4-desktop-rail-full-height",
        )}
        aria-label={
          desktopVariant === "full-height"
            ? "Spirit app desktop navigation"
            : "Dashboard desktop navigation"
        }
      >
        <div className="dashboard-demo-v4-desktop-rail-shell">
          <div className="dashboard-demo-v4-desktop-brand" aria-label="SpiritOS">
            <span className="dashboard-demo-v4-desktop-brand-mark" aria-hidden>
              S
            </span>
            <span className="dashboard-demo-v4-desktop-brand-text">SpiritOS</span>
          </div>

          <div className="dashboard-demo-v4-desktop-nav-list">
            {NAV.map((item) => {
              const active = item.match(pathname);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-label={item.label}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "dashboard-demo-v4-desktop-nav-item",
                    active && "dashboard-demo-v4-desktop-nav-item-active",
                  )}
                >
                  <Icon className="h-[1.15rem] w-[1.15rem]" strokeWidth={2} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>

          <div className="dashboard-demo-v4-desktop-rail-footer">
            <div className="dashboard-demo-v4-theme-picker-wrap">
              {renderPaletteButton("desktop")}
            </div>
          </div>
        </div>
      </nav>

      <nav
        className="dashboard-demo-v4-nav dashboard-demo-v4-mobile-pill-nav"
        aria-label="Dashboard mobile navigation"
      >
        <div className="dashboard-demo-v4-nav-shell">
          {NAV.map((item) => {
            const active = item.match(pathname);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "dashboard-demo-v4-nav-item",
                  active && "dashboard-demo-v4-nav-item-active",
                )}
              >
                <Icon className="h-[1.1rem] w-[1.1rem]" strokeWidth={2} />
                <span className="hidden sm:inline">{item.label}</span>
              </Link>
            );
          })}

          <div className="dashboard-demo-v4-nav-divider" aria-hidden />

          <div className="dashboard-demo-v4-theme-picker-wrap">
            {renderPaletteButton("mobile")}
          </div>
        </div>
      </nav>

      <DashboardDemoV4ThemePicker
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
      />
    </>
  );
}
