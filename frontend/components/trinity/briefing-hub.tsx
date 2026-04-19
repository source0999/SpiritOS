"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

const stories = [
  {
    tag: "Markets",
    title: "Futures lean green after CPI whisper",
    snippet: "Liquidity pockets widened overnight; vol sellers parked gamma at the door.",
    source: "Bloomberg · 5:42 AM",
  },
  {
    tag: "Local",
    title: "Transit: Blue line +6m due to signal",
    snippet: "Shuttle B rerouted via Harbor; consider the 6:10 water taxi if tight.",
    source: "CityPulse API · 5:58 AM",
  },
  {
    tag: "Science",
    title: "JWST batch: three candidate atmospheres",
    snippet: "Oxygen-bearing lines flagged for manual review — embargo lifts Thursday.",
    source: "NASA RSS · 4:12 AM",
  },
];

export function BriefingHub({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "flex flex-col rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 backdrop-blur-sm",
        className,
      )}
    >
      <div className="mb-4 flex items-baseline justify-between gap-2">
        <h2 className="text-sm font-semibold text-zinc-100">6 AM Briefing Hub</h2>
        <span className="font-mono text-xs text-cyan-400/90">06:00</span>
      </div>
      <div className="flex flex-col gap-3">
        {stories.map((s, i) => (
          <motion.article
            key={s.title}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 380, damping: 28, delay: i * 0.05 }}
            className="rounded-xl border border-zinc-800/80 bg-zinc-950/60 p-4"
          >
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className="rounded-md border border-violet-500/30 bg-violet-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-violet-200">
                {s.tag}
              </span>
            </div>
            <h3 className="text-sm font-medium leading-snug text-zinc-100">{s.title}</h3>
            <p className="mt-1.5 text-xs leading-relaxed text-zinc-500">{s.snippet}</p>
            <footer className="mt-3 border-t border-zinc-800/80 pt-2 text-[11px] text-zinc-600">{s.source}</footer>
          </motion.article>
        ))}
      </div>
    </div>
  );
}
