"use client";

import { motion } from "framer-motion";
import { AlertTriangle, Zap } from "lucide-react";
import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";

type Node = { id: string; label: string; load: number; kw: number };

const seedNodes: Node[] = [
  { id: "rack-a", label: "Rack A — UPS", load: 62, kw: 2.8 },
  { id: "rack-b", label: "Rack B — PDU", load: 48, kw: 2.1 },
  { id: "office", label: "Office ring", load: 31, kw: 0.9 },
  { id: "hvac", label: "HVAC aux", load: 74, kw: 3.6 },
];

export function EnergyMatrix({ className }: { className?: string }) {
  const [nodes] = useState(seedNodes);
  const peak = useMemo(() => nodes.some((n) => n.load >= 70), [nodes]);
  const totalKw = useMemo(() => nodes.reduce((a, n) => a + n.kw, 0), [nodes]);
  const estCost = (totalKw * 24 * 0.14).toFixed(2);

  return (
    <div
      className={cn(
        "flex flex-col rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 backdrop-blur-sm",
        className,
      )}
    >
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-sm font-semibold text-zinc-100">
            <Zap className="h-4 w-4 text-amber-400" />
            Energy Matrix
          </h2>
          <p className="mt-1 text-xs text-zinc-500">Mock nodes · swap for NUT / SNMP</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Est. 24h</p>
          <p className="text-lg font-semibold tabular-nums text-zinc-100">${estCost}</p>
          <p className="text-xs text-zinc-500">{totalKw.toFixed(1)} kW draw</p>
        </div>
      </div>
      {peak && (
        <motion.div
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 flex items-center gap-2 rounded-xl border border-amber-500/35 bg-amber-500/10 px-3 py-2 text-xs text-amber-100"
        >
          <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
          Peak load on one branch — consider shedding HVAC aux during training runs.
        </motion.div>
      )}
      <ul className="flex flex-col gap-4">
        {nodes.map((n, idx) => (
          <li key={n.id}>
            <div className="mb-1.5 flex justify-between text-xs">
              <span className="font-medium text-zinc-300">{n.label}</span>
              <span className="tabular-nums text-zinc-500">
                {n.load}% · {n.kw} kW
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-zinc-800">
              <motion.div
                className={cn(
                  "h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400",
                  n.load >= 70 && "from-amber-500 to-orange-400",
                )}
                initial={{ width: 0 }}
                animate={{ width: `${n.load}%` }}
                transition={{ type: "spring", stiffness: 120, damping: 20, delay: idx * 0.06 }}
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
