import type { ReactNode } from "react";
import clsx from "clsx";

// ── LayoutOrchestrator ────────────────────────────────────────────────────
// > Extracted from: _blueprints/design_system.md (Layout Orchestrator Rules)
// > Design language: Cinematic (full-bleed), Editorial (reader), Quarantine (rose)
// RSC — no client hook trapdoors. Modes only shuffle shells; leaves stay dumb.

export type LayoutOrchestratorMode = "cinematic" | "editorial" | "quarantine";

export type LayoutOrchestratorProps = {
  mode?: LayoutOrchestratorMode;
  children: ReactNode;
  /** Extra classes on the outer <main> */
  className?: string;
  /** Extra classes on the inner width constraint / prose column */
  contentClassName?: string;
  /** Cinematic only: skip max-w-6xl wrapper for true full-bleed chaos */
  bleed?: boolean;
};

export function LayoutOrchestrator({
  mode = "cinematic",
  children,
  className,
  contentClassName,
  bleed = false,
}: LayoutOrchestratorProps) {
  const shell = clsx(
    "w-full",
    mode === "cinematic" &&
      "min-h-dvh bg-void p-6 text-chalk/[0.97] sm:p-8",
    mode === "editorial" &&
      "min-h-dvh bg-void py-8 text-chalk/[0.97] sm:px-6 sm:py-12",
    mode === "quarantine" &&
      "min-h-dvh bg-transparent px-5 py-8 text-chalk/[0.98] sm:px-10 sm:py-12",
    className,
  );

  const inner =
    mode === "editorial" ? (
      <div className="mx-auto w-full max-w-4xl px-4 sm:px-6">
        <div
          className={clsx(
            "mx-auto max-w-3xl py-[var(--spacing-section-y)] leading-[var(--leading-reader)] text-chalk/[0.92] [&_a]:text-cyan [&_a]:underline [&_a]:decoration-cyan/55 [&_a]:underline-offset-4",
            contentClassName,
          )}
        >
          {children}
        </div>
      </div>
    ) : mode === "quarantine" ? (
      <div className={clsx("mx-auto w-full max-w-3xl", contentClassName)}>
        {children}
      </div>
    ) : bleed ? (
      <div className={clsx("w-full", contentClassName)}>{children}</div>
    ) : (
      <div className={clsx("mx-auto w-full max-w-6xl", contentClassName)}>
        {children}
      </div>
    );

  return <main className={shell}>{inner}</main>;
}
