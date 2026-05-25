"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useSpiritWorkspaceMobileChrome } from "@/components/dashboard/SpiritWorkspaceMobileChromeContext";
import {
  Code2,
  Film,
  LayoutDashboard,
  MessageCircle,
  Sparkles,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/cn";

const railBtn =
  "flex min-h-[44px] min-w-[44px] touch-manipulation items-center justify-center rounded-xl border border-transparent text-chalk/45 transition-all duration-200 hover:border-[color:var(--spirit-border)] hover:bg-white/[0.06] hover:text-chalk/90 active:scale-[0.97]";

const activeRail =
  "border-[color:color-mix(in_oklab,var(--spirit-accent)_38%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_11%,transparent)] text-[color:var(--spirit-accent-strong)] shadow-[0_0_24px_-8px_var(--spirit-glow)]";

const pillItem =
  "flex min-h-[44px] touch-manipulation items-center justify-center gap-1.5 rounded-full px-4 font-mono text-[9.5px] uppercase tracking-[0.14em] text-chalk/45 transition-all duration-200 hover:bg-white/[0.06] hover:text-chalk/85 active:scale-[0.97]";

const activePillItem =
  "bg-[color:color-mix(in_oklab,var(--spirit-accent)_13%,transparent)] text-[color:var(--spirit-accent-strong)] shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_0_16px_-6px_var(--spirit-glow)]";

export function WorkspacePrimarySidebar() {
  const pathname = usePathname() ?? "";
  const workspaceMobileChrome = useSpiritWorkspaceMobileChrome();
  const hideMobileDockForComposer = workspaceMobileChrome?.composerFocused ?? false;
  const homeActive = pathname === "/";
  const chatActive = pathname === "/chat" || pathname.startsWith("/chat/");
  const codingActive = pathname === "/coding" || pathname.startsWith("/coding/");
  const mediaActive = pathname === "/media" || pathname.startsWith("/media/");
  const oracleActive = pathname.startsWith("/oracle");

  const desktopRailNav = (
    <>
      <Link
        href="/"
        className={cn(railBtn, homeActive && activeRail)}
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
        href="/coding"
        className={cn(railBtn, codingActive && activeRail)}
        aria-current={codingActive ? "page" : undefined}
        aria-label="Source coding"
        title="Source coding (/coding)"
      >
        <Code2 className="h-5 w-5" aria-hidden strokeWidth={2} />
      </Link>
      <Link
        href="/media"
        className={cn(railBtn, mediaActive && activeRail)}
        aria-current={mediaActive ? "page" : undefined}
        aria-label="Media"
        title="Media (/media)"
      >
        <Film className="h-5 w-5" aria-hidden strokeWidth={2} />
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
      {/* ── Desktop sidebar rail ── */}
      <aside
        className="relative z-40 hidden h-full w-[72px] shrink-0 flex-col overflow-hidden border-r border-[color:var(--spirit-border)] bg-white/[0.025] backdrop-blur-xl lg:flex"
        aria-label="Spirit workspace navigation"
      >
        <div className="flex min-h-[52px] shrink-0 items-center justify-center border-b border-[color:var(--spirit-border)] py-2">
          <Link
            href="/"
            aria-label="Spirit OS home"
            title="Spirit OS dashboard"
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-full border bg-white/[0.04] transition-all duration-200 hover:brightness-110 active:scale-[0.96]",
              homeActive
                ? "border-[color:color-mix(in_oklab,var(--spirit-accent)_55%,transparent)] shadow-[0_0_28px_-5px_var(--spirit-glow),inset_0_1px_0_rgba(255,255,255,0.10)]"
                : "border-violet-500/28 shadow-[0_0_18px_-8px_var(--spirit-glow)]",
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
          {desktopRailNav}
        </nav>
        <div className="mt-auto flex shrink-0 flex-col items-center border-t border-[color:var(--spirit-border)] p-2 pb-3">
          <p className="select-none text-center font-mono text-[7px] uppercase leading-tight tracking-[0.2em] text-chalk/28">
            Spirit
          </p>
        </div>
      </aside>

      {/* ── Mobile floating dock ── */}
      <nav
        aria-label="Workspace navigation"
        className={cn(
          "pointer-events-none fixed inset-x-0 z-40 lg:hidden",
          "bottom-[var(--shell-keyboard-inset,var(--spirit-keyboard-inset,0px))]",
          chatActive && "max-lg:hidden",
          !chatActive && hideMobileDockForComposer && "max-lg:hidden",
          "flex items-end justify-center",
          "pb-[max(1.125rem,var(--shell-safe-area-bottom,env(safe-area-inset-bottom,0px)))]",
        )}
      >
        <div
          className={cn(
            "pointer-events-auto",
            "flex items-center gap-0.5 rounded-full",
            "border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_78%,transparent)]",
            "bg-[color:color-mix(in_oklab,var(--spirit-bg)_88%,transparent)]",
            "px-2 py-2",
            "shadow-[0_8px_40px_-10px_rgba(0,0,0,0.65),0_2px_8px_-4px_rgba(0,0,0,0.30),var(--spirit-nav-glow)]",
            "backdrop-blur-2xl",
          )}
        >
          <Link
            href="/"
            className={cn(pillItem, homeActive && activePillItem)}
            aria-current={homeActive ? "page" : undefined}
            aria-label="Dashboard home"
          >
            <LayoutDashboard className="h-5 w-5 shrink-0" aria-hidden strokeWidth={2} />
            <span className="hidden sm:inline">Home</span>
          </Link>
          <Link
            href="/chat"
            className={cn(pillItem, chatActive && activePillItem)}
            aria-current={chatActive ? "page" : undefined}
            aria-label="Chat workspace"
          >
            <MessageCircle className="h-5 w-5 shrink-0" aria-hidden strokeWidth={2} />
            <span className="hidden sm:inline">Chat</span>
          </Link>
          <Link
            href="/coding"
            className={cn(pillItem, codingActive && activePillItem)}
            aria-current={codingActive ? "page" : undefined}
            aria-label="Source coding"
          >
            <Code2 className="h-5 w-5 shrink-0" aria-hidden strokeWidth={2} />
            <span className="hidden sm:inline">Source</span>
          </Link>
          <Link
            href="/media"
            className={cn(pillItem, mediaActive && activePillItem)}
            aria-current={mediaActive ? "page" : undefined}
            aria-label="Media"
          >
            <Film className="h-5 w-5 shrink-0" aria-hidden strokeWidth={2} />
            <span className="hidden sm:inline">Media</span>
          </Link>
          <Link
            href="/oracle"
            className={cn(pillItem, oracleActive && activePillItem)}
            aria-current={oracleActive ? "page" : undefined}
            aria-label="Oracle"
          >
            <Sparkles className="h-5 w-5 shrink-0" aria-hidden strokeWidth={2} />
            <span className="hidden sm:inline">Oracle</span>
          </Link>
        </div>
      </nav>
    </>
  );
}
