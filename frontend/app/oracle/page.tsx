"use client";

import { useState } from "react";
import { ArrowLeft, Mic } from "lucide-react";
import Link from "next/link";

// ── Types ─────────────────────────────────────────────────────────────────────

type SarcasmId = "chill" | "peer" | "unhinged";

// ── Static config ─────────────────────────────────────────────────────────────

const SARCASM_LEVELS: {
  id: SarcasmId;
  label: string;
  desc: string;
  active: string;
}[] = [
  {
    id:     "chill",
    label:  "Chill",
    desc:   "Measured. Cooperative.",
    active: "border-emerald-500/40 bg-emerald-500/15 text-emerald-300",
  },
  {
    id:     "peer",
    label:  "Peer",
    desc:   "Direct. Unfiltered.",
    active: "border-violet-500/40 bg-violet-500/15 text-violet-300",
  },
  {
    id:     "unhinged",
    label:  "Unhinged",
    desc:   "Maximum exasperation.",
    active: "border-rose-500/40 bg-rose-500/15 text-rose-300",
  },
];

// XTTS v2 acoustic stage-direction markers
const MARKERS = [
  "[sigh]",
  "[scoffs]",
  "[groan]",
  "[exhale]",
  "[pause]",
  "[laughs]",
] as const;

// Pre-computed waveform bar shapes — envelope peaks at the centre so the
// visualiser looks like a real voice fundamental frequency plot.
const BARS = Array.from({ length: 44 }, (_, i) => {
  const envelope = Math.sin((i / 43) * Math.PI);            // 0 → 1 → 0
  const jitter   = ((i * 53 + 17) % 18);                    // 0–17 pseudo-random
  const maxH     = Math.round(10 + envelope * 50 + jitter); // 10–78 px
  const dur      = 0.48 + (i % 7) * 0.06;                   // 0.48–0.84 s
  const delay    = i * 0.022;                                // staggered
  // Colour accent: rose spike every ~9 bars, amber every ~5 bars, rest violet
  const color =
    i % 9 === 4 ? "bg-rose-400/65"
    : i % 5 === 2 ? "bg-amber-400/55"
    : "bg-violet-500/60";
  return { maxH, dur, delay, color };
});

// ── Component ─────────────────────────────────────────────────────────────────

export default function OraclePage() {
  const [sarcasm,      setSarcasm]      = useState<SarcasmId>("peer");
  const [activeMarker, setActiveMarker] = useState<string | null>(null);

  const currentLevel = SARCASM_LEVELS.find((l) => l.id === sarcasm)!;

  return (
    <div className="flex h-[100dvh] flex-col bg-zinc-950 text-zinc-100 overflow-hidden">

      {/* ── Header ────────────────────────────────────────────────────────── */}
      <header className="flex-shrink-0 flex items-center justify-between border-b border-white/[0.05] px-5 py-3">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm text-zinc-400 transition-colors hover:text-zinc-100"
        >
          <ArrowLeft size={15} className="pointer-events-none" />
          Dashboard
        </Link>

        {/* Pulse indicator */}
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-50" />
            <span className="relative h-2 w-2 rounded-full bg-emerald-400" />
          </span>
          <span className="font-mono text-xs text-zinc-400">XTTS v2 · Online</span>
        </div>

        <span className="font-mono text-xs text-zinc-600">Architecture 7</span>
      </header>

      {/* ── Main ──────────────────────────────────────────────────────────── */}
      <main className="flex flex-1 flex-col items-center justify-center gap-8 overflow-hidden px-4 py-4">

        {/* Status badge */}
        <div className="flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/[0.06] px-4 py-1.5">
          <Mic size={12} className="pointer-events-none text-violet-400" />
          <span className="font-mono text-[11px] uppercase tracking-widest text-violet-300">
            Listening · Idle
          </span>
        </div>

        {/* ── XL Navi Orb ─────────────────────────────────────────────────── */}
        {/* h-72 w-72 = 288px container; entity h-20 w-20 = 80px            */}
        <div className="relative h-72 w-72 flex-shrink-0 pointer-events-none">

          {/* Ambient glow — fixed at centre while Navi orbits */}
          <span className="navi-aura  pointer-events-none absolute inset-0 m-auto h-44 w-44 rounded-full bg-violet-500/15" />
          <span className="navi-halo  pointer-events-none absolute inset-0 m-auto h-32 w-32 rounded-full bg-violet-600/18" />

          {/* Particle trail */}
          <span className="navi-p1-xl pointer-events-none absolute inset-0 m-auto h-[11px] w-[11px] rounded-full bg-violet-300 opacity-70" />
          <span className="navi-p2-xl pointer-events-none absolute inset-0 m-auto h-[8px]  w-[8px]  rounded-full bg-violet-400 opacity-50" />
          <span className="navi-p3-xl pointer-events-none absolute inset-0 m-auto h-[6px]  w-[6px]  rounded-full bg-violet-400 opacity-30" />
          <span className="navi-p4-xl pointer-events-none absolute inset-0 m-auto h-[4px]  w-[4px]  rounded-full bg-violet-500 opacity-[0.18]" />
          <span className="navi-p5-xl pointer-events-none absolute inset-0 m-auto h-[3px]  w-[3px]  rounded-full bg-violet-500 opacity-10" />

          {/* Flying entity — wings as children so they travel together */}
          <div className="navi-float-xl absolute inset-0 m-auto flex h-20 w-20 items-center justify-center rounded-full">
            <span className="navi-wing-l-xl pointer-events-none absolute h-16 w-[14px] rounded-full bg-gradient-to-b from-violet-300/65 to-violet-700/10" />
            <span className="navi-wing-r-xl pointer-events-none absolute h-16 w-[14px] rounded-full bg-gradient-to-b from-violet-300/65 to-violet-700/10" />
            <span className="navi-halo-btn  pointer-events-none absolute h-20 w-20    rounded-full border border-violet-300/30" />
            {/* Glow pulse — radial gradient + opacity/scale3d (GPU safe, no box-shadow animation) */}
            <span
              className="navi-glow-pulse pointer-events-none absolute h-24 w-24 rounded-full"
              style={{ background: "radial-gradient(circle, rgba(139,92,246,0.70) 0%, rgba(139,92,246,0) 70%)" }}
            />
            <span className="navi-core-xl   pointer-events-none absolute h-10 w-10    rounded-full bg-white" />
          </div>
        </div>

        {/* ── Waveform Visualiser ─────────────────────────────────────────── */}
        {/*
          Bar heights peak at the centre (sine envelope) to simulate a real
          voice fundamental frequency plot. Rose spikes = acoustic markers.
          Amber spikes = stress / emphasis regions.
        */}
        <div className="flex w-full max-w-xl flex-col items-center gap-4">

          {/* Bar graph */}
          <div className="flex h-20 w-full items-end justify-center gap-[3px]">
            {BARS.map((bar, i) => (
              <span
                key={i}
                className={`${bar.color} w-[4px] origin-bottom rounded-full`}
                style={{
                  height: `${bar.maxH}px`,
                  animation: `navi-bar ${bar.dur}s ease-in-out ${bar.delay}s infinite alternate`,
                }}
              />
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 text-[11px] font-mono text-zinc-600">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-violet-500/60" />
              Normal
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-amber-400/55" />
              Stress
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-rose-400/65" />
              Marker
            </span>
          </div>

          {/* Acoustic marker chips */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            {MARKERS.map((marker) => {
              const active = activeMarker === marker;
              return (
                <button
                  key={marker}
                  type="button"
                  onClick={() => setActiveMarker(active ? null : marker)}
                  onTouchEnd={(e) => {
                    e.preventDefault();
                    setActiveMarker(active ? null : marker);
                  }}
                  className={`rounded-full border px-3 py-1 font-mono text-[11px] transition-colors ${
                    active
                      ? "border-rose-500/50 bg-rose-500/15 text-rose-300"
                      : "border-white/[0.08] bg-white/[0.02] text-zinc-500 hover:border-white/20 hover:text-zinc-400"
                  }`}
                >
                  {marker}
                </button>
              );
            })}
          </div>

          {/* Marker description */}
          {activeMarker && (
            <p className="font-mono text-[11px] italic text-zinc-500">
              XTTS v2 injects emotional inflection at{" "}
              <span className="text-rose-400">{activeMarker}</span> tokens
            </p>
          )}
        </div>
      </main>

      {/* ── Sarcasm Level ──────────────────────────────────────────────────── */}
      <footer
        className="flex-shrink-0 border-t border-white/[0.05] bg-zinc-950 px-4 pt-4"
        style={{ paddingBottom: "max(20px, env(safe-area-inset-bottom))" }}
      >
        <div className="mx-auto flex max-w-sm flex-col gap-3">

          {/* Label row */}
          <div className="flex items-center justify-between">
            <span className="font-mono text-[11px] uppercase tracking-widest text-zinc-500">
              Sarcasm Level
            </span>
            <span className="font-mono text-[11px] text-zinc-600 transition-all">
              {currentLevel.desc}
            </span>
          </div>

          {/* 3-step segmented control */}
          <div className="grid grid-cols-3 gap-1 rounded-xl border border-white/[0.07] bg-white/[0.02] p-1">
            {SARCASM_LEVELS.map((level) => (
              <button
                key={level.id}
                type="button"
                onClick={() => setSarcasm(level.id)}
                onTouchEnd={(e) => { e.preventDefault(); setSarcasm(level.id); }}
                className={`rounded-lg border py-2.5 text-xs font-semibold transition-colors ${
                  sarcasm === level.id
                    ? level.active
                    : "border-transparent text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {level.label}
              </button>
            ))}
          </div>

          {/* Visual tone bar — three coloured segments, active one glows */}
          <div className="flex gap-1">
            {SARCASM_LEVELS.map((level) => (
              <div
                key={level.id}
                className={`h-0.5 flex-1 rounded-full transition-all duration-300 ${
                  sarcasm === level.id
                    ? level.id === "chill"    ? "bg-emerald-400"
                      : level.id === "peer"   ? "bg-violet-400"
                      :                         "bg-rose-400"
                    : "bg-white/10"
                }`}
              />
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
