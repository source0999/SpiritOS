"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Music2,
  Film,
  FlaskConical,
  Terminal,
  ChevronLeft,
  ChevronRight,
  Zap,
  Menu,
  X,
  Sparkles,
  TerminalSquare,
} from "lucide-react";
import { useOverlayLock } from "@/components/OverlayLockContext";

const NAV_ITEMS = [
  { label: "Dashboard",        icon: LayoutDashboard, href: "/"          },
  { label: "Sovereign Chat",   icon: Terminal,         href: "/chat"      },
  { label: "Oracle",           icon: Sparkles,         href: "/oracle"    },
  { label: "Projects & IDE",    icon: TerminalSquare,   href: "/projects"  },
  { label: "YTM Hub",          icon: Music2,           href: "/ytm"       },
  { label: "Sovereign Cinema", icon: Film,             href: "/cinema"    },
  { label: "Research Lab",     icon: FlaskConical,     href: "/research"  },
];

function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

function isActive(href: string, pathname: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

function LogoMark() {
  return (
    <div className="pointer-events-none flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border border-violet-500/40 bg-violet-500/20">
      <Zap size={14} className="text-violet-400" />
    </div>
  );
}

// Rendered before the flex layout container in AppShell so these fixed nodes
// are direct body-level siblings — no ancestor stacking context can clip them.
export function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { setNavDrawerOpen } = useOverlayLock();

  useEffect(() => {
    setNavDrawerOpen(open);
    return () => { setNavDrawerOpen(false); };
  }, [open, setNavDrawerOpen]);

  useEffect(() => {
    document.documentElement.style.overflow = open ? "hidden" : "";
    return () => { document.documentElement.style.overflow = ""; };
  }, [open]);

  // Close drawer on route change
  useEffect(() => { setOpen(false); }, [pathname]);

  return (
    <>
      {/*
        When open, drawer + backdrop must stack ABOVE this header (z-[99999]).
        Previously backdrop/nav were z-[99997]/[99998], so they painted *below*
        the header and the drawer looked missing or broken on mobile.
      */}
      <header
        className={cn(
          "fixed left-0 right-0 top-0 flex h-[60px] items-center justify-between border-b border-white/10 bg-zinc-950 px-4 md:hidden",
          open ? "z-[99990]" : "z-[99999]",
        )}
      >
        <div className="pointer-events-none flex items-center gap-2.5">
          <LogoMark />
          <span className="text-sm font-semibold tracking-tight text-zinc-100">Spirit OS</span>
        </div>
        <button
          type="button"
          onClick={() => setOpen(true)}
          onTouchEnd={(e) => {
            e.preventDefault(); // iOS WebKit: bypass delayed / dropped synthetic click
            setOpen(!isOpen);
          }}
          aria-label="Open navigation"
          className="relative z-[99999] flex h-11 w-11 cursor-pointer touch-manipulation items-center justify-center rounded-xl border border-white/10 bg-white/5 text-zinc-400 active:bg-white/10"
        >
          <Menu size={18} className="pointer-events-none" aria-hidden />
        </button>
      </header>

      {/*
        Conditional DOM mount — no CSS visibility/opacity toggle.
        Fresh nodes force a synchronous iOS Safari paint on every open.
      */}
      {open && (
        <>
          <div
            role="button"
            tabIndex={0}
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
            onTouchEnd={(e) => {
              e.preventDefault(); // iOS WebKit
              setOpen(false);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                setOpen(false);
              }
            }}
            className="fixed inset-0 z-[99999] cursor-pointer bg-black/80 md:hidden"
          />

          <nav
            aria-label="Mobile navigation"
            className="fixed left-0 top-0 z-[100000] flex h-[100dvh] w-72 transform-gpu flex-col border-r border-white/10 bg-zinc-950 md:hidden"
          >
            <div className="flex h-[60px] flex-shrink-0 items-center justify-between border-b border-white/10 px-4">
              <div className="flex items-center gap-2.5">
                <LogoMark />
                <span className="text-sm font-semibold tracking-tight text-zinc-100">Spirit OS</span>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                onTouchEnd={(e) => {
                  e.preventDefault(); // iOS WebKit
                  setOpen(false);
                }}
                aria-label="Close navigation"
                className="relative flex h-11 w-11 cursor-pointer touch-manipulation items-center justify-center rounded-xl border border-white/10 bg-white/5 text-zinc-400 active:bg-white/10"
              >
                <X size={16} className="pointer-events-none" aria-hidden />
              </button>
            </div>

            <div className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href, pathname);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    onTouchEnd={(e) => {
                      e.preventDefault(); // iOS WebKit: navigate from touch path; avoids ghost-click issues
                      setOpen(false);
                      router.push(item.href);
                    }}
                    className={cn(
                      "flex cursor-pointer touch-manipulation items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                      active
                        ? "bg-white/[0.07] text-zinc-100"
                        : "text-zinc-400 hover:bg-white/5 hover:text-zinc-100",
                    )}
                  >
                    <Icon
                      size={18}
                      className={cn("flex-shrink-0", active ? "text-violet-400" : "")}
                    />
                    <span>{item.label}</span>
                    {active && (
                      <span className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-400" />
                    )}
                  </Link>
                );
              })}
            </div>

            <div className="flex-shrink-0 border-t border-white/10 px-4 py-4">
              <p className="font-mono text-[10px] text-zinc-600">Source · Intuitive Wrld</p>
            </div>
          </nav>
        </>
      )}
    </>
  );
}

export function DesktopSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  // On /chat and /projects the sidebar auto-collapses to an icon-only rail
  // so the workspace gets maximum horizontal room.
  // The manual toggle remains available on all other routes.
  const isRail      = (pathname?.startsWith("/chat") || pathname?.startsWith("/projects") || pathname?.startsWith("/ytm") || pathname?.startsWith("/cinema")) ?? false;
  const isCollapsed = isRail || collapsed;

  // Rail is narrower than the manual-collapse state so the chat workspace
  // gets maximum breathing room.
  const sidebarWidth = isRail ? "68px" : collapsed ? "72px" : "220px";

  return (
    <aside
      style={{
        width: sidebarWidth,
        transition: "width 250ms cubic-bezier(0.4, 0, 0.2, 1)",
      }}
      className="sticky top-0 hidden h-[100dvh] flex-shrink-0 self-start overflow-hidden border-r border-white/10 bg-zinc-950 md:flex md:flex-col"
    >
      {/* ── Logo header ── */}
      <div
        className={cn(
          "flex flex-shrink-0 items-center border-b border-white/10 py-5",
          isCollapsed ? "justify-center px-0" : "gap-3 px-4",
        )}
      >
        <LogoMark />
        <span
          className="overflow-hidden whitespace-nowrap text-sm font-semibold tracking-tight text-zinc-100"
          style={{
            maxWidth: isCollapsed ? "0px" : "160px",
            opacity:  isCollapsed ? 0 : 1,
            transition: "opacity 150ms ease-out, max-width 150ms ease-out",
          }}
        >
          Spirit OS
        </span>
      </div>

      {/* ── Nav items ── */}
      <nav className="flex-1 space-y-1 px-2 py-4">
        {NAV_ITEMS.map((item) => {
          const Icon   = item.icon;
          const active = isActive(item.href, pathname);
          return (
            <a
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex cursor-pointer touch-manipulation items-center rounded-xl py-2.5 text-sm font-medium transition-colors",
                isCollapsed ? "justify-center px-0" : "gap-3 px-3",
                active
                  ? "bg-white/[0.07] text-zinc-100"
                  : "text-zinc-400 hover:bg-white/5 hover:text-zinc-100",
              )}
            >
              {/*
                Active indicator:
                  Rail / collapsed → thin violet bar on the left edge (Discord-style)
                  Expanded         → small violet dot on the right
              */}
              {active && isCollapsed && (
                <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r-full bg-violet-400" />
              )}

              <Icon
                size={18}
                className={cn("flex-shrink-0", active ? "text-violet-400" : "")}
              />

              <span
                className="overflow-hidden whitespace-nowrap"
                style={{
                  maxWidth: isCollapsed ? "0px" : "160px",
                  opacity:  isCollapsed ? 0 : 1,
                  transition: "opacity 150ms ease-out, max-width 150ms ease-out",
                }}
              >
                {item.label}
              </span>

              {/* Hover tooltip shown in collapsed / rail state */}
              {isCollapsed && (
                <span className="pointer-events-none absolute left-14 z-50 whitespace-nowrap rounded-lg border border-white/10 bg-zinc-800 px-2 py-1 text-xs text-zinc-100 opacity-0 transition-opacity group-hover:opacity-100">
                  {item.label}
                </span>
              )}

              {active && !isCollapsed && (
                <span className="ml-auto h-1.5 w-1.5 flex-shrink-0 rounded-full bg-violet-400" />
              )}
            </a>
          );
        })}
      </nav>

      {/*
        Manual collapse toggle — hidden on /chat where the rail
        is driven automatically by the route, not by user preference.
      */}
      {!isRail && (
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          className="relative z-10 mx-3 mb-4 flex h-11 w-11 flex-shrink-0 cursor-pointer touch-manipulation items-center justify-center rounded-xl border border-white/10 bg-white/5 text-zinc-400 transition-colors hover:bg-white/10 hover:text-zinc-100"
        >
          {collapsed ? (
            <ChevronRight size={16} className="pointer-events-none" aria-hidden />
          ) : (
            <ChevronLeft size={16} className="pointer-events-none" aria-hidden />
          )}
        </button>
      )}
    </aside>
  );
}

export function Navigation() {
  return (
    <>
      <MobileNav />
      <DesktopSidebar />
    </>
  );
}
