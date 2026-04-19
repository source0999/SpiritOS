"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useCallback, useState } from "react";
import { cn } from "@/lib/utils";

const roastLines = [
  "> analyzing commit messages…",
  "> detected 14 instances of \"final_final_v2\"",
  "> your README still says \"TODO: write readme\"",
  "> git blame --line-porcelain → mostly you at 3am",
  "> verdict: ship it, but never speak of this diff again",
];

export function ToxicGrader({ className }: { className?: string }) {
  const [lines, setLines] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  const grade = useCallback(() => {
    setBusy(true);
    setLines([]);
    let i = 0;
    const tick = () => {
      if (i < roastLines.length) {
        setLines((prev) => [...prev, roastLines[i]]);
        i += 1;
        window.setTimeout(tick, 420 + Math.random() * 280);
      } else {
        setBusy(false);
      }
    };
    window.setTimeout(tick, 200);
  }, []);

  return (
    <div
      className={cn(
        "flex flex-col overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 shadow-xl",
        className,
      )}
    >
      <div className="flex h-9 items-center gap-2 border-b border-zinc-800 bg-zinc-900/90 px-3">
        <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
        <span className="h-3 w-3 rounded-full bg-[#febc2e]" />
        <span className="h-3 w-3 rounded-full bg-[#28c840]" />
        <span className="ml-2 flex-1 truncate text-center font-mono text-[11px] text-zinc-500">toxic-grader — zsh</span>
      </div>
      <div className="flex flex-1 flex-col bg-[#0d0d0d] p-4 font-mono text-[13px] leading-relaxed text-emerald-400/95">
        <p className="text-zinc-600">Welcome to Toxic Grader. Press the button to regret nothing.</p>
        <div className="mt-3 min-h-[140px] space-y-1">
          <AnimatePresence mode="popLayout">
            {lines.map((l) => (
              <motion.p
                key={l}
                initial={{ opacity: 0, x: -4 }}
                animate={{ opacity: 1, x: 0 }}
                className="break-words"
              >
                {l}
              </motion.p>
            ))}
          </AnimatePresence>
          <div className="flex items-center gap-1 pt-1">
            <span className="text-emerald-500">❯</span>
            <motion.span
              className="inline-block h-4 w-2.5 bg-emerald-400"
              animate={{ opacity: [1, 0, 1] }}
              transition={{ duration: 0.9, repeat: Infinity }}
            />
          </div>
        </div>
        <motion.button
          type="button"
          disabled={busy}
          onClick={grade}
          whileTap={{ scale: 0.98 }}
          className={cn(
            "mt-auto w-full rounded-lg border border-zinc-700 bg-zinc-900 py-2.5 text-sm font-medium text-zinc-200 transition",
            "hover:border-emerald-600/50 hover:bg-zinc-800",
            busy && "cursor-wait opacity-70",
          )}
        >
          {busy ? "Roasting…" : "Grade my week"}
        </motion.button>
      </div>
    </div>
  );
}
