"use client";

// ── DashboardClient — stage machine + layout chrome (thin orchestrator) ───────
// > Phase 2: heavy stage bodies code-split (Neural/Quarantine); hub/oracle eager
// > RSC parent passes DiagnosticsPanel as `rightRail` (server slot pattern)
import dynamic from "next/dynamic";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Zap } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";

import { Clock } from "@/components/dashboard/Clock";
import { StageFallback } from "@/components/dashboard/StageFallback";
import { HubStage } from "@/components/dashboard/stages/HubStage";
import { OracleStage } from "@/components/dashboard/stages/OracleStage";
import { TaskbarRail } from "@/components/dashboard/TaskbarRail";
import { ThemeStrip } from "@/components/dashboard/ThemeStrip";
import type { StageId } from "@/components/dashboard/stageTypes";
import { ClientFailSafe } from "@/components/system/ClientFailSafe";
import { cn } from "@/lib/cn";

const DynamicNeuralStage = dynamic(
  () => import("@/components/dashboard/stages/NeuralStage"),
  {
    loading: () => <StageFallback label="Loading neural…" />,
  },
);

const DynamicQuarantineStage = dynamic(
  () => import("@/components/dashboard/stages/QuarantineStage"),
  {
    loading: () => <StageFallback label="Loading quarantine…" />,
  },
);

export type DashboardClientProps = {
  rightRail: ReactNode;
};

function DashboardClientInner({ rightRail }: DashboardClientProps) {
  const pathname = usePathname();
  const [stage, setStage] = useState<StageId>("hub");

  const spring = useMemo(
    () => ({ type: "spring" as const, stiffness: 420, damping: 36 }),
    [],
  );

  return (
    <div
      data-pathname={pathname}
      data-stage={stage}
      className="relative flex min-h-[100dvh] min-h-dvh w-full bg-[color:var(--spirit-bg)] text-chalk lg:flex-row"
      style={{ transition: "background-color 320ms ease" }}
    >
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-[color:var(--spirit-bg)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(ellipse_110%_75%_at_50%_-8%,color-mix(in_oklab,var(--spirit-accent)_16%,transparent),transparent_55%)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 opacity-[0.2] [background-image:linear-gradient(rgba(255,255,255,0.035)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.035)_1px,transparent_1px)] [background-size:52px_52px]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 z-0 bg-[radial-gradient(circle_at_50%_115%,rgba(0,0,0,0.42),transparent_52%)]"
        aria-hidden
      />

      <aside
        className="relative z-40 hidden w-[72px] shrink-0 flex-col border-r border-[color:var(--spirit-border)] bg-white/[0.03] backdrop-blur-xl lg:flex"
        aria-label="Primary taskbar"
      >
        <div className="flex min-h-[44px] items-center justify-center border-b border-[color:var(--spirit-border)] py-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-full border border-violet-500/35 bg-white/[0.04] shadow-[0_0_28px_-6px_var(--spirit-glow)]">
            <Zap className="h-4 w-4 text-[color:var(--spirit-accent-strong)]" aria-hidden />
          </div>
        </div>
        <TaskbarRail
          stage={stage}
          setStage={setStage}
          className="flex flex-1 flex-col gap-1 p-2"
          linkWrap="min-h-[44px] min-w-[44px] w-full"
          tooltips
        />
        <div className="border-t border-[color:var(--spirit-border)] p-2">
          <p className="text-center font-mono text-[9px] uppercase tracking-[0.2em] text-chalk/45">
            SPIRIT OS
          </p>
        </div>
      </aside>

      <div className="relative z-10 flex min-h-0 min-w-0 flex-1 flex-col pb-[calc(5rem+env(safe-area-inset-bottom,0px))] lg:pb-0">
        <header className="shrink-0 border-b border-[color:var(--spirit-border)] bg-white/[0.03] px-4 py-2.5 backdrop-blur-xl sm:px-5 sm:py-3">
          <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
            <div className="min-w-0 flex-1">
              <motion.h1
                key={stage}
                initial={{ opacity: 0.55, filter: "blur(3px)" }}
                animate={{ opacity: 1, filter: "blur(0px)" }}
                transition={spring}
                className="truncate font-semibold tracking-tight text-chalk text-lg sm:text-xl md:text-[1.4rem]"
              >
                Spirit OS
              </motion.h1>
              <p className="mt-0.5 truncate font-mono text-[11px] leading-snug text-chalk/50 sm:text-xs">
                {stage === "hub" && (
                  <>
                    Command surface · orchestrate stages{" "}
                    <span className="text-chalk/35">
                      · local inference · diagnostics
                    </span>
                  </>
                )}
                {stage === "neural" && (
                  <>
                    Neural interface · conversational core{" "}
                    <span className="text-chalk/35">· streaming /api/spirit</span>
                  </>
                )}
                {stage === "oracle" && (
                  <>
                    Oracle lane · signal routing{" "}
                    <span className="text-chalk/35">· workspace escalation</span>
                  </>
                )}
                {stage === "quarantine" && (
                  <>
                    Voice lab · containment prototype{" "}
                    <span className="text-chalk/35">· not chat transport</span>
                  </>
                )}
              </p>
            </div>
            <div className={cn("flex shrink-0 flex-wrap items-center gap-2")}>
              <Clock />
              <ThemeStrip />
            </div>
          </div>
        </header>

        <div className="relative z-10 flex min-h-0 flex-1 flex-col lg:flex-row">
          <AnimatePresence mode="wait" initial={false}>
            <motion.main
              key={stage}
              role="region"
              aria-label={`Stage ${stage}`}
              initial={{ opacity: 0, x: stage === "hub" ? 0 : 12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.26, ease: [0.22, 1, 0.36, 1] }}
              className="glass relative flex min-h-0 flex-1 flex-col overflow-hidden border-[color:var(--spirit-border)]/80 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] sm:rounded-none lg:rounded-none"
            >
              {stage === "hub" ? <HubStage setStage={setStage} /> : null}
              {stage === "neural" ? <DynamicNeuralStage /> : null}
              {stage === "oracle" ? <OracleStage /> : null}
              {stage === "quarantine" ? <DynamicQuarantineStage /> : null}
            </motion.main>
          </AnimatePresence>

          {rightRail}
        </div>
      </div>

      <nav
        className={cn(
          "fixed inset-x-0 bottom-0 z-40 flex min-h-[calc(4.85rem+env(safe-area-inset-bottom,0px))] items-center justify-around",
          "border-t border-[color:var(--spirit-border)]",
          "bg-[color:color-mix(in_oklab,var(--spirit-bg)_82%,transparent)]",
          "shadow-[0_-1px_0_color-mix(in_oklab,var(--spirit-glow)_60%,transparent),0_-14px_40px_-26px_var(--spirit-glow)]",
          "px-1 pb-[env(safe-area-inset-bottom,0px)] pt-2 backdrop-blur-2xl lg:hidden",
        )}
        aria-label="Mobile taskbar"
      >
        <TaskbarRail
          stage={stage}
          setStage={setStage}
          className="w-full justify-around gap-0.5"
          linkWrap="min-h-[52px] min-w-[52px] flex-shrink-0"
        />
      </nav>
    </div>
  );
}

export default function DashboardClient(props: DashboardClientProps) {
  return (
    <ClientFailSafe label="dashboard">
      <DashboardClientInner {...props} />
    </ClientFailSafe>
  );
}
