"use client";

import { motion } from "framer-motion";
import { Cpu, HardDrive, MemoryStick, WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";

const stats = [
  { label: "CPU", icon: Cpu, value: 38, color: "from-sky-500 to-cyan-400" },
  { label: "RAM", icon: MemoryStick, value: 71, color: "from-violet-500 to-fuchsia-400" },
  { label: "Disk", icon: HardDrive, value: 54, color: "from-emerald-500 to-teal-400" },
];

export function SystemStats({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "flex flex-col rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 backdrop-blur-sm",
        className,
      )}
    >
      <h2 className="mb-4 text-sm font-semibold text-zinc-100">System Stats</h2>
      <ul className="flex flex-col gap-5">
        {stats.map((s, idx) => (
          <li key={s.label}>
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="flex items-center gap-2 font-medium text-zinc-300">
                <s.icon className="h-3.5 w-3.5 text-zinc-500" />
                {s.label}
              </span>
              <span className="tabular-nums text-zinc-500">{s.value}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
              <motion.div
                className={cn("h-full rounded-full bg-gradient-to-r", s.color)}
                initial={{ width: 0 }}
                animate={{ width: `${s.value}%` }}
                transition={{ type: "spring", stiffness: 100, damping: 18, delay: idx * 0.08 }}
              />
            </div>
          </li>
        ))}
      </ul>
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="mt-5 flex gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-100"
      >
        <WifiOff className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
        <div>
          <p className="font-semibold text-amber-200">P40 accelerator offline</p>
          <p className="mt-0.5 text-amber-100/80">PCIe link dropped at 04:18 — jobs queued on CPU pool.</p>
        </div>
      </motion.div>
    </div>
  );
}
