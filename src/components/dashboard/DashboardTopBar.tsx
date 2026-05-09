import { Zap } from "lucide-react";

import { Clock } from "@/components/dashboard/Clock";
import { ThemeStrip } from "@/components/dashboard/ThemeStrip";

interface Props {
  telemetryLine: string;
  dotClass: string;
}

export function DashboardTopBar({ telemetryLine, dotClass }: Props) {
  return (
    <header className="spirit-dashboard-v2-header-glass sticky top-0 z-20 shrink-0">
      <div className="flex items-center gap-3 px-4 py-2 sm:px-5">
        <div className="flex min-w-0 flex-1 items-center gap-2">
          {/* Brand icon: visible on mobile only (desktop sidebar has the orb) */}
          <div
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_72%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg-soft)_58%,transparent)] lg:hidden"
            aria-hidden
          >
            <Zap className="h-3.5 w-3.5 text-[color:var(--spirit-accent-strong)]" strokeWidth={2} />
          </div>

          <div className="min-w-0">
            <h1 className="truncate font-mono text-sm font-semibold uppercase tracking-tight text-chalk">
              SpiritOS <span className="font-light text-chalk/40">Homelab</span>
            </h1>
            <p className="mt-0.5 hidden font-mono text-[10px] leading-none text-chalk/36 sm:block">
              {telemetryLine}
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          <p className="hidden items-center gap-1.5 font-mono text-[9px] leading-tight text-chalk/30 sm:flex">
            <span className={dotClass} aria-hidden />
            <Clock inline className="text-[9px] text-chalk/30" />
          </p>
          <ThemeStrip />
        </div>
      </div>
    </header>
  );
}
