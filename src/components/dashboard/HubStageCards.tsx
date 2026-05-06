"use client";

// ── HubStageCards - command surface: Neural hero + lanes (Oracle / Quarantine) ─
// > Neural hub card burned - hero + taskbar already own that jump; duplicates PM2 karma.
// > Oracle lane sets stage shell; `/oracle` only from OracleStagePanel when you bail out.
import { motion } from "framer-motion";

import type { StageId } from "@/components/dashboard/stageTypes";
import { glassPanelSurfaceClasses } from "@/components/ui/GlassPanel";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { cn } from "@/lib/cn";

export type HubStageCardsProps = {
  setStage: (s: StageId) => void;
};

export function HubStageCards({ setStage }: HubStageCardsProps) {
  return (
    <div className="flex min-h-[50vh] flex-1 flex-col gap-6 p-4 sm:p-7 lg:min-h-0">
      <motion.button
        type="button"
        whileHover={{ scale: 1.004 }}
        whileTap={{ scale: 0.996 }}
        onClick={() => setStage("neural")}
        className={cn(
          glassPanelSurfaceClasses,
          "relative w-full overflow-hidden rounded-2xl border border-[color:color-mix(in_oklab,var(--spirit-accent)_24%,transparent)] bg-gradient-to-b from-white/[0.07] to-white/[0.02] px-5 py-5 text-left shadow-[0_24px_72px_-32px_var(--spirit-glow)] transition",
        )}
      >
        <div className="pointer-events-none absolute -right-16 -top-20 h-48 w-48 rounded-full bg-[color:color-mix(in_oklab,var(--spirit-accent)_18%,transparent)] blur-3xl" />
        <SectionLabel className="relative font-normal text-chalk/50">
          Quick chat
        </SectionLabel>
        <p className="relative mt-2 text-lg font-semibold tracking-tight text-chalk sm:text-xl">
          Ask Spirit from anywhere
        </p>
        <p className="relative mt-1 max-w-xl text-sm text-chalk/50">
          Same wire as <span className="font-mono text-chalk/65">/chat</span> - opens the neural stage.
        </p>
        <div className="relative mt-5 flex items-center gap-3 rounded-full border border-[color:var(--spirit-border)] bg-black/40 px-4 py-3 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)]">
          <span className="flex-1 truncate font-mono text-sm text-chalk/40">
            Type a prompt…
          </span>
          <span className="shrink-0 rounded-full border border-[color:color-mix(in_oklab,var(--spirit-accent)_35%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_12%,transparent)] px-3 py-1.5 font-mono text-[10px] font-semibold uppercase tracking-wider text-[color:var(--spirit-accent-strong)]">
            Neural →
          </span>
        </div>
      </motion.button>

      <div className="grid flex-1 grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5">
        <motion.button
          type="button"
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.994 }}
          onClick={() => setStage("oracle")}
          className={cn(
            glassPanelSurfaceClasses,
            "flex min-h-[11rem] flex-col rounded-2xl border border-[color:color-mix(in_oklab,var(--spirit-secondary-mix)_28%,transparent)] bg-gradient-to-b from-violet-500/[0.06] to-transparent p-6 text-left transition sm:h-full",
          )}
        >
          <SectionLabel className="font-normal text-violet-300/90">Oracle</SectionLabel>
          <h2 className="mt-2 text-base font-semibold text-chalk sm:text-lg">
            Signal router + orb lane
          </h2>
          <p className="mt-2 flex-1 text-sm leading-snug text-chalk/55">
            In-shell lane first; escalate to standalone workspace only when that panel sends you.
          </p>
          <span className="mt-5 inline-flex font-mono text-xs text-violet-200/90">
            Enter Oracle stage →
          </span>
        </motion.button>

        <motion.button
          type="button"
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.994 }}
          onClick={() => setStage("quarantine")}
          className={cn(
            glassPanelSurfaceClasses,
            "flex min-h-[11rem] flex-col rounded-2xl border border-amber-500/22 bg-amber-500/[0.035] p-6 text-left transition sm:h-full",
          )}
        >
          <SectionLabel className="font-normal text-amber-500/85">Quarantine</SectionLabel>
          <h2 className="mt-2 text-base font-semibold text-chalk sm:text-lg">
            Voice lab · containment
          </h2>
          <p className="mt-2 flex-1 text-sm leading-snug text-chalk/55">
            Voice lab and containment zone - visualizer prototype, not chat transport.
          </p>
          <span className="mt-5 inline-flex font-mono text-xs text-amber-200/90">
            Enter stage →
          </span>
        </motion.button>
      </div>
    </div>
  );
}
