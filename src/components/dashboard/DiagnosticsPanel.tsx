// ── DiagnosticsPanel — live server-derived rail (RSC + client leaf for polling) ─
// > SpiritDiagnosticsLive owns the only /api/spirit/health poll — never stack SpiritHealthIndicator here.
// > Design language: _blueprints/design_system.md — mono metadata, cyan values
import type { ReactNode } from "react";

import { SpiritDiagnosticsLive } from "@/components/dashboard/SpiritDiagnosticsLive";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { cn } from "@/lib/cn";

export type DiagnosticsPanelProps = {
  className?: string;
  /** Mounted inside WorkspaceDiagnosticsRail — flush column, skip glass card stacking. */
  docked?: boolean;
  /** Rail collapse control — absolutely positioned top-right so it reads as panel chrome, not a stray tab. */
  headerActions?: ReactNode;
};

export function DiagnosticsPanel({
  className,
  docked,
  headerActions,
}: DiagnosticsPanelProps) {
  return (
    <div
      role="complementary"
      className={cn(
        "flex min-h-0 w-full shrink-0 flex-col border-[color:var(--spirit-border)]",
        docked
          ? "h-full min-h-0 flex-1 overflow-hidden border-0 bg-transparent"
          : "glass lg:border-l lg:border-t-0 lg:backdrop-blur-xl",
        className,
      )}
      aria-label="System diagnostics (read-only)"
    >
      <div
        className={cn(
          "shrink-0 border-b border-[color:var(--spirit-border)] px-3 py-2 sm:px-4",
          docked ? "text-left" : "py-2.5 text-center",
          headerActions && "relative min-h-[52px] pr-14 sm:pr-16",
        )}
      >
        {headerActions ? (
          <div className="absolute right-3 top-3 z-10">{headerActions}</div>
        ) : null}
        <SectionLabel className="tracking-[0.26em]">Diagnostics</SectionLabel>
        <p className="mt-0.5 truncate font-mono text-[10px] leading-snug text-chalk/38">
          /api/spirit/health · 20s
        </p>
      </div>
      <div
        className={cn(
          "flex min-h-0 flex-1 flex-col overflow-y-auto p-3 px-4 pb-5 pt-3 sm:p-4 sm:px-5",
          docked && "px-3 pb-4 pt-2",
        )}
      >
        <SpiritDiagnosticsLive />
      </div>
    </div>
  );
}
