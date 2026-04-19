"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, TerminalSquare } from "lucide-react";
import { PROJECTS } from "@/lib/mockProjects";
import type { ProjectStatus } from "@/lib/mockProjects";

// ── Helpers ───────────────────────────────────────────────────────────────────

function statusColor(s: ProjectStatus) {
  if (s === "active") return "bg-emerald-400";
  if (s === "paused") return "bg-amber-400";
  return "bg-zinc-600";
}

function barColor(pct: number) {
  if (pct >= 70) return "bg-emerald-500";
  if (pct >= 40) return "bg-violet-500";
  return "bg-amber-500";
}

// Full class strings required so Tailwind purge keeps each variant.
function langBadge(lang: string): string {
  switch (lang.toLowerCase()) {
    case "typescript": return "border-sky-500/30 bg-sky-500/10 text-sky-400";
    case "python":     return "border-amber-500/30 bg-amber-500/10 text-amber-400";
    case "shell":
    case "bash":       return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
    case "react":      return "border-cyan-500/30 bg-cyan-500/10 text-cyan-400";
    default:           return "border-white/[0.08] bg-white/[0.04] text-zinc-500";
  }
}

// ── Component ─────────────────────────────────────────────────────────────────

interface ProjectWidgetProps {
  /**
   * Overrides the hardcoded completion% in mockProjects.ts for specific repos.
   * Populated server-side by ProjectWidgetServer via lib/readmeProgress.ts.
   * Any repo slug absent from this map falls back to the mockProjects value.
   */
  completionOverrides?: Record<string, number>;
}

export function ProjectWidget({ completionOverrides = {} }: ProjectWidgetProps) {
  // Trigger CSS scaleX transition after mount — GPU-composited, iOS safe.
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const id = setTimeout(() => setMounted(true), 60);
    return () => clearTimeout(id);
  }, []);

  return (
    <Link
      href="/projects"
      className="col-span-12 md:col-span-7 flex flex-col rounded-2xl border border-white/10 bg-zinc-900 p-5 cursor-pointer touch-manipulation group hover:border-violet-500/30 transition-colors"
    >
      {/* ── Header ── */}
      <div className="mb-3 flex items-start justify-between">
        <div>
          <p className="mb-0.5 font-mono text-[10px] uppercase tracking-widest text-violet-400/70">
            Architecture 5 · Project Tracker
          </p>
          <h2 className="text-base font-semibold tracking-tight text-zinc-100">
            Active Repositories
          </h2>
        </div>
        <div className="flex flex-shrink-0 items-center gap-2">
          <TerminalSquare size={14} className="text-zinc-600" />
          <ArrowRight
            size={14}
            className="text-zinc-600 transition-all group-hover:translate-x-0.5 group-hover:text-violet-400"
          />
        </div>
      </div>

      {/* ── Project list ──────────────────────────────────────────────────────
        All 5 projects rendered. overflow-y-auto contains any future growth
        without blowing the card height.
        divide-y gives each row a hairline separator without extra margin math.
      ──────────────────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto divide-y divide-white/[0.04]">
        {PROJECTS.map((proj, i) => {
          // Prefer the README-parsed override; fall back to the static mock value.
          const completion = completionOverrides[proj.repo] ?? proj.completion;

          return (
          <div key={proj.repo} className="flex items-center gap-3 py-2.5">

            {/* Status pulse dot */}
            <span
              className={`h-1.5 w-1.5 flex-shrink-0 rounded-full ${statusColor(proj.status)}`}
            />

            {/* Name · lang badge · progress bar */}
            <div className="min-w-0 flex-1">

              {/* Row 1: title + language badge */}
              <div className="mb-1.5 flex items-center gap-2">
                <span className="truncate font-mono text-xs font-medium leading-none text-zinc-200">
                  {proj.name}
                </span>
                <span
                  className={`flex-shrink-0 rounded border px-1.5 py-px font-mono text-[9px] font-bold uppercase tracking-wide ${langBadge(proj.lang)}`}
                >
                  {proj.lang}
                </span>
              </div>

              {/* Row 2: animated progress bar.
                  scaleX animates on the GPU compositor (translate3d-promoted
                  layer). origin-left grows the bar left → right.
                  Staggered transitionDelay creates a cascade on first mount.  */}
              <div className="relative h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                <div
                  className={`absolute inset-y-0 left-0 w-full origin-left rounded-full transition-transform ease-out ${barColor(completion)}/70`}
                  style={{
                    transform:         `scaleX(${mounted ? completion / 100 : 0})`,
                    transitionDuration: "750ms",
                    transitionDelay:    `${60 + i * 70}ms`,
                  }}
                />
              </div>
            </div>

            {/* Completion % */}
            <span className="w-8 flex-shrink-0 text-right font-mono text-[11px] tabular-nums text-zinc-500">
              {completion}%
            </span>

            {/* TODO count pill — amber when >5 open tasks */}
            <span
              className={`hidden flex-shrink-0 rounded-full border px-1.5 py-px font-mono text-[9px] font-semibold sm:block ${
                proj.todos.length > 5
                  ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                  : "border-white/[0.07] bg-white/[0.03] text-zinc-600"
              }`}
            >
              {proj.todos.length}
            </span>
          </div>
          );
        })}
      </div>

      {/* ── Footer ── */}
      <div className="mt-3 flex items-center gap-2 border-t border-white/[0.06] pt-3">
        <span className="text-[11px] text-zinc-600">
          Spirit scans TODOs vs README · auto-computes completion %
        </span>
        <span className="ml-auto flex flex-shrink-0 items-center gap-1 font-semibold text-[11px] text-violet-400">
          View All <ArrowRight size={11} />
        </span>
      </div>
    </Link>
  );
}
