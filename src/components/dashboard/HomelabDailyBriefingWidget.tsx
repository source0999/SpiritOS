import { cn } from "@/lib/cn";

interface BriefingItem {
  category: string;
  headline: string;
  time: string;
}

const ITEMS: BriefingItem[] = [
  {
    category: "Local AI",
    headline: "Whisper STT routing stable — no restarts in 48h.",
    time: "demo",
  },
  {
    category: "Homelab",
    headline: "Tesla P40 standby — PSU upgrade queued, ETA TBD.",
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
    "text-[color:var(--spirit-accent-strong)] border-[color:color-mix(in_oklab,var(--spirit-accent)_40%,transparent)]",
  Homelab: "text-blue-300/80 border-blue-500/30",
  Storage: "text-amber-300/75 border-amber-500/30",
  Energy: "text-emerald-300/75 border-emerald-500/30",
};

interface Props {
  className?: string;
}

export function HomelabDailyBriefingWidget({ className }: Props) {
  return (
    <section
      aria-label="Daily Briefing"
      className={cn("homelab-panel p-4 sm:p-5", className)}
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-chalk/48">
            Spirit · Daily Briefing
          </p>
          <h2 className="mt-0.5 font-mono text-[15px] font-semibold uppercase tracking-tight text-chalk">
            Daily Briefing
          </h2>
        </div>
        <span className="shrink-0 rounded-full border border-white/[0.08] bg-white/[0.04] px-2.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-chalk/45">
          Demo
        </span>
      </div>

      <ul className="flex flex-col gap-2">
        {ITEMS.map((item) => (
          <li
            key={item.headline}
            className="flex items-start gap-2.5 rounded-[10px] border border-white/[0.05] bg-white/[0.02] px-3 py-2"
          >
            <span
              className={cn(
                "mt-0.5 shrink-0 rounded border px-1.5 py-0.5 font-mono text-[8.5px] uppercase tracking-widest",
                CATEGORY_STYLE[item.category] ??
                  "text-chalk/45 border-white/[0.1]",
              )}
            >
              {item.category}
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-mono text-[10.5px] leading-snug text-chalk/80">
                {item.headline}
              </p>
              <p className="mt-0.5 font-mono text-[9px] text-chalk/30">{item.time}</p>
            </div>
          </li>
        ))}
      </ul>

      <p className="mt-3 font-mono text-[9.5px] text-chalk/28 leading-relaxed">
        Demo briefing queue — research pipeline pending.
      </p>
    </section>
  );
}
