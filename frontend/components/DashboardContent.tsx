"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useOverlayLock } from "@/components/OverlayLockContext";
import Link from "next/link";
import {
  Zap, Clock, AlertTriangle, Flame, Terminal,
  Cpu, HardDrive,
  Send, X, Command,
  Thermometer, ShieldCheck, ShieldAlert,
  Music2, ArrowRight, Play, Pause,
} from "lucide-react";

// ─── Utility ──────────────────────────────────────────────────────────────────
function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

// ─── BentoCard ────────────────────────────────────────────────────────────────
function BentoCard({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={cn("col-span-12 bg-zinc-900 border border-white/10 rounded-2xl p-5 flex flex-col", className)}
    >
      {children}
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-semibold tracking-widest uppercase text-zinc-500 mb-1">
      {children}
    </p>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. ORACLE ORB
// ─────────────────────────────────────────────────────────────────────────────
function OracleOrb() {
  const router = useRouter();
  return (
    <BentoCard className="md:col-span-4 md:self-start items-center justify-center gap-4 py-8">
      <Label>Spirit · AI Core</Label>

      <div className="relative h-40 w-40 my-2 pointer-events-none">
        <span className="navi-aura pointer-events-none absolute inset-0 m-auto h-20 w-20 rounded-full bg-violet-500/20" />
        <span className="navi-halo pointer-events-none absolute inset-0 m-auto h-12 w-12 rounded-full bg-violet-600/25" />
        <span className="navi-p1 pointer-events-none absolute inset-0 m-auto h-[7px] w-[7px] rounded-full bg-violet-300 opacity-70" />
        <span className="navi-p2 pointer-events-none absolute inset-0 m-auto h-[5px] w-[5px] rounded-full bg-violet-400 opacity-50" />
        <span className="navi-p3 pointer-events-none absolute inset-0 m-auto h-[4px] w-[4px] rounded-full bg-violet-400 opacity-30" />
        <span className="navi-p4 pointer-events-none absolute inset-0 m-auto h-[3px] w-[3px] rounded-full bg-violet-500 opacity-[0.18]" />
        <span className="navi-p5 pointer-events-none absolute inset-0 m-auto h-[2px] w-[2px] rounded-full bg-violet-500 opacity-10" />

        <Link
          href="/oracle"
          aria-label="Open Oracle"
          onTouchEnd={(e) => {
            e.preventDefault(); // iOS WebKit: Link + click alone is unreliable on mobile Safari
            router.push("/oracle");
          }}
          className="navi-float pointer-events-auto absolute inset-0 m-auto z-10 flex h-12 w-12 cursor-pointer touch-manipulation items-center justify-center rounded-full"
        >
          <span className="navi-wing-l pointer-events-none absolute h-10 w-[9px] rounded-full bg-gradient-to-b from-violet-300/60 to-violet-700/10" />
          <span className="navi-wing-r pointer-events-none absolute h-10 w-[9px] rounded-full bg-gradient-to-b from-violet-300/60 to-violet-700/10" />
          <span className="navi-halo-btn pointer-events-none absolute h-12 w-12 rounded-full border border-violet-300/35" />
          <span
            className="navi-glow-pulse pointer-events-none absolute h-14 w-14 rounded-full"
            style={{ background: "radial-gradient(circle, rgba(139,92,246,0.65) 0%, rgba(139,92,246,0) 70%)" }}
          />
          <span className="navi-core pointer-events-none absolute h-6 w-6 rounded-full bg-white" />
        </Link>
      </div>

      <div className="text-center">
        <p className="text-sm font-semibold tracking-tight text-zinc-200">Oracle Orb</p>
        <p className="text-xs text-zinc-500 mt-0.5">Listening · Idle</p>
      </div>

      <div className="pointer-events-none flex h-5 items-end gap-[3px]">
        {Array.from({ length: 18 }).map((_, i) => (
          <span
            key={i}
            className="w-[3px] origin-bottom rounded-full bg-violet-500/50"
            style={{
              height: `${6 + ((i * 41 + 7) % 12)}px`,
              animation: `navi-bar ${0.7 + (i % 5) * 0.11}s ease-in-out infinite alternate`,
              animationDelay: `${i * 0.045}s`,
            }}
          />
        ))}
      </div>

      <Link
        href="/oracle"
        onTouchEnd={(e) => {
          e.preventDefault(); // iOS WebKit
          router.push("/oracle");
        }}
        className="mt-1 flex w-full cursor-pointer touch-manipulation items-center justify-center gap-2 rounded-xl border border-violet-500/25 bg-violet-500/10 py-2.5 text-xs font-semibold text-violet-300 transition-transform active:scale-[0.98]"
      >
        <Command size={12} className="pointer-events-none shrink-0" aria-hidden /> Open Oracle
      </Link>
    </BentoCard>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. BRIEFING HUB
// ─────────────────────────────────────────────────────────────────────────────
const BRIEFING = [
  { tag: "Local LLM", title: "Llama 3.3 Q4_K_M quant benchmarks on consumer DDR5 — context window throughput.",         time: "06:02" },
  { tag: "Homelab",   title: "PCIe x1 riser bottleneck: TTFT degradation on 24GB VRAM models vs x16 ribbon cables.",    time: "06:04" },
  { tag: "Privacy",   title: "CCPA Q3 enforcement: brokers ignoring opt-outs face record seven-figure penalties.",       time: "06:06" },
  { tag: "Energy",    title: "Southern CA ToU shift: super off-peak window narrows to 11 PM – 5 AM next billing.",      time: "06:08" },
];

function BriefingHub() {
  return (
    <BentoCard className="md:col-span-8">
      <div className="flex items-start justify-between mb-4 gap-3">
        <div className="min-w-0">
          <Label>Intelligence Briefing · 06:00</Label>
          <h2 className="text-base font-semibold tracking-tight text-zinc-100">Daily Briefing Hub</h2>
        </div>
        <span className="text-[10px] font-mono text-zinc-500 bg-white/5 border border-white/10 rounded-lg px-2 py-1 flex-shrink-0 whitespace-nowrap">
          Next: 03:00 AM
        </span>
      </div>
      <div className="space-y-2">
        {BRIEFING.map((item, i) => (
          <div key={i} className="flex items-start gap-2.5 p-3 rounded-xl bg-white/5 border border-white/5">
            <span className="text-[10px] font-semibold tracking-wider uppercase text-violet-400 bg-violet-500/10 border border-violet-500/20 rounded-lg px-2 py-0.5 mt-0.5 whitespace-nowrap flex-shrink-0">
              {item.tag}
            </span>
            <p className="text-xs text-zinc-300 flex-1 leading-snug min-w-0">{item.title}</p>
            <p className="text-[10px] text-zinc-600 whitespace-nowrap mt-0.5 flex-shrink-0 hidden sm:block">{item.time}</p>
          </div>
        ))}
      </div>
      <p className="text-[10px] text-zinc-600 mt-3 text-center">
        — SearXNG (local) · GPT-Researcher · No Google pings —
      </p>
    </BentoCard>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. LOCAL DRIVE HEALTH
// ─────────────────────────────────────────────────────────────────────────────
type SmartStatus = "Healthy" | "Warning" | "Unknown";
interface Drive { label: string; type: "SSD" | "HDD"; total: number; used: number; temp: number; smart: SmartStatus; }

const DRIVES: { node: string; drives: Drive[] }[] = [
  {
    node: "spiritdesktop · Node 1",
    drives: [
      { label: "250GB SSD", type: "SSD", total: 250,  used: 147, temp: 38, smart: "Healthy" },
      { label: "1TB HDD",   type: "HDD", total: 1000, used: 412, temp: 34, smart: "Healthy" },
      { label: "2TB HDD",   type: "HDD", total: 2000, used: 880, temp: 36, smart: "Healthy" },
    ],
  },
  {
    node: "spirit (Dell) · Node 2",
    drives: [
      { label: "Dell SSD",  type: "SSD", total: 512,  used: 198, temp: 41, smart: "Healthy" },
    ],
  },
];

function SmartBadge({ status }: { status: SmartStatus }) {
  if (status === "Healthy") return <span className="flex items-center gap-1 text-[10px] font-medium text-emerald-400"><ShieldCheck size={10} /> Healthy</span>;
  if (status === "Warning")  return <span className="flex items-center gap-1 text-[10px] font-medium text-amber-400"><ShieldAlert size={10} /> Warning</span>;
  return <span className="flex items-center gap-1 text-[10px] font-medium text-zinc-500"><ShieldAlert size={10} /> Unknown</span>;
}

function DriveHealthWidget() {
  const fmt = (n: number) => n >= 1000 ? `${(n / 1000).toFixed(0)} TB` : `${n} GB`;

  return (
    <BentoCard className="md:col-span-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <Label>Local Drive Health</Label>
          <h2 className="text-base font-semibold tracking-tight text-zinc-100">Storage</h2>
        </div>
        <HardDrive size={14} className="text-zinc-600 flex-shrink-0" />
      </div>
      <div className="space-y-5">
        {DRIVES.map((section) => (
          <div key={section.node}>
            <p className="text-[10px] font-mono font-semibold text-violet-400 mb-2.5">{section.node}</p>
            <div className="space-y-3">
              {section.drives.map((drive, di) => {
                const pct = Math.round((drive.used / drive.total) * 100);
                return (
                  <div key={di}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-1.5 min-w-0">
                        <span className={cn(
                          "text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded flex-shrink-0",
                          drive.type === "SSD" ? "bg-sky-500/15 text-sky-400 border border-sky-500/20" : "bg-zinc-700/60 text-zinc-400 border border-white/10"
                        )}>
                          {drive.type}
                        </span>
                        <span className="text-xs text-zinc-300 font-medium truncate">{drive.label}</span>
                      </div>
                      <span className="text-[10px] font-mono text-zinc-500 flex-shrink-0 ml-2">
                        {fmt(drive.used)} / {fmt(drive.total)}
                      </span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden mb-1.5">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.8, delay: 0.5 + di * 0.08, ease: "easeOut" }}
                        className={cn(
                          "h-full rounded-full transform-gpu",
                          pct >= 85 ? "bg-red-500/70" : pct >= 65 ? "bg-amber-500/65" : "bg-violet-500/65"
                        )}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <SmartBadge status={drive.smart} />
                      <span className="flex items-center gap-1 text-[10px] text-zinc-500">
                        <Thermometer size={9} className="text-zinc-600" />
                        {drive.temp}°C
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex items-center gap-2 bg-zinc-900/60 border border-white/10 rounded-xl px-3 py-2">
        <AlertTriangle size={11} className="text-zinc-600 flex-shrink-0" />
        <p className="text-[10px] text-zinc-500">Wire to <span className="font-mono text-zinc-400">smartctl</span> on Node 2 for live readings. Values are mock.</p>
      </div>
    </BentoCard>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. SYSTEM STATS
// ─────────────────────────────────────────────────────────────────────────────
const STATS = [
  {
    node: "spiritdesktop", sub: "Ryzen AM5 · XFX · DDR5",
    rows: [
      { label: "CPU · Ryzen AM5", value: 12,   display: "12%",     max: 100 },
      { label: "RAM · 16GB DDR5", value: 7.2,  display: "7.2 GB",  max: 16  },
      { label: "GPU · XFX",       value: 8,    display: "8%",      max: 100 },
    ],
    alert: { color: "sky" as const, text: "RAM bottleneck on 3-monitor Cursor workflow. Target: 32GB DDR5." },
  },
  {
    node: "spirit (Dell)", sub: "i7-6700 · 16GB DDR4",
    rows: [
      { label: "CPU · i7-6700",   value: 34,   display: "34%",     max: 100 },
      { label: "RAM · 16GB DDR4", value: 11.2, display: "11.2 GB", max: 16  },
    ],
    alert: null,
  },
  {
    node: "Ghost Node", sub: "Pi 3 · 1GB LPDDR2",
    rows: [
      { label: "CPU · ARM",        value: 22,   display: "22%",     max: 100 },
      { label: "RAM · 1GB LPDDR2", value: 0.54, display: "0.54 GB", max: 1   },
    ],
    alert: { color: "amber" as const, text: "FLIRC case pending. Watch for thermal throttle under DNS load." },
  },
];

function SystemStats() {
  return (
    <BentoCard className="md:col-span-8">
      <div className="flex items-center justify-between mb-4">
        <div>
          <Label>Node Vitals</Label>
          <h2 className="text-base font-semibold tracking-tight text-zinc-100">System Stats</h2>
        </div>
        <Cpu size={14} className="text-zinc-600 flex-shrink-0" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        {STATS.map((section, si) => (
          <div key={section.node}>
            <p className="text-[10px] font-mono font-semibold text-violet-400 mb-0.5 truncate">{section.node}</p>
            <p className="text-[10px] text-zinc-600 mb-2 truncate">{section.sub}</p>
            <div className="space-y-3">
              {section.rows.map((row, ri) => (
                <div key={ri}>
                  <div className="flex justify-between items-baseline mb-1">
                    <p className="text-[11px] text-zinc-500 truncate">{row.label}</p>
                    <p className="text-[11px] font-mono text-zinc-200 ml-2 flex-shrink-0">{row.display}</p>
                  </div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(row.value / row.max) * 100}%` }}
                      transition={{ duration: 0.8, delay: 0.45 + si * 0.06 + ri * 0.05, ease: "easeOut" }}
                      className="h-full rounded-full bg-violet-500/70 transform-gpu"
                    />
                  </div>
                </div>
              ))}
            </div>
            {section.alert && (
              <div className={cn("mt-3 rounded-xl px-2.5 py-1.5 flex items-start gap-1.5", section.alert.color === "amber" ? "bg-amber-500/10 border border-amber-500/20" : "bg-sky-500/10 border border-sky-500/20")}>
                <AlertTriangle size={11} className={cn("flex-shrink-0 mt-0.5", section.alert.color === "amber" ? "text-amber-400" : "text-sky-400")} />
                <p className={cn("text-[10px] leading-snug", section.alert.color === "amber" ? "text-amber-300" : "text-sky-300")}>{section.alert.text}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </BentoCard>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. ENERGY MATRIX
// ─────────────────────────────────────────────────────────────────────────────
const NODES = [
  { name: "spiritdesktop", sub: "Ryzen AM5 · XFX GPU",     wattage: 148, state: "active"  as const },
  { name: "spirit",        sub: "Dell i7-6700 · 16GB DDR4", wattage: 198, state: "active"  as const },
  { name: "Ghost Node",    sub: "Raspberry Pi 3 · 2017",    wattage: 4,   state: "active"  as const },
  { name: "Tesla P40",     sub: "24GB VRAM · Awaiting PSU", wattage: 0,   state: "pending" as const },
];

function EnergyMatrix() {
  const total = NODES.reduce((s, n) => s + n.wattage, 0);
  const costHr = ((total / 1000) * 0.11).toFixed(4);

  return (
    <BentoCard className="md:col-span-4">
      <div className="flex items-start justify-between mb-4 gap-3">
        <div className="min-w-0">
          <Label>Energy Matrix · Node 5</Label>
          <h2 className="text-xl font-semibold tracking-tight text-zinc-100">
            {total}<span className="text-sm text-zinc-500 font-normal ml-1">W</span>
          </h2>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-lg font-mono font-semibold text-emerald-400">$0.11<span className="text-xs text-zinc-500 font-normal">/kWh</span></p>
          <p className="text-[10px] text-emerald-600 font-medium">Super Off-Peak</p>
          <p className="text-xs text-zinc-500">${costHr}/hr</p>
        </div>
      </div>
      <div className="space-y-3">
        {NODES.map((node, i) => {
          const pct = total > 0 ? (node.wattage / total) * 100 : 0;
          const isPending = node.state === "pending";
          return (
            <div key={i}>
              <div className="flex items-center gap-2 mb-1">
                <span className={cn("w-1.5 h-1.5 rounded-full flex-shrink-0", isPending ? "bg-amber-500" : "bg-emerald-400")} />
                <span className="text-xs font-mono text-zinc-300 truncate flex-1 min-w-0">{node.name}</span>
                <span className={cn("text-xs font-mono flex-shrink-0", isPending ? "text-amber-500" : "text-zinc-400")}>
                  {isPending ? "PENDING" : `${node.wattage}W`}
                </span>
              </div>
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: isPending ? "0%" : `${pct}%` }}
                  transition={{ duration: 0.8, delay: 0.4 + i * 0.07, ease: "easeOut" }}
                  className="h-full rounded-full bg-violet-500/70 transform-gpu"
                />
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 rounded-xl px-3 py-2">
        <Clock size={12} className="text-amber-400 flex-shrink-0" />
        <p className="text-xs text-amber-300">Peak (2 PM – 7 PM) in <span className="font-semibold">6h 14m</span>. Heavy compute queued.</p>
      </div>
    </BentoCard>
  );
}

// ─── YTM Telemetry mock data ──────────────────────────────────────────────────

const CURRENT_TRACK = {
  title:       "Luther",
  artist:      "Kendrick Lamar ft. SZA",
  album:       "GNX",
  year:        2024,
  progress:    0.34,
  duration:    238,
  artGradient: "from-red-950/70 via-zinc-900 to-zinc-900",
  spiritTone:  "You've looped this 42 times. The concept of seeking help might warrant genuine consideration at this point.",
};

const TOP_TEN_REPEAT = [
  { rank: 1,  title: "Luther",         artist: "Kendrick Lamar",     plays: 312 },
  { rank: 2,  title: "Burning",        artist: "Doja Cat",           plays: 287 },
  { rank: 3,  title: "See You Again",  artist: "Tyler, the Creator", plays: 241 },
  { rank: 4,  title: "Kill Bill",      artist: "SZA",                plays: 198 },
  { rank: 5,  title: "Nights",         artist: "Frank Ocean",        plays: 176 },
  { rank: 6,  title: "BABUSHKA BOY",   artist: "A$AP Rocky",         plays: 156 },
  { rank: 7,  title: "N95",            artist: "Kendrick Lamar",     plays: 143 },
  { rank: 8,  title: "Lost One",       artist: "Kendrick Lamar",     plays: 131 },
  { rank: 9,  title: "Pyramids",       artist: "Frank Ocean",        plays: 118 },
  { rank: 10, title: "Noid",           artist: "Yeat",               plays: 104 },
];

// ─────────────────────────────────────────────────────────────────────────────
// 7. TOXIC GRADER
// ─────────────────────────────────────────────────────────────────────────────
const ROAST = [
  { pre: "GRADER >", text: "Querying Langfuse DB... pulling your last 24h of sessions.", color: "text-violet-400" },
  { pre: "GRADER >", text: "You fixed the same null reference error four consecutive times. Spectacular.", color: "text-amber-400" },
  { pre: "GRADER >", text: "Prompt efficiency: 34%. You are an expensive rubber duck with a standing desk.", color: "text-red-400" },
  { pre: "GRADER >", text: "47 minutes on one flexbox issue. Three lines of CSS. I have nothing to add.", color: "text-red-400" },
  { pre: "GRADE   >", text: "D+  —  Functional. Barely. Like a 2004 Civic with a cracked manifold.", color: "text-orange-300" },
  { pre: "SYSTEM  >", text: "Ready. Click [GRADE ME] when your ego has recovered.", color: "text-zinc-500" },
];

// ─────────────────────────────────────────────────────────────────────────────
// 8. LIVE PULSE — Now Playing
// ─────────────────────────────────────────────────────────────────────────────
function LivePulseWidget({
  livePlaying,
  onTogglePlaying,
}: {
  livePlaying:     boolean;
  onTogglePlaying: () => void;
}) {
  return (
    <BentoCard
      className={cn(
        "col-span-12 md:col-span-3 md:self-start",
        "bg-gradient-to-br p-3 md:p-3.5",
        CURRENT_TRACK.artGradient,
      )}
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <Label>YTM · Live</Label>
        <span className="flex flex-shrink-0 items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[9px] font-semibold text-emerald-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          Maloja
        </span>
      </div>

      <div className="mt-1 flex items-center gap-2.5">
        <div className="ytm-art-entrance h-8 w-8 flex-shrink-0 rounded-lg border border-white/[0.06] bg-zinc-800" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-semibold text-zinc-100">{CURRENT_TRACK.title}</p>
          <p className="truncate text-[10px] text-zinc-500">{CURRENT_TRACK.artist}</p>
        </div>
      </div>

      <div className="relative mt-2 h-[3px] w-full rounded-full bg-white/10">
        <div
          className="pointer-events-none absolute inset-y-0 left-0 w-full origin-left rounded-full bg-violet-500/70"
          style={{ transform: `scaleX(${CURRENT_TRACK.progress})`, transition: "transform 600ms ease-out" }}
        />
      </div>

      <div className="mt-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            aria-label={livePlaying ? "Pause" : "Play"}
            onClick={onTogglePlaying}
            onTouchEnd={(e) => { e.preventDefault(); onTogglePlaying(); }}
            className="flex h-7 w-7 cursor-pointer touch-manipulation items-center justify-center rounded-full bg-white text-zinc-950 transition-transform active:scale-95"
          >
            {livePlaying
              ? <Pause size={12} className="pointer-events-none" fill="currentColor" aria-hidden />
              : <Play  size={12} className="pointer-events-none" fill="currentColor"
                       style={{ transform: "translate3d(1px,0,0)" }} aria-hidden />}
          </button>
          <div className="pointer-events-none flex h-3.5 items-end gap-[2px]">
            {Array.from({ length: 4 }).map((_, i) => (
              <span
                key={i}
                className="w-[3px] origin-bottom rounded-full bg-violet-500/60"
                style={{
                  height:             `${6 + ((i * 31 + 5) % 6)}px`,
                  animation:          `navi-bar ${0.6 + (i % 4) * 0.12}s ease-in-out infinite alternate`,
                  animationDelay:     `${i * 0.07}s`,
                  animationPlayState: livePlaying ? "running" : "paused",
                }}
              />
            ))}
          </div>
        </div>
        <Link
          href="/ytm"
          className="text-[10px] font-semibold text-violet-400 transition-colors hover:text-violet-300"
        >
          → Open TYMDesktop
        </Link>
      </div>
    </BentoCard>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 9. ON REPEAT — Top 10
// ─────────────────────────────────────────────────────────────────────────────
function OnRepeatWidget() {
  return (
    <BentoCard className="col-span-12 md:col-span-5">
      {/* Header */}
      <div className="mb-3 flex items-start justify-between">
        <div className="flex items-center gap-1.5">
          <Music2 size={12} className="flex-shrink-0 text-violet-400" />
          <Label>On Repeat · Top 10</Label>
        </div>
        <Link
          href="/ytm"
          className="flex items-center gap-1 text-[10px] text-zinc-600 transition-colors hover:text-violet-400"
        >
          <ArrowRight size={11} className="pointer-events-none" aria-hidden />
        </Link>
      </div>

      {/* Track list — overflow-y-auto contains growth without blowing card height */}
      <div className="flex-1 divide-y divide-white/[0.04] overflow-y-auto" style={{ maxHeight: "340px" }}>
        {TOP_TEN_REPEAT.map((track) => (
          <div key={track.rank} className="on-repeat-row flex items-center gap-2.5 px-2 py-2">
            {/* Rank */}
            <span className="w-5 flex-shrink-0 text-right font-mono text-[10px] text-violet-400">
              {track.rank}
            </span>
            {/* Album art placeholder */}
            <div className="h-7 w-7 flex-shrink-0 rounded bg-zinc-800" />
            {/* Track + Artist */}
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium leading-none text-zinc-200">{track.title}</p>
              <p className="truncate text-[10px] text-zinc-500">{track.artist}</p>
            </div>
            {/* Play count — full-track spins (mock Maloja telemetry) */}
            <span
              className="flex flex-shrink-0 items-baseline gap-0.5 whitespace-nowrap rounded-full border border-white/[0.05] bg-zinc-900 px-2 py-0.5"
              title="Full-track plays (mock Maloja · rolling window)"
            >
              <span className="font-mono text-[9px] tabular-nums text-zinc-400">{track.plays}</span>
              <span className="text-[8px] font-medium uppercase tracking-wide text-zinc-600">plays</span>
            </span>
          </div>
        ))}
      </div>
    </BentoCard>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. TOXIC GRADER
// ─────────────────────────────────────────────────────────────────────────────
function ToxicGrader() {
  return (
    <BentoCard className="md:col-span-8 bg-zinc-950/90 border-red-900/25">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
          </div>
          <p className="text-[11px] font-mono text-zinc-600 ml-1 hidden sm:block">toxic-grader · langfuse-hook</p>
        </div>
        <div className="flex items-center gap-1">
          <Flame size={11} className="text-red-400" />
          <p className="text-[10px] font-semibold uppercase tracking-widest text-red-400">Roast Wall</p>
        </div>
      </div>
      <div className="font-mono text-[11px] space-y-1.5 mb-4">
        {ROAST.map((line, i) => (
          <div key={i} className="flex gap-2 leading-snug">
            <span className="text-zinc-700 select-none w-[60px] flex-shrink-0">{line.pre}</span>
            <span className={cn(line.color, "break-words min-w-0")}>{line.text}</span>
          </div>
        ))}
        <div className="flex gap-2">
          <span className="text-zinc-700 select-none w-[60px] flex-shrink-0">GRADER {">"}</span>
          <motion.span animate={{ opacity: [1, 0, 1] }} transition={{ duration: 1.1, repeat: Infinity }} className="text-zinc-400">█</motion.span>
        </div>
      </div>
      <button className="w-full py-2.5 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs font-semibold active:scale-[0.98] transition-transform flex items-center justify-center gap-2">
        <Terminal size={13} />
        GRADE ME — IF YOU DARE
      </button>
    </BentoCard>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// COMMAND BAR
// ─────────────────────────────────────────────────────────────────────────────
type ChatMsg = { role: "user" | "spirit"; text: string };
const INIT_MSGS: ChatMsg[] = [{ role: "spirit", text: "Source. Command bar online. What do you need?" }];
type SpiritStatus = "online" | "error";

function CommandBar({ onClose }: { onClose: () => void }) {
  const [msgs, setMsgs] = useState<ChatMsg[]>(INIT_MSGS);
  const [draft, setDraft] = useState("");
  const [thinking, setThinking] = useState(false);
  const [status, setStatus] = useState<SpiritStatus>("online");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { setCommandBarOpen } = useOverlayLock();

  useEffect(() => {
    setCommandBarOpen(true);
    return () => { setCommandBarOpen(false); };
  }, [setCommandBarOpen]);

  useEffect(() => { inputRef.current?.focus(); }, []);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, thinking]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);

  const send = async () => {
    const text = draft.trim();
    if (!text || thinking) return;
    setDraft("");
    setMsgs((m) => [...m, { role: "user", text }]);
    setThinking(true);
    setStatus("online");
    try {
      const res = await fetch("/api/spirit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: text }),
      });
      const data: unknown = await res.json().catch(() => ({}));
      if (!res.ok) {
        const errMsg =
          typeof data === "object" &&
          data !== null &&
          "error" in data &&
          typeof (data as { error: unknown }).error === "string"
            ? (data as { error: string }).error
            : `Request failed (${res.status})`;
        setStatus("error");
        setMsgs((m) => [...m, { role: "spirit", text: errMsg }]);
        return;
      }
      const reply =
        typeof data === "object" &&
        data !== null &&
        "reply" in data &&
        typeof (data as { reply: unknown }).reply === "string"
          ? (data as { reply: string }).reply
          : "";
      if (!reply) {
        setStatus("error");
        setMsgs((m) => [...m, { role: "spirit", text: "Empty reply from Spirit API." }]);
        return;
      }
      setStatus("online");
      setMsgs((m) => [...m, { role: "spirit", text: reply }]);
    } catch (e) {
      setStatus("error");
      const message = e instanceof Error ? e.message : "Network error";
      setMsgs((m) => [...m, { role: "spirit", text: `Spirit API error: ${message}` }]);
    } finally {
      setThinking(false);
    }
  };

  return (
    <>
      <div
        role="button"
        tabIndex={0}
        aria-label="Close command bar"
        className="fixed inset-0 z-[99998] cursor-pointer touch-manipulation bg-black/80"
        onClick={onClose}
        onTouchEnd={(e) => {
          e.preventDefault(); // iOS WebKit
          onClose();
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onClose(); }
        }}
      />
      <div className="fixed bottom-0 inset-x-0 z-[99999] transform-gpu sm:bottom-6 sm:left-1/2 sm:w-full sm:max-w-2xl sm:-translate-x-1/2 sm:px-4">
        <div
          className="flex flex-col overflow-hidden border-t border-white/10 bg-zinc-950 shadow-2xl sm:rounded-2xl sm:border"
          style={{ maxHeight: "65dvh" }}
        >
          <div className="flex flex-shrink-0 items-center justify-between border-b border-white/10 px-4 py-3">
            <div className="flex items-center gap-2">
              <div className="pointer-events-none flex h-5 w-5 items-center justify-center rounded-full border border-violet-500/40 bg-violet-500/20">
                <Zap size={10} className="text-violet-400" />
              </div>
              <p className="font-mono text-xs font-semibold text-zinc-300">Spirit · Command Bar</p>
              <span
                className={cn(
                  "rounded-full border px-2 py-0.5 text-[10px]",
                  status === "error"
                    ? "border-red-500/30 bg-red-500/10 text-red-300"
                    : "border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
                )}
              >
                {status === "error" ? "Error" : "Online"}
              </span>
            </div>
            <button
              type="button"
              onClick={onClose}
              onTouchEnd={(e) => {
                e.preventDefault(); // iOS WebKit
                onClose();
              }}
              aria-label="Close command bar"
              className="flex min-h-[44px] min-w-[44px] cursor-pointer touch-manipulation items-center justify-center rounded-lg p-2 text-zinc-500 transition-colors hover:bg-white/5 hover:text-zinc-300"
            >
              <X size={16} className="pointer-events-none" aria-hidden />
            </button>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
            {msgs.map((msg, i) => (
              <div key={i} className={cn("flex gap-2", msg.role === "user" ? "justify-end" : "justify-start")}>
                {msg.role === "spirit" && (
                  <div className="pointer-events-none mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full border border-violet-500/30 bg-violet-500/20">
                    <Zap size={9} className="text-violet-400" />
                  </div>
                )}
                <div className={cn(
                  "max-w-[85%] rounded-2xl px-3 py-2 text-xs leading-relaxed",
                  msg.role === "user"
                    ? "rounded-tr-sm border border-violet-500/25 bg-violet-500/20 text-zinc-200"
                    : "rounded-tl-sm border border-white/10 bg-white/5 font-mono text-zinc-300",
                )}>
                  {msg.text}
                </div>
              </div>
            ))}
            {thinking && (
              <div className="flex gap-2">
                <div className="pointer-events-none flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full border border-violet-500/30 bg-violet-500/20">
                  <Zap size={9} className="text-violet-400" />
                </div>
                <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm border border-white/10 bg-white/5 px-3 py-2.5">
                  {[0, 1, 2].map((d) => (
                    <span
                      key={d}
                      className="block h-1.5 w-1.5 animate-bounce rounded-full bg-violet-400"
                      style={{ animationDelay: `${d * 0.18}s` }}
                    />
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="flex flex-shrink-0 items-center gap-2 border-t border-white/10 bg-zinc-950 px-3 py-3">
            <input
              ref={inputRef}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void send(); }
              }}
              placeholder="Issue a command to Spirit..."
              className="min-w-0 flex-1 rounded-xl border border-white/10 bg-zinc-900 px-3 py-2.5 font-mono text-xs text-zinc-200 outline-none placeholder:text-zinc-600 transition-colors focus:border-violet-500/40"
            />
            <button
              type="button"
              onClick={() => void send()}
              onTouchEnd={(e) => {
                if (!draft.trim() || thinking) return;
                e.preventDefault(); // iOS WebKit
                void send();
              }}
              disabled={!draft.trim() || thinking}
              aria-label="Send"
              className="flex h-11 w-11 flex-shrink-0 cursor-pointer touch-manipulation items-center justify-center rounded-xl border border-violet-500/30 bg-violet-500/20 text-violet-300 transition-all hover:bg-violet-500/30 disabled:opacity-30 active:scale-95"
            >
              <Send size={13} className="pointer-events-none" aria-hidden />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// DASHBOARD CONTENT
// Accepts `projectWidget` as a React node slot from the Server Component page.
// ─────────────────────────────────────────────────────────────────────────────
export default function DashboardContent({
  projectWidget,
}: {
  projectWidget: React.ReactNode;
}) {
  const [chatOpen, setChatOpen] = useState(false);
  const [livePlaying, setLivePlaying] = useState(true);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") { e.preventDefault(); setChatOpen((o) => !o); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

  return (
    <div className="relative p-4 md:p-6">
      <div className="relative z-[1] mb-5 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-xl md:text-2xl font-semibold tracking-tight text-zinc-100 truncate">Trinity Dashboard</h1>
          <p className="text-xs md:text-sm text-zinc-500 mt-0.5 truncate">
            Source · Intuitive Wrld · <span className="text-emerald-400 font-medium">All nodes nominal</span>
          </p>
        </div>
        <button
          type="button"
          onClick={() => setChatOpen(true)}
          onTouchEnd={(e) => {
            e.preventDefault(); // iOS WebKit
            setChatOpen(true);
          }}
          aria-label="Open Command Bar"
          className="pointer-events-auto relative z-[99999] flex min-h-[44px] shrink-0 touch-manipulation cursor-pointer items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-zinc-400 transition-transform active:scale-95"
        >
          <Command size={13} className="pointer-events-none shrink-0" aria-hidden />
          <span className="hidden sm:inline">Command Bar</span>
          <kbd className="hidden md:inline text-[10px] bg-white/10 px-1.5 py-0.5 rounded font-mono">⌘K</kbd>
        </button>
      </div>

      <div className="grid grid-cols-12 gap-4">
        <OracleOrb />
        <LivePulseWidget livePlaying={livePlaying} onTogglePlaying={() => setLivePlaying((p) => !p)} />
        <OnRepeatWidget />
        <BriefingHub />
        {projectWidget}
        <DriveHealthWidget />
        <SystemStats />
        <EnergyMatrix />
        <ToxicGrader />
      </div>

      {chatOpen && <CommandBar onClose={() => setChatOpen(false)} />}
    </div>
  );
}
