// ── DiagnosticRow — compact telemetry stripe (thin grid, no card-per-row nonsense) ─
// > Labels stay editorial-mono caps; hints truncate so URLs don’t own the rail
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export type DiagnosticRowProps = {
  label: string;
  value: ReactNode;
  hint: string;
  className?: string;
};

export function DiagnosticRow({
  label,
  value,
  hint,
  className,
}: DiagnosticRowProps) {
  return (
    <div
      className={cn(
        // Uniform column proportions so the stripe doesn’t “hang” right in a narrow rail
        "grid grid-cols-[minmax(0,5.25rem),minmax(0,1fr)] items-start gap-x-3 gap-y-0.5 py-2",
        className,
      )}
    >
      <dt className="pt-px font-mono text-[9px] font-semibold uppercase leading-tight tracking-[0.12em] text-chalk/38">
        {label}
      </dt>
      <dd className="m-0 min-w-0 text-start">
        <div className="font-mono text-xs leading-snug tracking-tight text-[color:color-mix(in_oklab,var(--spirit-accent-strong)_82%,white)] [&_span]:tracking-tight">
          {value}
        </div>
        <div
          className="mt-px truncate font-mono text-[10px] leading-tight tracking-tight text-chalk/32"
          title={hint !== "…" && hint !== "—" ? hint : undefined}
        >
          {hint}
        </div>
      </dd>
    </div>
  );
}
