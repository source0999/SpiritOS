"use client";

// ── TaskbarRail — stage switcher (desktop + mobile) ──────────────────────────
// > Client leaf: only onClick + aria. TASKBAR config lives in stageTypes.ts
// > Buttons floor at min 44×44 — mobile tab bar stacking uses parent linkWrap sizing
import { cn } from "@/lib/cn";
import { TASKBAR, type StageId } from "@/components/dashboard/stageTypes";

export type TaskbarRailProps = {
  stage: StageId;
  setStage: (s: StageId) => void;
  className?: string;
  linkWrap: string;
  tooltips?: boolean;
};

export function TaskbarRail({
  stage,
  setStage,
  className,
  linkWrap,
  tooltips,
}: TaskbarRailProps) {
  return (
    <nav className={cn("flex", className)} aria-label="Spirit taskbar">
      {TASKBAR.map(({ id, label, icon: Icon }) => (
        <div key={id} className="group relative shrink-0 lg:w-full">
          <button
            type="button"
            aria-current={stage === id ? "true" : undefined}
            aria-label={label}
            onClick={() => setStage(id)}
            className={cn(
              linkWrap,
              "relative flex min-h-[44px] min-w-[44px] items-center justify-center rounded-xl border border-transparent transition-colors touch-manipulation",
              stage === id
                ? "border-[color:var(--spirit-border)] bg-white/[0.06] shadow-[0_0_28px_-8px_var(--spirit-glow)]"
                : "border-transparent text-chalk/45 hover:border-[color:var(--spirit-border)] hover:bg-white/[0.03] hover:text-chalk/75",
            )}
          >
            {stage === id ? (
              <span
                aria-hidden
                className={cn(
                  "pointer-events-none absolute bg-[color:color-mix(in_oklab,var(--spirit-accent-strong)_65%,transparent)]",
                  "bottom-1 left-1/2 h-px w-8 max-w-[60%] -translate-x-1/2 lg:bottom-auto lg:left-auto lg:right-2 lg:top-1/2 lg:h-9 lg:w-px lg:-translate-y-1/2 lg:translate-x-0",
                )}
              />
            ) : null}
            <Icon
              className={cn(
                "h-5 w-5 shrink-0",
                stage === id ? "text-[color:var(--spirit-accent-strong)]" : "",
              )}
              aria-hidden
            />
          </button>
          {tooltips ? (
            <span className="pointer-events-none absolute left-full top-1/2 z-[100] ml-3 hidden -translate-y-1/2 rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.06] px-2 py-1 font-mono text-xs text-chalk/90 opacity-0 shadow-xl backdrop-blur-xl lg:block lg:opacity-0 lg:transition-opacity lg:group-hover:opacity-100">
              {label}
            </span>
          ) : null}
        </div>
      ))}
    </nav>
  );
}
