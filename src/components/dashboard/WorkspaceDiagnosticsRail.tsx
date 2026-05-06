"use client";

// ── WorkspaceDiagnosticsRail - route-scoped collapse memory (no /chat ⇄ / leakage) ─
// > /chat persists under its own LS key; "/" never reads /chat; other lanes use :default.
// > Single chevron lives in the diagnostics header chrome - not a random strip tab.
import { usePathname } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { DiagnosticsPanel } from "@/components/dashboard/DiagnosticsPanel";
import { cn } from "@/lib/cn";

const LS_LEGACY = "spirit:diagnosticsRailCollapsed";
const LS_CHAT = "spirit:diagnosticsRailCollapsed:/chat";
const LS_DASH = "spirit:diagnosticsRailCollapsed:/";
const LS_DEFAULT = "spirit:diagnosticsRailCollapsed:default";

function storageKeyForPath(pathname: string): string {
  if (pathname === "/chat") return LS_CHAT;
  if (pathname === "/") return LS_DASH;
  return LS_DEFAULT;
}

/** Collapsed = narrow ribbon. /chat defaults collapsed; "/" and everything else default expanded. */
function defaultCollapsedForPath(pathname: string): boolean {
  return pathname === "/chat";
}

function readCollapsedFromStorage(pathname: string): boolean {
  if (typeof window === "undefined") return defaultCollapsedForPath(pathname);
  const key = storageKeyForPath(pathname);
  try {
    let raw = window.localStorage.getItem(key);
    // One-time migration: old global key only seeds /chat so we do not poison "/".
    if (raw === null && pathname === "/chat") {
      const legacy = window.localStorage.getItem(LS_LEGACY);
      if (legacy === "true" || legacy === "false") {
        raw = legacy;
        window.localStorage.setItem(LS_CHAT, legacy);
        window.localStorage.removeItem(LS_LEGACY);
      }
    }
    if (raw === "true") return true;
    if (raw === "false") return false;
  } catch {
    /* quota / private mode */
  }
  return defaultCollapsedForPath(pathname);
}

const railToggleBtn =
  "inline-flex h-8 w-8 shrink-0 touch-manipulation items-center justify-center rounded-md " +
  "border border-[color:color-mix(in_oklab,var(--spirit-border)_50%,transparent)] " +
  "bg-white/[0.06] text-chalk/90 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] backdrop-blur-md " +
  "transition hover:bg-white/[0.1] active:scale-[0.97] motion-reduce:transition-none";

function DiagnosticsRailToggle({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={!collapsed}
      aria-controls="spirit-diagnostics-panel"
      aria-label={
        collapsed ? "Expand diagnostics panel" : "Collapse diagnostics panel"
      }
      className={railToggleBtn}
    >
      {collapsed ? (
        <ChevronRight className="h-4 w-4" aria-hidden strokeWidth={2} />
      ) : (
        <ChevronLeft className="h-4 w-4" aria-hidden strokeWidth={2} />
      )}
    </button>
  );
}

export function WorkspaceDiagnosticsRail() {
  const pathname = usePathname() ?? "";

  const [collapsed, setCollapsed] = useState<boolean>(() =>
    defaultCollapsedForPath(pathname),
  );

  useEffect(() => {
    queueMicrotask(() => {
      setCollapsed(readCollapsedFromStorage(pathname));
    });
  }, [pathname]);

  const persist = useCallback((next: boolean) => {
    const key = storageKeyForPath(pathname);
    try {
      window.localStorage.setItem(key, next ? "true" : "false");
    } catch {
      /* ignore */
    }
  }, [pathname]);

  const toggle = useCallback(() => {
    setCollapsed((c) => {
      const next = !c;
      persist(next);
      return next;
    });
  }, [persist]);

  return (
    <aside
      className={cn(
        "relative z-20 hidden h-full min-h-0 shrink-0 flex-col overflow-hidden",
        "border-l border-[color:var(--spirit-border)] bg-white/[0.02] backdrop-blur-xl lg:flex",
        "transition-[width] duration-200 ease-out motion-reduce:transition-none",
        collapsed ? "w-12 items-center pt-3" : "w-[min(320px,100%)]",
      )}
      aria-label="Diagnostics rail"
    >
      {collapsed ? (
        <DiagnosticsRailToggle collapsed onToggle={toggle} />
      ) : (
        <div
          id="spirit-diagnostics-panel"
          className="flex min-h-0 flex-1 flex-col overflow-hidden"
        >
          <DiagnosticsPanel
            docked
            className="min-h-0 flex-1"
            headerActions={
              <DiagnosticsRailToggle collapsed={false} onToggle={toggle} />
            }
          />
        </div>
      )}
    </aside>
  );
}
