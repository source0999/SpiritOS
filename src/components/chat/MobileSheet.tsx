"use client";

// ── MobileSheet - portal overlay; escapes overflow/transform hell (Prompt 9E-A) ─
import { X } from "lucide-react";
import {
  memo,
  useCallback,
  useEffect,
  useId,
  useState,
} from "react";
import { createPortal } from "react-dom";

import { cn } from "@/lib/cn";

export type MobileSheetSide = "left" | "right" | "bottom";

export type MobileSheetVariant = "panel" | "tray" | "trayCompact";

export type MobileSheetProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  side?: MobileSheetSide;
  className?: string;
  /** `tray` = compact bottom sheet for quick actions (Prompt 9F). */
  variant?: MobileSheetVariant;
};

export const MobileSheet = memo(function MobileSheet({
  open,
  title,
  onClose,
  children,
  side = "bottom",
  className,
  variant = "panel",
}: MobileSheetProps) {
  const [mounted, setMounted] = useState(false);
  const titleId = useId();

  useEffect(() => {
    setMounted(true);
  }, []);

  const onKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (!open) return;
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onKeyDown]);

  // #region agent log
  useEffect(() => {
    if (!open || !mounted) return;
    let cancelled = false;
    const raf = requestAnimationFrame(() => {
      if (cancelled) return;
      const shell = document.querySelector('[data-layout="spirit-workspace"]');
      const portalRoot = document.querySelector("[data-agent-mobile-sheet-root]");
      const shellZ = shell ? getComputedStyle(shell).zIndex : null;
      const portalZ = portalRoot ? getComputedStyle(portalRoot).zIndex : null;
      const nz = (z: string | null) =>
        z === "auto" || z == null ? 0 : Number.parseInt(z, 10) || 0;
      fetch("http://localhost:7530/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "26a808",
        },
        body: JSON.stringify({
          sessionId: "26a808",
          location: "MobileSheet.tsx:stacking",
          message: "mobile_sheet_open_stacking_probe",
          data: {
            shellZIndex: shellZ,
            portalZIndex: portalZ,
            portalNumericallyBelowOrEqualShell:
              nz(portalZ) <= nz(shellZ) && nz(shellZ) > 0,
            shellFound: Boolean(shell),
            portalFound: Boolean(portalRoot),
          },
          timestamp: Date.now(),
          hypothesisId: "H1",
        }),
      }).catch(() => {});
    });
    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
    };
  }, [open, mounted]);
  // #endregion

  if (!mounted || !open) return null;

  const panel =
    side === "left" ? (
      <div
        className={cn(
          "pointer-events-auto absolute inset-y-0 left-0 z-[2] flex w-[min(92vw,360px)] flex-col border-r border-[color:var(--spirit-border)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_98%,black)] shadow-[8px_0_40px_-12px_rgba(0,0,0,0.65)]",
          className,
        )}
      >
        <header className="flex shrink-0 items-center justify-between gap-2 border-b border-white/[0.06] px-3 py-2.5">
          <h2
            id={titleId}
            className="truncate font-mono text-[11px] font-semibold uppercase tracking-[0.18em] text-chalk/70"
          >
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="inline-flex h-9 w-9 shrink-0 touch-manipulation items-center justify-center rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.04] text-chalk/75"
          >
            <X className="h-4 w-4" aria-hidden strokeWidth={2} />
          </button>
        </header>
        <div className="scrollbar-hide min-h-0 flex-1 overflow-y-auto overscroll-y-contain px-1 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-1">
          {children}
        </div>
      </div>
    ) : side === "right" ? (
      <div
        className={cn(
          "pointer-events-auto absolute inset-y-0 right-0 z-[2] flex w-[min(92vw,360px)] flex-col border-l border-[color:var(--spirit-border)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_98%,black)] shadow-[-8px_0_40px_-12px_rgba(0,0,0,0.65)]",
          className,
        )}
      >
        <header className="flex shrink-0 items-center justify-between gap-2 border-b border-white/[0.06] px-3 py-2.5">
          <h2
            id={titleId}
            className="truncate font-mono text-[11px] font-semibold uppercase tracking-[0.18em] text-chalk/70"
          >
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="inline-flex h-9 w-9 shrink-0 touch-manipulation items-center justify-center rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.04] text-chalk/75"
          >
            <X className="h-4 w-4" aria-hidden strokeWidth={2} />
          </button>
        </header>
        <div className="scrollbar-hide min-h-0 flex-1 overflow-y-auto overscroll-y-contain px-1 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-1">
          {children}
        </div>
      </div>
    ) : (
      <div
        className={cn(
          "pointer-events-auto absolute inset-x-0 bottom-0 z-[2] flex flex-col rounded-t-2xl border border-b-0 border-[color:var(--spirit-border)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_98%,black)] shadow-[0_-12px_48px_-8px_rgba(0,0,0,0.55)]",
          variant === "tray"
            ? "max-h-[min(52dvh,420px)] rounded-t-3xl"
            : variant === "trayCompact"
              ? "max-h-[min(45dvh,360px)] rounded-t-2xl"
              : "max-h-[min(70dvh,560px)]",
          className,
        )}
      >
        {variant === "tray" || variant === "trayCompact" ? (
          <div
            className={cn(
              "flex shrink-0 flex-col items-center border-b border-white/[0.06] px-3",
              variant === "trayCompact" ? "pt-1.5 pb-1" : "pt-2 pb-1",
            )}
          >
            <div
              className={cn(
                "mb-1 flex shrink-0 items-center justify-center gap-0.5",
                variant === "trayCompact" ? "min-h-[10px] py-1" : "min-h-[12px]",
              )}
              aria-hidden
            >
              {variant === "trayCompact" ? (
                <span className="grid grid-cols-3 gap-0.5 opacity-40">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <span key={i} className="h-[3px] w-[3px] rounded-full bg-chalk/55" />
                  ))}
                </span>
              ) : (
                <div className="h-1 w-10 shrink-0 rounded-full bg-chalk/25" />
              )}
            </div>
            <div className="flex w-full items-center justify-between gap-2">
              <h2
                id={titleId}
                className={cn(
                  "truncate font-mono font-semibold uppercase tracking-[0.2em] text-chalk/50",
                  variant === "trayCompact"
                    ? "text-[8px] opacity-70"
                    : "text-[9px]",
                )}
              >
                {title}
              </h2>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close"
                className={cn(
                  "inline-flex shrink-0 touch-manipulation items-center justify-center rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.04] text-chalk/75",
                  variant === "trayCompact"
                    ? "h-8 w-8 [&>svg]:h-3 [&>svg]:w-3"
                    : "h-8 w-8 [&>svg]:h-3.5 [&>svg]:w-3.5",
                )}
              >
                <X aria-hidden strokeWidth={2} />
              </button>
            </div>
          </div>
        ) : (
          <header className="flex shrink-0 items-center justify-between gap-2 border-b border-white/[0.06] px-3 py-2.5">
            <h2
              id={titleId}
              className="truncate font-mono text-[11px] font-semibold uppercase tracking-[0.18em] text-chalk/70"
            >
              {title}
            </h2>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="inline-flex h-9 w-9 shrink-0 touch-manipulation items-center justify-center rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.04] text-chalk/75"
            >
              <X className="h-4 w-4" aria-hidden strokeWidth={2} />
            </button>
          </header>
        )}
        <div
          className={cn(
            "scrollbar-hide min-h-0 flex-1 overflow-y-auto overscroll-y-contain px-3 pb-[max(1rem,env(safe-area-inset-bottom))] pt-2",
            (variant === "tray" || variant === "trayCompact") &&
              "px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2",
            variant === "trayCompact" && "pt-1.5",
          )}
        >
          {children}
        </div>
      </div>
    );

  return createPortal(
    <div
      data-agent-mobile-sheet-root
      className="fixed inset-0 z-[80] isolate"
      role="presentation"
    >
      <button
        type="button"
        aria-label="Dismiss"
        className="absolute inset-0 z-[1] bg-black/55 backdrop-blur-[1px]"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="pointer-events-none absolute inset-0 z-[2]"
      >
        {panel}
      </div>
    </div>,
    document.body,
  );
});
