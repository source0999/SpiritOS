"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

const bars = Array.from({ length: 24 }, (_, i) => i);

export function OracleOrb({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "relative flex flex-col overflow-hidden rounded-2xl border border-zinc-800 bg-gradient-to-b from-zinc-900/90 to-zinc-950 p-6",
        className,
      )}
    >
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold tracking-tight text-zinc-100">Oracle Orb</h2>
        <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-cyan-300">
          Live
        </span>
      </div>
      <div className="relative mx-auto flex aspect-square w-full max-w-[220px] items-center justify-center">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="absolute rounded-full border border-cyan-400/25 bg-cyan-400/5"
            style={{
              width: `${68 + i * 36}%`,
              height: `${68 + i * 36}%`,
            }}
            animate={{ scale: [1, 1.04, 1], opacity: [0.35, 0.6, 0.35] }}
            transition={{
              duration: 3.2 + i * 0.4,
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 0.35,
            }}
          />
        ))}
        <motion.div
          className="relative z-10 h-[42%] w-[42%] rounded-full bg-gradient-to-br from-cyan-300 via-violet-500 to-indigo-700 shadow-[0_0_40px_rgba(34,211,238,0.45)]"
          animate={{ scale: [1, 1.03, 1] }}
          transition={{ type: "spring", stiffness: 260, damping: 18, repeat: Infinity, repeatDelay: 0.6 }}
        />
        <div className="pointer-events-none absolute inset-0 rounded-full bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.22),transparent_55%)]" />
      </div>
      <div className="mt-6 flex h-14 items-end justify-center gap-[3px]">
        {bars.map((i) => (
          <motion.div
            key={i}
            className="w-1 rounded-full bg-gradient-to-t from-cyan-600 to-cyan-300"
            initial={{ height: 8 }}
            animate={{
              height: [10 + (i % 5) * 4, 28 + (i % 7) * 5, 12 + (i % 4) * 3],
              opacity: [0.45, 1, 0.55],
            }}
            transition={{
              duration: 1.1 + (i % 5) * 0.08,
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 0.04,
            }}
          />
        ))}
      </div>
      <p className="mt-3 text-center text-xs text-zinc-500">Ambient resonance · no audio wired</p>
    </div>
  );
}
