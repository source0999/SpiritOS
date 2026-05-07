import { ShieldCheck } from "lucide-react";

import { cn } from "@/lib/cn";

interface BriefingItem {
  category: string;
  headline: string;
  time: string;
}

const ITEMS: BriefingItem[] = [
  {
    category: "Local AI",
    headline: "Whisper STT routing stable - no restarts in 48h.",
    time: "demo",
  },
  {
    category: "Homelab",
    headline: "Tesla P40 standby - PSU upgrade queued, ETA TBD.",
    time: "demo",
  },
  {
    category: "Storage",
    headline: "spiritdesktop pool nominal. No SMART alerts active.",
    time: "demo",
  },
  {
    category: "Energy",
    headline: "Cluster draw ~180W avg (demo estimate).",
    time: "demo",
  },
];

const CATEGORY_STYLE: Record<string, string> = {
  "Local AI":
    "text-[color:var(--spirit-accent-strong)] border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)]",
  Homelab: "text-blue-300/80 border-blue-500/35",
  Storage: "text-amber-300/75 border-amber-500/35",
  Energy: "text-emerald-300/75 border-emerald-500/35",
};

interface Props {
  className?: string;
}

export function HomelabDailyBriefingWidget({ className }: Props) {
  return (
    <section
      aria-label="Daily Briefing"
      className={cn(
        "spirit-dashboard-v2-glass flex flex-col p-5 sm:p-7",
        className,
      )}
    >
      <span className="spirit-dashboard-v2-glass__shine-t" aria-hidden />

      <div className="mb-6 flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <div
            className="mt-0.5 shrink-0 rounded-2xl border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_65%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg-soft)_42%,transparent)] p-2"
            aria-hidden
          >
            <ShieldCheck className="h-5 w-5 text-chalk/48" strokeWidth={2} />
          </div>
          <div className="min-w-0">
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-chalk/48">
              Spirit · Daily Briefing
            </p>
            <h2 className="mt-1 font-mono text-[15px] font-semibold uppercase tracking-tight text-chalk">
              Daily Briefing
            </h2>
          </div>
        </div>
        <span className="shrink-0 rounded-full border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_55%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg-soft)_38%,transparent)] px-3 py-1 font-mono text-[9px] uppercase tracking-wider text-chalk/48">
          Demo
        </span>
      </div>

      <ul className="flex flex-col gap-2.5">
        {ITEMS.map((item) => (
          <li
            key={item.headline}
            className={cn(
              "spirit-dashboard-v2-inner-card group border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_55%,transparent)] p-3.5 transition-colors",
              "hover:border-[color:color-mix(in_oklab,var(--spirit-accent)_28%,transparent)]",
            )}
          >
            <div className="mb-2 flex items-center justify-between gap-2">
              <span
                className={cn(
                  "rounded-full border px-2 py-0.5 font-mono text-[8.5px] font-semibold uppercase tracking-widest",
                  CATEGORY_STYLE[item.category] ??
                    "text-chalk/45 border-[color:color-mix(in_oklab,var(--spirit-glass-border)_70%,transparent)]",
                )}
              >
                {item.category}
              </span>
            </div>
            <p className="font-mono text-[10.5px] leading-relaxed text-chalk/80">{item.headline}</p>
            <p className="mt-1.5 font-mono text-[9px] text-chalk/38">{item.time}</p>
          </li>
        ))}
      </ul>

      <p className="mt-5 font-mono text-[9.5px] leading-relaxed text-chalk/38">
        Static demo briefing — not connected to live telemetry.
      </p>
    </section>
  );
}
