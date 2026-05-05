"use client";

// ── WorkspacePrimarySidebar — 72px rail: dashboard home (/), chat (/chat), labs ───
// > Theme palette lives in workspace headers (ThemeStrip) — keep this rail nav-only.
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageCircle,
  Sparkles,
  Zap,
} from "lucide-react";

import { cn } from "@/lib/cn";

const railBtn =
  "flex min-h-[44px] min-w-[44px] touch-manipulation items-center justify-center rounded-xl border border-transparent text-chalk/50 transition hover:border-[color:var(--spirit-border)] hover:bg-white/[0.04] hover:text-chalk/85 active:scale-[0.98]";

const activeRail =
  "border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_12%,transparent)] text-[color:var(--spirit-accent-strong)] shadow-[0_0_20px_-8px_var(--spirit-glow)]";

export function WorkspacePrimarySidebar() {
  const pathname = usePathname() ?? "";
  const homeActive = pathname === "/";
  const chatActive = pathname === "/chat" || pathname.startsWith("/chat/");
  const oracleActive = pathname.startsWith("/oracle");

  const railNav = (
    <>
      <Link
        href="/"
        className={cn(
          railBtn,
          homeActive && activeRail,
        )}
        aria-current={homeActive ? "page" : undefined}
        aria-label="Dashboard home"
        title="Dashboard"
      >
        <LayoutDashboard className="h-5 w-5" aria-hidden strokeWidth={2} />
      </Link>
      <Link
        href="/chat"
        className={cn(railBtn, chatActive && activeRail)}
        aria-current={chatActive ? "page" : undefined}
        aria-label="Chat workspace"
        title="Saved chat (/chat)"
      >
        <MessageCircle className="h-5 w-5" aria-hidden strokeWidth={2} />
      </Link>
      <Link
        href="/oracle"
        className={cn(railBtn, oracleActive && activeRail)}
        aria-current={oracleActive ? "page" : undefined}
        aria-label="Oracle"
        title="/oracle lane"
      >
        <Sparkles className="h-5 w-5" aria-hidden strokeWidth={2} />
      </Link>
    </>
  );

  return (
    <>
      <aside
        className="relative z-40 hidden h-full w-[72px] shrink-0 flex-col overflow-hidden border-r border-[color:var(--spirit-border)] bg-white/[0.03] backdrop-blur-xl lg:flex"
        aria-label="Spirit workspace navigation"
      >
        <div className="flex min-h-[52px] shrink-0 items-center justify-center border-b border-[color:var(--spirit-border)] py-2">
          <Link
            href="/"
            aria-label="Spirit OS home"
            title="Spirit OS dashboard"
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-full border border-violet-500/35 bg-white/[0.04] shadow-[0_0_28px_-6px_var(--spirit-glow)] transition hover:brightness-110 active:scale-[0.96]",
              homeActive &&
                "border-[color:color-mix(in_oklab,var(--spirit-accent)_58%,transparent)] shadow-[0_0_34px_-6px_var(--spirit-glow)]",
            )}
            aria-current={homeActive ? "page" : undefined}
          >
            <Zap className="h-4 w-4 text-[color:var(--spirit-accent-strong)]" aria-hidden />
          </Link>
        </div>
        <nav
          className="flex flex-1 flex-col items-center gap-2 p-2 pt-3"
          aria-label="Primary"
        >
          {railNav}
        </nav>
        <div className="mt-auto flex shrink-0 flex-col items-center border-t border-[color:var(--spirit-border)] p-2 pb-3">
          <p className="select-none text-center font-mono text-[7px] uppercase leading-tight tracking-[0.2em] text-chalk/32">
            Spirit
          </p>
        </div>
      </aside>

      <nav
        className={cn(
          "fixed inset-x-0 bottom-0 z-40 lg:hidden",
          "flex items-center justify-around gap-0.5 border-t border-[color:var(--spirit-border)]",
          "bg-[color:color-mix(in_oklab,var(--spirit-bg)_82%,transparent)] px-1 pb-[env(safe-area-inset-bottom,0px)] pt-2 backdrop-blur-2xl",
          "shadow-[0_-14px_40px_-26px_var(--spirit-glow)]",
        )}
        aria-label="Workspace navigation"
      >
        <Link
          href="/"
          className={cn(railBtn, "rounded-2xl", homeActive && activeRail)}
          aria-current={homeActive ? "page" : undefined}
          aria-label="Dashboard home"
          title="Dashboard"
        >
          <LayoutDashboard className="h-6 w-6" aria-hidden />
        </Link>
        <Link
          href="/chat"
          className={cn(railBtn, "rounded-2xl", chatActive && activeRail)}
          aria-current={chatActive ? "page" : undefined}
          aria-label="Chat"
          title="Chat"
        >
          <MessageCircle className="h-6 w-6" aria-hidden />
        </Link>
        <Link
          href="/oracle"
          className={cn(railBtn, "rounded-2xl", oracleActive && activeRail)}
          aria-label="Oracle"
          title="Oracle"
        >
          <Sparkles className="h-6 w-6" aria-hidden />
        </Link>
      </nav>
    </>
  );
}
