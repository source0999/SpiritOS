"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, MessageCircle, Sparkles, Zap } from "lucide-react";

import { cn } from "@/lib/cn";

const railBtn =
  "flex min-h-[44px] min-w-[44px] touch-manipulation items-center justify-center rounded-xl border border-transparent text-chalk/45 transition-all duration-200 hover:border-[color:var(--spirit-border)] hover:bg-white/[0.06] hover:text-chalk/90 active:scale-[0.97]";

const activeRailBtn =
  "border-[color:color-mix(in_oklab,var(--spirit-accent)_38%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_11%,transparent)] text-[color:var(--spirit-accent-strong)] shadow-[0_0_24px_-8px_var(--spirit-glow)]";

const mobilePill =
  "flex min-h-[44px] min-w-[44px] touch-manipulation items-center justify-center rounded-full border border-transparent text-chalk/45 transition-all duration-200 hover:bg-white/[0.07] hover:text-chalk/90 active:scale-[0.97]";

const activeMobilePill =
  "bg-[color:color-mix(in_oklab,var(--spirit-accent)_13%,transparent)] text-[color:var(--spirit-accent-strong)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_0_16px_-6px_var(--spirit-glow)]";

export function DashboardInternalSidebar() {
  const pathname = usePathname() ?? "";
  const homeActive = pathname === "/" || pathname === "";
  const chatActive = pathname === "/chat" || pathname.startsWith("/chat/");
  const oracleActive = pathname.startsWith("/oracle");

  return (
    <>
      {/* Desktop: slim internal sidebar (60px) inside the dashboard shell */}
      <aside
        className="relative z-10 hidden h-full w-[60px] shrink-0 flex-col border-r border-[color:color-mix(in_oklab,var(--spirit-glass-border)_32%,transparent)] lg:flex"
        aria-label="Dashboard navigation"
      >
        <div className="flex shrink-0 items-center justify-center border-b border-[color:color-mix(in_oklab,var(--spirit-glass-border)_22%,transparent)] py-3.5">
          <Link
            href="/"
            aria-label="Spirit OS home"
            title="Dashboard home"
            aria-current={homeActive ? "page" : undefined}
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full border bg-white/[0.04] transition-all duration-200 hover:brightness-110 active:scale-[0.96]",
              homeActive
                ? "border-[color:color-mix(in_oklab,var(--spirit-accent)_52%,transparent)] shadow-[0_0_20px_-5px_var(--spirit-glow),inset_0_1px_0_rgba(255,255,255,0.09)]"
                : "border-violet-500/22 shadow-[0_0_12px_-8px_var(--spirit-glow)]",
            )}
          >
            <Zap
              className="h-3.5 w-3.5 text-[color:var(--spirit-accent-strong)]"
              strokeWidth={2.5}
              aria-hidden
            />
          </Link>
        </div>

        <nav
          className="flex flex-1 flex-col items-center gap-2 p-2 pt-3"
          aria-label="Primary"
        >
          <Link
            href="/"
            className={cn(railBtn, homeActive && activeRailBtn)}
            aria-current={homeActive ? "page" : undefined}
            aria-label="Dashboard home"
            title="Dashboard"
          >
            <LayoutDashboard className="h-5 w-5" aria-hidden />
          </Link>
          <Link
            href="/chat"
            className={cn(railBtn, chatActive && activeRailBtn)}
            aria-current={chatActive ? "page" : undefined}
            aria-label="Chat"
            title="Chat"
          >
            <MessageCircle className="h-5 w-5" aria-hidden />
          </Link>
          <Link
            href="/oracle"
            className={cn(railBtn, oracleActive && activeRailBtn)}
            aria-current={oracleActive ? "page" : undefined}
            aria-label="Oracle"
            title="Oracle"
          >
            <Sparkles className="h-5 w-5" aria-hidden />
          </Link>
        </nav>

        <div className="flex shrink-0 flex-col items-center border-t border-[color:color-mix(in_oklab,var(--spirit-glass-border)_18%,transparent)] p-2 pb-3">
          <p className="select-none text-center font-mono text-[7px] uppercase leading-tight tracking-[0.2em] text-chalk/22">
            Spirit
          </p>
        </div>
      </aside>

      {/* Mobile: floating pill dock */}
      <nav
        aria-label="Dashboard navigation"
        className={cn(
          "pointer-events-none fixed inset-x-0 z-40 lg:hidden",
          "bottom-[var(--shell-keyboard-inset,var(--spirit-keyboard-inset,0px))]",
          "flex items-end justify-center",
          "pb-[max(1.125rem,var(--shell-safe-area-bottom,env(safe-area-inset-bottom,0px)))]",
        )}
      >
        <div
          className={cn(
            "pointer-events-auto flex items-center gap-0.5 rounded-full",
            "border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_78%,transparent)]",
            "bg-[color:color-mix(in_oklab,var(--spirit-bg)_88%,transparent)]",
            "px-2 py-2",
            "shadow-[0_8px_40px_-10px_rgba(0,0,0,0.65),0_2px_8px_-4px_rgba(0,0,0,0.30),var(--spirit-nav-glow)]",
            "backdrop-blur-2xl",
          )}
        >
          <Link
            href="/"
            className={cn(mobilePill, homeActive && activeMobilePill)}
            aria-current={homeActive ? "page" : undefined}
            aria-label="Dashboard home"
          >
            <LayoutDashboard className="h-5 w-5 shrink-0" aria-hidden strokeWidth={2} />
          </Link>
          <Link
            href="/chat"
            className={cn(mobilePill, chatActive && activeMobilePill)}
            aria-current={chatActive ? "page" : undefined}
            aria-label="Chat workspace"
          >
            <MessageCircle className="h-5 w-5 shrink-0" aria-hidden strokeWidth={2} />
          </Link>
          <Link
            href="/oracle"
            className={cn(mobilePill, oracleActive && activeMobilePill)}
            aria-current={oracleActive ? "page" : undefined}
            aria-label="Oracle"
          >
            <Sparkles className="h-5 w-5 shrink-0" aria-hidden strokeWidth={2} />
          </Link>
        </div>
      </nav>
    </>
  );
}
