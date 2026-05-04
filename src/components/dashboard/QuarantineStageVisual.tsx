"use client";

import { Zap } from "lucide-react";

import { cn } from "@/lib/cn";

const SPECTRUM_BAR_CLASSES = [
  "h-2 delay-0",
  "h-3 delay-75",
  "h-4 delay-150",
  "h-5 delay-100",
  "h-3 delay-200",
  "h-6 delay-75",
  "h-4 delay-300",
  "h-2 delay-150",
  "h-5 delay-0",
  "h-3 delay-200",
  "h-4 delay-100",
  "h-8 delay-75",
  "h-3 delay-150",
  "h-4 delay-300",
  "h-6 delay-150",
  "h-3 delay-0",
  "h-5 delay-200",
  "h-4 delay-100",
  "h-8 delay-75",
  "h-3 delay-150",
  "h-4 delay-300",
] as const;

type Props = {
  /** Full route page keeps back nav; Hub stage skips chrome */
  variant?: "embedded" | "page";
};

// ── Quarantine visual — orb + spectrum (prototype / standby copy only) ─────────
// > No live mic or reactive audio claims until the stack is actually wired.

export function QuarantineStageVisual({ variant = "embedded" }: Props) {
  return (
    <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_42%,rgba(139,92,246,0.28)_0%,rgba(76,29,149,0.12)_40%,transparent_72%)]" />
      <div className="pointer-events-none absolute left-1/2 top-[36%] h-[min(78vw,520px)] w-[min(78vw,520px)] -translate-x-1/2 -translate-y-1/2 bg-violet-600/18 blur-[110px]" />
      <div className="pointer-events-none absolute left-1/2 top-[50%] h-[min(55vw,400px)] w-[min(55vw,400px)] -translate-x-1/2 -translate-y-1/2 bg-purple-900/22 blur-[90px]" />

      <div className="relative z-10 mx-auto flex w-full max-w-xl flex-col rounded-2xl p-5 sm:p-7">
        {variant === "page" ? (
          <div className="mb-5 flex items-center justify-end gap-2 font-mono text-[10px] uppercase tracking-widest text-chalk/40">
            <Zap className="h-4 w-4 text-[color:var(--spirit-accent-strong)]" aria-hidden />
            feature lab
          </div>
        ) : null}

        <p className="mb-1 font-mono text-[10px] font-semibold uppercase tracking-[0.28em] text-chalk/45">
          Quarantine · feature lab
        </p>
        <h2 className="text-lg font-semibold tracking-tight text-chalk sm:text-xl">
          Visualizer standby
        </h2>
        <p className="mt-2 max-w-md text-sm leading-relaxed text-chalk/50">
          Prototype containment visuals only — no live uplink, no mic capture, and no
          streaming audio path in this build.
        </p>

        <div className="relative mx-auto mt-8 flex min-h-[220px] w-full flex-col items-center justify-center py-2">
          <div
            className={cn(
              "relative flex aspect-square w-full max-w-[240px] items-center justify-center rounded-[2rem] border border-[color:color-mix(in_oklab,var(--spirit-border)_80%,transparent)]",
              "bg-[linear-gradient(145deg,rgba(255,255,255,0.04),transparent)] p-4 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.05)] sm:max-w-[280px]",
            )}
          >
            <span className="absolute h-[88%] w-[88%] animate-[pulse_3.4s_ease-in-out_infinite] rounded-full border border-cyan-400/18 bg-cyan-400/[0.04] shadow-[0_0_32px_-8px_var(--spirit-glow,rgba(34,211,238,0.12))]" />
            <span className="absolute h-[72%] w-[72%] animate-[pulse_2.8s_ease-in-out_infinite_200ms] rounded-full border border-violet-400/22 bg-violet-500/[0.04]" />
            <span className="absolute h-[56%] w-[56%] animate-[pulse_3.2s_ease-in-out_infinite_400ms] rounded-full border border-violet-300/25" />
            <div className="relative z-10 h-[38%] w-[38%] rounded-full bg-gradient-to-br from-cyan-300 via-violet-500 to-indigo-700 shadow-[0_0_44px_var(--spirit-glow,rgba(34,211,238,0.2))]" />
            <div className="pointer-events-none absolute inset-0 rounded-full bg-[radial-gradient(circle_at_30%_22%,rgba(255,255,255,0.16),transparent_55%)]" />
          </div>

          <div className="mt-7 flex h-12 w-full max-w-xs items-end justify-center gap-0.5 px-2">
            {SPECTRUM_BAR_CLASSES.map((hDelay, i) => (
              <span
                key={i}
                className={cn(
                  "w-[3px] origin-bottom animate-pulse rounded-full bg-gradient-to-t from-violet-700/75 to-violet-400/55",
                  ...(hDelay.split(" ") as [string, string]),
                  i % 4 === 1 && "opacity-65",
                  i % 5 === 2 && "opacity-50",
                )}
              />
            ))}
          </div>
          <p className="mt-4 text-center font-mono text-[11px] text-chalk/45">
            Ambient mesh · decorative only
          </p>
        </div>

        <div className="mt-auto border-t border-[color:var(--spirit-border)] pt-5">
          <div className="mb-4 rounded-xl border border-cyan-500/20 bg-cyan-500/[0.06] px-4 py-3 text-sm leading-snug text-chalk/80">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.24em] text-cyan-300/90">
              Oracle Voice MVP
            </p>
            <p className="mt-1.5">
              Tap-to-talk uses the browser{" "}
              <span className="font-mono text-chalk/65">Web Speech API</span> when available;
              text fallback always works. Still experimental — no persistent Oracle threads, wake
              word, or local Whisper yet (
              <a
                href="/oracle"
                className="text-[color:var(--spirit-accent-strong)] underline underline-offset-4 hover:brightness-110"
              >
                /oracle
              </a>
              ).
            </p>
          </div>
          <div className="rounded-xl border border-amber-500/25 bg-amber-500/[0.08] px-4 py-3.5">
            <p className="text-center font-mono text-[10px] font-semibold uppercase tracking-[0.32em] text-amber-300/95">
              Prototype · standby
            </p>
            <p className="mt-2 text-center text-sm leading-snug text-chalk/50">
              This page stays a decorative visualizer lab — outbound voice sessions live on{" "}
              <a
                href="/oracle"
                className="text-[color:var(--spirit-accent-strong)] underline underline-offset-4 hover:brightness-110"
              >
                /oracle
              </a>
              .
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
