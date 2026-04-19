"use client";

import { useState, useEffect, useCallback, type CSSProperties } from "react";
import {
  Music2, SkipBack, SkipForward, Play, Pause,
  Volume2, Heart, ListMusic, Radio, Share2,
  Flame, TrendingUp, Clock, X,
  Home, Compass, Library, BarChart3, Plus, Search,
} from "lucide-react";

// ─── Mock data ────────────────────────────────────────────────────────────────

const MOCK_TRACK = {
  title:    "Luther",
  artist:   "Kendrick Lamar ft. SZA",
  album:    "GNX",
  duration: 238,
};

const TOP_ARTISTS = [
  { name: "Kendrick Lamar",         plays: 1_204, pct: 100, trend: "+18%" },
  { name: "Doja Cat",               plays:   847, pct:  70, trend: "+12%" },
  { name: "Tyler, the Creator",     plays:   634, pct:  53, trend:  "+3%" },
  { name: "SZA",                    plays:   421, pct:  35, trend:  "-2%" },
  { name: "Frank Ocean",            plays:   398, pct:  33, trend:    "—" },
];

const TOP_SONGS = [
  { rank: 1, title: "Luther",          artist: "Kendrick Lamar",      plays: 312 },
  { rank: 2, title: "Burning",         artist: "Doja Cat",            plays: 287 },
  { rank: 3, title: "See You Again",   artist: "Tyler, the Creator",  plays: 241 },
  { rank: 4, title: "Kill Bill",       artist: "SZA",                 plays: 198 },
  { rank: 5, title: "Nights",          artist: "Frank Ocean",         plays: 176 },
];

const MOOD_SETS = [
  { name: "Late Night Sessions", sub: "11 PM – 3 AM · 1,240 plays",  active: true,  icon: "🌙" },
  { name: "Focus Mode",          sub: "9 AM – 1 PM · 876 plays",     active: true,  icon: "⚡" },
  { name: "Weekend Binge",       sub: "Sat/Sun · 2,100 plays",       active: false, icon: "🔥" },
  { name: "Morning Drive",       sub: "7 AM – 9 AM · 312 plays",     active: false, icon: "☀️" },
];

const SCROBBLES = [
  { title: "Luther",         artist: "Kendrick Lamar",      ago: "2m ago"  },
  { title: "Burning",        artist: "Doja Cat",            ago: "8m ago"  },
  { title: "Noid",           artist: "Yeat",                ago: "14m ago" },
  { title: "See You Again",  artist: "Tyler, the Creator",  ago: "21m ago" },
  { title: "Kill Bill",      artist: "SZA",                 ago: "29m ago" },
  { title: "Pyramids",       artist: "Frank Ocean",         ago: "37m ago" },
  { title: "Money Trees",    artist: "Kendrick Lamar",      ago: "44m ago" },
  { title: "BABUSHKA BOY",   artist: "A$AP Rocky",          ago: "52m ago" },
];

// Deterministic heatmap — [time band 0-4][day 0-6 Mon→Sun]
// Higher values = later evening, weekends peak. No Math.random() — SSR safe.
const HEATMAP: number[][] = [
  [0.10, 0.08, 0.15, 0.10, 0.12, 0.28, 0.42], // 12a – 6a
  [0.22, 0.30, 0.25, 0.28, 0.20, 0.52, 0.60], // 6a – 12p
  [0.45, 0.52, 0.48, 0.50, 0.42, 0.72, 0.68], // 12p – 6p
  [0.72, 0.65, 0.70, 0.68, 0.85, 0.90, 0.82], // 6p – 10p
  [0.90, 0.72, 0.85, 0.74, 0.95, 0.88, 0.80], // 10p – 12a
];
const HEATMAP_TIMES = ["12a – 6a", "6a – 12p", "12p – 6p", "6p – 10p", "10p – 12a"];
const HEATMAP_DAYS  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

// 14-day plays (deterministic, ascending trend)
const PLAYS_CHART = [24, 41, 18, 56, 72, 48, 33, 61, 88, 45, 37, 64, 52, 79];

const LISTEN_AGAIN = [
  "Kendrick Lamar", "Doja Cat", "Tyler, the Creator",
  "Frank Ocean", "SZA", "A$AP Rocky", "Yeat", "Playboi Carti",
];

const MIXED_FOR_YOU = [
  { name: "My Supermix",    sub: "Based on your history",  gradient: "from-violet-900/60 to-violet-950/80" },
  { name: "Discover Mix",   sub: "Fresh picks · Weekly",     gradient: "from-emerald-900/60 to-zinc-900" },
  { name: "Late Night Mix", sub: "Your 11 PM sessions",      gradient: "from-blue-900/60 to-zinc-900" },
  { name: "Focus Flow",     sub: "Instrumental & chill",     gradient: "from-red-900/60 to-zinc-900" },
];

const RECOMMENDED = [
  { title: "Not Like Us",       artist: "Kendrick Lamar" },
  { title: "Agora Hills",       artist: "Doja Cat" },
  { title: "SORRY NOT SORRY",   artist: "Bryson Tiller" },
  { title: "Victoria's Secret", artist: "Jax" },
  { title: "Rich Flex",         artist: "Drake & 21 Savage" },
  { title: "Break My Soul",     artist: "Beyoncé" },
];

const SIDEBAR_PLAYLISTS = [
  "Late Night Drive", "Focus Mode", "Workout Grind", "Chill Sunday", "Rap God Mode",
];

type YTMView = "home" | "explore" | "library" | "analytics";

// ─── Utilities ────────────────────────────────────────────────────────────────

function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

function formatTime(secs: number) {
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-3 text-[10px] font-semibold uppercase tracking-widest text-zinc-500">
      {children}
    </p>
  );
}

// ─── Scrubber ─────────────────────────────────────────────────────────────────
//
// Custom div-based; NOT <input type="range"> — iOS Safari renders it with
// system chrome and triggers layout repaints on every value change.
// scaleX on the fill runs on the GPU compositor thread (no repaints at all).
//
interface ScrubberProps {
  value:     number;
  onChange:  (v: number) => void;
  className?: string;
}

function Scrubber({ value, onChange, className = "" }: ScrubberProps) {
  const resolve = useCallback((clientX: number, rect: DOMRect) => {
    onChange(Math.max(0, Math.min(1, (clientX - rect.left) / rect.width)));
  }, [onChange]);

  return (
    <div
      className={cn("group relative h-1 cursor-pointer rounded-full bg-white/10", className)}
      onClick={(e) => resolve(e.clientX, e.currentTarget.getBoundingClientRect())}
      onTouchEnd={(e) => {
        e.preventDefault();
        resolve(e.changedTouches[0].clientX, e.currentTarget.getBoundingClientRect());
      }}
    >
      {/* Fill — scaleX is compositor-only on iOS; zero layout repaints */}
      <div
        className="pointer-events-none absolute inset-y-0 left-0 w-full origin-left rounded-full bg-violet-500/80"
        style={{ transform: `scaleX(${value})`, transition: "transform 200ms linear" }}
      />
      {/* Hover thumb — translate3d keeps it on the GPU compositor layer */}
      <div
        className="pointer-events-none absolute top-1/2 h-3.5 w-3.5 -translate-y-1/2 rounded-full bg-white opacity-0 shadow transition-opacity group-hover:opacity-100"
        style={{ left: `${value * 100}%`, transform: `translate3d(-50%, -50%, 0)` }}
      />
    </div>
  );
}

// ─── Scrobble Feed ────────────────────────────────────────────────────────────

function ScrobbleFeed({ onClose }: { onClose?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-shrink-0 items-center justify-between border-b border-white/[0.06] px-4 py-3">
        <div className="flex items-center gap-2">
          <Radio size={11} className="flex-shrink-0 text-emerald-400" />
          <p className="text-[11px] font-semibold text-zinc-300">Live Scrobble Feed</p>
          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 font-mono text-[9px] font-bold text-emerald-400">
            Maloja ●
          </span>
        </div>
        {onClose && (
          <button
            type="button"
            aria-label="Close scrobble feed"
            onClick={onClose}
            onTouchEnd={(e) => { e.preventDefault(); onClose(); }}
            className="flex h-8 w-8 cursor-pointer touch-manipulation items-center justify-center rounded-lg text-zinc-500 hover:text-zinc-300"
          >
            <X size={14} className="pointer-events-none" aria-hidden />
          </button>
        )}
      </div>

      <div
        className="flex-1 divide-y divide-white/[0.04] overflow-y-auto overscroll-none pb-[140px] md:pb-[90px]"
      >
        {SCROBBLES.map((s, i) => (
          <div key={i} className="flex items-center gap-3 px-4 py-2.5">
            <div className="h-8 w-8 flex-shrink-0 rounded-md bg-zinc-800" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium text-zinc-200">{s.title}</p>
              <p className="truncate text-[10px] text-zinc-500">{s.artist}</p>
            </div>
            <span className="flex-shrink-0 font-mono text-[10px] tabular-nums text-zinc-600">{s.ago}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Heatmap (shared between Player and Analytics views) ─────────────────────

function ListeningHeatmap({ mounted }: { mounted: boolean }) {
  return (
    <div className="flex gap-3">
      {/* Time-band labels */}
      <div className="flex w-16 flex-shrink-0 flex-col justify-between py-0.5">
        {HEATMAP_TIMES.map((t) => (
          <span key={t} className="font-mono text-[8px] leading-none text-zinc-600">{t}</span>
        ))}
      </div>
      {/* Grid */}
      <div className="flex flex-1 flex-col gap-1.5">
        {/* Day headers */}
        <div className="flex gap-1.5">
          {HEATMAP_DAYS.map((d) => (
            <span key={d} className="flex-1 text-center font-mono text-[9px] text-zinc-600">{d}</span>
          ))}
        </div>
        {/* Cells — rgba alpha baked in, not CSS opacity (avoids WebKit stack compositing issues) */}
        {HEATMAP.map((row, ri) => (
          <div key={ri} className="flex gap-1.5">
            {row.map((intensity, di) => (
              <div
                key={di}
                className="h-4 flex-1 rounded-sm"
                style={{
                  background:  `rgba(139, 92, 246, ${mounted ? intensity : 0.04})`,
                  transition:  `background 600ms ease-out ${(ri * 7 + di) * 16}ms`,
                }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Home View (TYMDesktop home) ───────────────────────────────────────────────

function HomeView() {
  return (
    <div className="space-y-8 p-5">
      <div className="flex items-center gap-3 rounded-full border border-white/10 bg-zinc-900 px-4 py-2.5">
        <Search size={14} className="flex-shrink-0 text-zinc-500" aria-hidden />
        <span className="text-sm text-zinc-600">Search songs, artists, albums…</span>
      </div>

      <section>
        <Label>Listen Again</Label>
        <div className="flex gap-4 overflow-x-auto pb-2 overscroll-none">
          {LISTEN_AGAIN.map((name) => (
            <div key={name} className="flex w-20 flex-shrink-0 flex-col items-center gap-2">
              <div className="h-20 w-20 flex-shrink-0 rounded-full bg-zinc-800" />
              <p className="line-clamp-2 text-center text-[10px] text-zinc-400">{name}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <Label>Mixed for You</Label>
        <div className="flex gap-3 overflow-x-auto pb-2 overscroll-none">
          {MIXED_FOR_YOU.map((mix) => (
            <div
              key={mix.name}
              className={cn(
                "flex h-40 w-40 flex-shrink-0 flex-col justify-end rounded-xl border border-white/[0.06] bg-gradient-to-br p-3",
                mix.gradient,
              )}
            >
              <p className="text-xs font-semibold text-zinc-100">{mix.name}</p>
              <p className="text-[10px] text-zinc-500">{mix.sub}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <Label>Recommended Music</Label>
        <div className="grid grid-cols-2 gap-3">
          {RECOMMENDED.map((r) => (
            <div
              key={r.title}
              className="flex gap-3 rounded-xl border border-white/[0.07] bg-zinc-900/60 p-3"
            >
              <div className="h-10 w-10 flex-shrink-0 rounded-lg bg-zinc-800" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium text-zinc-200">{r.title}</p>
                <p className="truncate text-[10px] text-zinc-500">{r.artist}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function ExploreView() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center p-8">
      <p className="text-sm text-zinc-500">Coming soon</p>
    </div>
  );
}

function LibraryView() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center p-8">
      <p className="text-sm text-zinc-500">Coming soon</p>
    </div>
  );
}

// ─── Analytics View (merged former Player + Analytics tabs) ─────────────────

function AnalyticsView({ mounted }: { mounted: boolean }) {
  const maxPlays = Math.max(...PLAYS_CHART);

  return (
    <div className="space-y-8 p-5">

      {/* Top Artists bar chart */}
      <section>
        <Label>Top Artists · Last 30 Days</Label>
        <div className="space-y-3">
          {TOP_ARTISTS.map((artist, i) => (
            <div key={artist.name} className="flex items-center gap-3">
              <span className="w-4 flex-shrink-0 text-right font-mono text-[10px] text-zinc-600">{i + 1}</span>
              <div className="min-w-0 flex-1">
                <div className="mb-1.5 flex items-center justify-between gap-2">
                  <span className="truncate text-xs font-medium text-zinc-200">{artist.name}</span>
                  <div className="flex flex-shrink-0 items-center gap-2">
                    <span className="font-mono text-[10px] text-zinc-500">{artist.plays.toLocaleString()}</span>
                    <span className={cn(
                      "font-mono text-[9px] font-semibold",
                      artist.trend.startsWith("+") ? "text-emerald-400"
                        : artist.trend.startsWith("-") ? "text-red-400"
                        : "text-zinc-600"
                    )}>{artist.trend}</span>
                  </div>
                </div>
                <div className="relative h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className="absolute inset-y-0 left-0 w-full origin-left rounded-full bg-gradient-to-r from-violet-500/80 to-violet-700/50"
                    style={{
                      transform:         `scaleX(${mounted ? artist.pct / 100 : 0})`,
                      transition:        `transform 750ms ease-out ${60 + i * 80}ms`,
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <Label>Top Songs · All Time</Label>
        <div className="divide-y divide-white/[0.04]">
          {TOP_SONGS.map((song) => (
            <div key={song.rank} className="flex items-center gap-3 py-2.5">
              <span className="w-4 flex-shrink-0 text-right font-mono text-[10px] text-zinc-600">{song.rank}</span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium text-zinc-200">{song.title}</p>
                <p className="truncate text-[10px] text-zinc-500">{song.artist}</p>
              </div>
              <span className="flex-shrink-0 rounded-full border border-white/[0.07] bg-white/[0.03] px-2 py-0.5 font-mono text-[9px] text-zinc-500">
                {song.plays}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section>
        <Label>Mood Sets · Detected by Maloja</Label>
        <div className="flex gap-3 overflow-x-auto pb-2">
          {MOOD_SETS.map((mood) => (
            <div
              key={mood.name}
              className={cn(
                "flex w-52 flex-shrink-0 flex-col gap-2 rounded-2xl border p-4",
                mood.active
                  ? "border-violet-500/25 bg-violet-500/10"
                  : "border-white/[0.07] bg-zinc-900/60"
              )}
            >
              <div className="flex items-center gap-2">
                <span className="text-base leading-none">{mood.icon}</span>
                {mood.active && <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />}
              </div>
              <p className="text-xs font-semibold text-zinc-100">{mood.name}</p>
              <p className="text-[10px] text-zinc-500">{mood.sub}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <Label>Your Wrapped · 2025</Label>
        <div className="rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-500/15 via-violet-500/5 to-transparent p-5">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <p className="text-[10px] uppercase tracking-widest text-violet-400/70">Top Artist</p>
              <p className="text-lg font-bold tracking-tight text-zinc-100">Kendrick Lamar</p>
            </div>
            <div className="text-right">
              <p className="text-[10px] uppercase tracking-widest text-violet-400/70">Total Hours</p>
              <p className="font-mono text-lg font-bold tracking-tight text-zinc-100">847</p>
            </div>
          </div>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[10px] uppercase tracking-widest text-violet-400/70">Top Track</p>
              <p className="text-xs font-semibold text-zinc-200">Luther</p>
            </div>
            <button
              type="button"
              className="flex cursor-pointer touch-manipulation items-center gap-2 rounded-xl border border-violet-500/30 bg-violet-500/20 px-3 py-2 text-[11px] font-semibold text-violet-300 transition-transform active:scale-95"
            >
              <Share2 size={11} className="pointer-events-none" aria-hidden />
              Export Wrapped
            </button>
          </div>
        </div>
      </section>

      {/* Plays-per-day bar chart */}
      <section>
        <Label>Plays Per Day · Last 14 Days</Label>
        <div className="flex h-24 items-end gap-[3px]">
          {PLAYS_CHART.map((count, i) => (
            <div
              key={i}
              className="flex-1 origin-bottom rounded-t-sm bg-violet-500/55"
              style={{
                transform:  `scaleY(${mounted ? count / maxPlays : 0})`,
                transition: `transform 600ms ease-out ${i * 28}ms`,
              }}
              title={`${count} plays`}
            />
          ))}
        </div>
        <div className="mt-1 flex justify-between">
          <span className="font-mono text-[9px] text-zinc-600">14d ago</span>
          <span className="font-mono text-[9px] text-zinc-600">Today</span>
        </div>
      </section>

      {/* Top 3 Podium */}
      <section>
        <Label>Top 3 Artists · All-Time Podium</Label>
        <div className="flex items-end justify-center gap-3">
          {/* 2nd place */}
          <div className="flex flex-1 flex-col items-center gap-2">
            <p className="w-full truncate text-center text-[10px] font-semibold text-zinc-400">{TOP_ARTISTS[1].name}</p>
            <div
              className="flex w-full items-center justify-center rounded-t-xl border border-white/[0.07] bg-zinc-700/60"
              style={{ height: "80px" }}
            >
              <span className="font-mono text-2xl font-bold text-zinc-400">2</span>
            </div>
          </div>
          {/* 1st place */}
          <div className="flex flex-1 flex-col items-center gap-2">
            <p className="w-full truncate text-center text-[10px] font-semibold text-violet-300">{TOP_ARTISTS[0].name}</p>
            <div
              className="flex w-full items-center justify-center rounded-t-xl border border-violet-500/30 bg-violet-500/25"
              style={{ height: "112px" }}
            >
              <span className="font-mono text-2xl font-bold text-violet-300">1</span>
            </div>
          </div>
          {/* 3rd place */}
          <div className="flex flex-1 flex-col items-center gap-2">
            <p className="w-full truncate text-center text-[10px] font-semibold text-amber-400/70">{TOP_ARTISTS[2].name}</p>
            <div
              className="flex w-full items-center justify-center rounded-t-xl border border-amber-500/15 bg-amber-500/10"
              style={{ height: "64px" }}
            >
              <span className="font-mono text-2xl font-bold text-amber-400/70">3</span>
            </div>
          </div>
        </div>
      </section>

      {/* Listening Streak + Heatmap */}
      <section>
        <div className="mb-4 flex items-center gap-3">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500">Listening Streak</p>
          <span className="ml-auto flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-400">
            <Flame size={11} className="pointer-events-none" /> 14-day streak
          </span>
        </div>
        <ListeningHeatmap mounted={mounted} />
      </section>

      {/* All-Time Stats */}
      <section>
        <Label>All-Time Stats</Label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "Total Plays",     value: "12,847", Icon: Music2      },
            { label: "Unique Artists",  value: "284",    Icon: TrendingUp  },
            { label: "Hours Listened",  value: "847",    Icon: Clock       },
          ].map(({ label, value, Icon }) => (
            <div key={label} className="rounded-2xl border border-white/[0.07] bg-zinc-900 p-3.5 text-center">
              <Icon size={14} className="mx-auto mb-1.5 text-violet-400" />
              <p className="font-mono text-base font-bold text-zinc-100">{value}</p>
              <p className="text-[10px] text-zinc-500">{label}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

// ─── Electron desktop chrome (drag-region mock) ──────────────────────────────

function ElectronChrome() {
  return (
    <div
      className="hidden h-9 flex-shrink-0 cursor-default select-none items-center border-b border-white/[0.06] bg-zinc-950 px-3 md:flex"
      style={{ WebkitAppRegion: "drag" } as CSSProperties}
    >
      <div className="flex flex-1 items-center gap-1.5">
        <span className="h-3 w-3 rounded-full bg-red-500/80" />
        <span className="h-3 w-3 rounded-full bg-amber-500/80" />
        <span className="h-3 w-3 rounded-full bg-emerald-500/80" />
      </div>
      <p className="flex-1 text-center text-[11px] font-medium text-zinc-500">Spirit YTM Desktop</p>
      <div className="flex-1" />
    </div>
  );
}

function Sidebar({
  activeView,
  onViewChange,
}: {
  activeView:   YTMView;
  onViewChange: (v: YTMView) => void;
}) {
  const items: { id: YTMView; label: string; Icon: typeof Home }[] = [
    { id: "home",      label: "Home",    Icon: Home },
    { id: "explore",   label: "Explore", Icon: Compass },
    { id: "library",   label: "Library", Icon: Library },
    { id: "analytics", label: "Stats",   Icon: BarChart3 },
  ];
  return (
    <aside className="hidden w-[220px] flex-shrink-0 flex-col border-r border-white/[0.06] bg-zinc-950 md:flex">
      <div className="flex items-center gap-2 px-4 py-4">
        <Music2 size={18} className="flex-shrink-0 text-red-400" aria-hidden />
        <span className="text-sm font-semibold text-zinc-100">Spirit YTM</span>
      </div>
      <nav className="flex-1 space-y-0.5 overflow-y-auto overscroll-none px-2 pb-2">
        {items.map(({ id, label, Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => onViewChange(id)}
            onTouchEnd={(e) => { e.preventDefault(); onViewChange(id); }}
            className={cn(
              "flex w-full cursor-pointer touch-manipulation items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-xs font-medium transition-transform",
              activeView === id
                ? "bg-white/[0.08] text-zinc-100"
                : "text-zinc-500 hover:bg-white/[0.04] hover:text-zinc-300",
              "active:[transform:scale3d(0.97,0.97,1)]",
            )}
          >
            <Icon size={16} className="pointer-events-none flex-shrink-0" aria-hidden />
            {label}
          </button>
        ))}
      </nav>
      <div className="px-3 py-2">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-zinc-600">Playlists</p>
        <div className="max-h-40 space-y-0.5 overflow-y-auto overscroll-none">
          {SIDEBAR_PLAYLISTS.map((name) => (
            <button
              key={name}
              type="button"
              onClick={() => {}}
              onTouchEnd={(e) => { e.preventDefault(); }}
              className="block w-full truncate rounded-lg px-2 py-1.5 text-left text-[11px] text-zinc-500 hover:text-zinc-300"
            >
              {name}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-auto border-t border-white/[0.06] p-2">
        <button
          type="button"
          onClick={() => {}}
          onTouchEnd={(e) => { e.preventDefault(); }}
          className="flex w-full cursor-pointer touch-manipulation items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-zinc-400 active:[transform:scale3d(0.97,0.97,1)]"
        >
          <Plus size={13} className="pointer-events-none" aria-hidden />
          Create Playlist
        </button>
      </div>
    </aside>
  );
}

function MobileDock({
  playing,
  onTogglePlay,
  activeView,
  onViewChange,
}: {
  playing:      boolean;
  onTogglePlay: () => void;
  activeView:   YTMView;
  onViewChange: (v: YTMView) => void;
}) {
  const tabs: { id: YTMView; label: string; Icon: typeof Home }[] = [
    { id: "home",      label: "Home",    Icon: Home },
    { id: "explore",   label: "Explore", Icon: Compass },
    { id: "library",   label: "Library", Icon: Library },
    { id: "analytics", label: "Stats",   Icon: BarChart3 },
  ];
  return (
    <div className="fixed bottom-0 left-0 right-0 z-[9000] border-t border-white/[0.08] bg-zinc-950 md:hidden">
      <div className="flex items-center gap-3 border-b border-white/[0.06] px-4 py-2">
        <div className="h-8 w-8 flex-shrink-0 rounded-md bg-zinc-800" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-semibold text-zinc-100">{MOCK_TRACK.title}</p>
          <p className="truncate text-[10px] text-zinc-500">{MOCK_TRACK.artist}</p>
        </div>
        <button
          type="button"
          aria-label={playing ? "Pause" : "Play"}
          onClick={onTogglePlay}
          onTouchEnd={(e) => { e.preventDefault(); onTogglePlay(); }}
          className="flex h-8 w-8 cursor-pointer touch-manipulation items-center justify-center rounded-full bg-white text-zinc-950 transition-transform active:[transform:scale3d(0.95,0.95,1)]"
        >
          {playing
            ? <Pause size={14} className="pointer-events-none" fill="currentColor" aria-hidden />
            : <Play  size={14} className="pointer-events-none" fill="currentColor"
                    style={{ transform: "translate3d(1px,0,0)" }} aria-hidden />}
        </button>
      </div>
      <div
        className="flex justify-around pt-2"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        {tabs.map(({ id, label, Icon }) => (
          <button
            key={id}
            type="button"
            aria-label={label}
            onClick={() => onViewChange(id)}
            onTouchEnd={(e) => { e.preventDefault(); onViewChange(id); }}
            className={cn(
              "flex min-w-[56px] flex-col items-center gap-0.5 pb-1 transition-transform active:[transform:scale3d(0.92,0.92,1)]",
              activeView === id ? "text-violet-400" : "text-zinc-600",
            )}
          >
            <Icon size={20} className="pointer-events-none" aria-hidden />
            <span className="text-[9px] font-medium">{label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Page root ────────────────────────────────────────────────────────────────

export default function YTMPage() {
  const [playing,          setPlaying]          = useState(false);
  const [progress,         setProgress]         = useState(0.34);
  const [volume,           setVolume]           = useState(0.72);
  const [scrobbleFeedOpen, setScrobbleFeedOpen] = useState(false);
  const [mounted,          setMounted]          = useState(false);
  const [activeView,       setActiveView]       = useState<YTMView>("home");

  // Staggered mount flag — drives CSS entrance transitions on charts
  useEffect(() => {
    const id = setTimeout(() => setMounted(true), 80);
    return () => clearTimeout(id);
  }, []);

  // Prevent body rubber-band bounce while on /ytm (PWA feel).
  // Restores the previous value on route unmount.
  useEffect(() => {
    const prev = document.body.style.overscrollBehavior;
    document.body.style.overscrollBehavior = "none";
    return () => { document.body.style.overscrollBehavior = prev; };
  }, []);

  const togglePlay = useCallback(() => setPlaying((p) => !p), []);

  const elapsed = formatTime(progress * MOCK_TRACK.duration);
  const total   = formatTime(MOCK_TRACK.duration);

  return (
    /*
      Height model:
        Mobile — AppShell MobileNav: YTM root uses calc(100dvh - 60px).
        Desktop — Full 100dvh. Electron chrome + sidebar + main + scrobble rail.
      Mobile: MobileDock is fixed bottom (mini-player + tab bar). env(safe-area)
        padding only on the tab row — avoids double-padding the mini-player.
    */
    <div className="flex h-[calc(100dvh-60px)] flex-col overflow-hidden md:h-[100dvh]">
      <ElectronChrome />

      {/* Mobile: scrobble toggle + title (sidebar hidden) */}
      <div className="flex flex-shrink-0 items-center justify-between gap-3 border-b border-white/[0.06] px-4 py-2.5 md:hidden">
        <div className="flex min-w-0 items-center gap-2">
          <Music2 size={15} className="flex-shrink-0 text-violet-400" aria-hidden />
          <span className="truncate text-sm font-semibold text-zinc-100">Spirit YTM</span>
        </div>
        <button
          type="button"
          aria-label="Open scrobble feed"
          onClick={() => setScrobbleFeedOpen(true)}
          onTouchEnd={(e) => { e.preventDefault(); setScrobbleFeedOpen(true); }}
          className="flex h-8 w-8 cursor-pointer touch-manipulation items-center justify-center rounded-xl border border-white/10 bg-white/5 text-zinc-400 active:bg-white/10"
        >
          <ListMusic size={14} className="pointer-events-none" aria-hidden />
        </button>
      </div>

      <div className="flex min-h-0 flex-1 overflow-hidden">
        <Sidebar activeView={activeView} onViewChange={setActiveView} />

        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <div className="hidden flex-shrink-0 items-center justify-between gap-3 border-b border-white/[0.06] px-5 py-3 md:flex">
            <div className="flex min-w-0 items-center gap-3">
              <Music2 size={16} className="flex-shrink-0 text-violet-400" aria-hidden />
              <div className="min-w-0">
                <h1 className="text-sm font-semibold tracking-tight text-zinc-100">YTM Intelligence Hub</h1>
                <p className="text-[10px] text-zinc-500">ytmusicapi · Mock</p>
              </div>
            </div>
            <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-400">
              <Heart size={9} className="pointer-events-none" aria-hidden /> Bi-directional sync active
            </span>
          </div>

          <div className="flex min-h-0 flex-1 overflow-hidden">
            <main
              className="flex-1 overflow-y-auto overscroll-none pb-[130px] md:pb-[90px]"
            >
              {activeView === "home"      && <HomeView />}
              {activeView === "explore"   && <ExploreView />}
              {activeView === "library"   && <LibraryView />}
              {activeView === "analytics" && <AnalyticsView mounted={mounted} />}
            </main>

            <aside className="hidden min-h-0 w-72 flex-shrink-0 flex-col overflow-hidden border-l border-white/[0.06] md:flex">
              <ScrobbleFeed />
            </aside>
          </div>
        </div>
      </div>

      {/* ── Mobile: Scrobble feed slide-over (conditional DOM mount) ──────── */}
      {/*
        Nuclear iOS pattern: conditional mount means WebKit gets fresh DOM nodes
        on every open — no cached compositor layer, no ghost tap zones.
        No backdrop-filter — solid bg-zinc-950 on the panel, black/60 on the
        backdrop. Both paint reliably under GPU pressure.
      */}
      {scrobbleFeedOpen && (
        <>
          <div
            role="button"
            tabIndex={0}
            aria-label="Close scrobble feed"
            className="fixed inset-0 z-[7999] cursor-pointer bg-black/60 md:hidden"
            onClick={() => setScrobbleFeedOpen(false)}
            onTouchEnd={(e) => { e.preventDefault(); setScrobbleFeedOpen(false); }}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                setScrobbleFeedOpen(false);
              }
            }}
          />
          <div className="fixed inset-y-0 right-0 z-[8000] flex w-[85vw] max-w-sm transform-gpu flex-col border-l border-white/10 bg-zinc-950 md:hidden">
            <ScrobbleFeed onClose={() => setScrobbleFeedOpen(false)} />
          </div>
        </>
      )}

      {/* ── Desktop: full Now Playing bar (mobile uses MobileDock below) ─── */}
      {/*
        PWA / manifest (reference for home-screen pinning — implement in layout):
          manifest: display standalone, theme_color #09090b, background_color #09090b
          apple-mobile-web-app-capable, apple-touch-icon, viewportFit cover

        Nuclear iOS Protocol: solid bg-zinc-950, onTouchEnd on controls, z below MobileNav.
      */}
      <div
        className="fixed bottom-0 left-0 right-0 z-[9000] hidden border-t border-white/[0.08] bg-zinc-950 md:block"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        {/* Mobile: full-width progress strip above controls */}
        <div className="px-4 pt-2.5 md:hidden">
          <Scrubber value={progress} onChange={setProgress} />
          <div className="mt-1 flex justify-between">
            <span className="font-mono text-[9px] text-zinc-600">{elapsed}</span>
            <span className="font-mono text-[9px] text-zinc-600">{total}</span>
          </div>
        </div>

        {/* Control row */}
        <div className="flex items-center gap-3 px-4 py-2.5">

          {/* Left: Album art + track info */}
          <div className="flex min-w-0 flex-1 items-center gap-3 md:w-[30%] md:flex-none">
            {/* ytm-art-entrance: translate3d + scale3d entrance — GPU compositor only */}
            <div className="ytm-art-entrance h-10 w-10 flex-shrink-0 rounded-lg bg-zinc-800" />
            <div className="min-w-0">
              <p className="truncate text-xs font-semibold text-zinc-100">{MOCK_TRACK.title}</p>
              <p className="truncate text-[10px] text-zinc-500">{MOCK_TRACK.artist}</p>
            </div>
          </div>

          {/* Center: Desktop controls + scrubber */}
          <div className="hidden flex-1 flex-col items-center gap-1.5 md:flex">
            <div className="flex items-center gap-5">
              <button
                type="button"
                aria-label="Previous"
                onClick={() => setProgress(0)}
                onTouchEnd={(e) => { e.preventDefault(); setProgress(0); }}
                className="flex cursor-pointer touch-manipulation items-center justify-center text-zinc-400 transition-colors hover:text-zinc-100 active:scale-95"
              >
                <SkipBack size={16} className="pointer-events-none" aria-hidden />
              </button>

              <button
                type="button"
                aria-label={playing ? "Pause" : "Play"}
                onClick={togglePlay}
                onTouchEnd={(e) => { e.preventDefault(); togglePlay(); }}
                className="flex h-9 w-9 cursor-pointer touch-manipulation items-center justify-center rounded-full bg-white text-zinc-950 transition-transform active:scale-95"
              >
                {playing
                  ? <Pause size={16} className="pointer-events-none" fill="currentColor" aria-hidden />
                  : <Play  size={16} className="pointer-events-none" fill="currentColor"
                           style={{ transform: "translate3d(1px,0,0)" }} aria-hidden />}
              </button>

              <button
                type="button"
                aria-label="Next"
                onClick={() => setProgress(0)}
                onTouchEnd={(e) => { e.preventDefault(); setProgress(0); }}
                className="flex cursor-pointer touch-manipulation items-center justify-center text-zinc-400 transition-colors hover:text-zinc-100 active:scale-95"
              >
                <SkipForward size={16} className="pointer-events-none" aria-hidden />
              </button>
            </div>

            {/* Desktop scrubber with timestamps */}
            <div className="flex w-full max-w-xs items-center gap-2">
              <span className="flex-shrink-0 font-mono text-[9px] text-zinc-600">{elapsed}</span>
              <Scrubber value={progress} onChange={setProgress} className="flex-1" />
              <span className="flex-shrink-0 font-mono text-[9px] text-zinc-600">{total}</span>
            </div>
          </div>

          {/* Right: Mobile Play/Pause · Desktop volume + Maloja badge */}
          <div className="flex flex-shrink-0 items-center justify-end gap-3 md:w-[30%]">

            {/* Mobile: single play/pause button */}
            <button
              type="button"
              aria-label={playing ? "Pause" : "Play"}
              onClick={togglePlay}
              onTouchEnd={(e) => { e.preventDefault(); togglePlay(); }}
              className="flex h-9 w-9 cursor-pointer touch-manipulation items-center justify-center rounded-full bg-white text-zinc-950 transition-transform active:scale-95 md:hidden"
            >
              {playing
                ? <Pause size={15} className="pointer-events-none" fill="currentColor" aria-hidden />
                : <Play  size={15} className="pointer-events-none" fill="currentColor"
                         style={{ transform: "translate3d(1px,0,0)" }} aria-hidden />}
            </button>

            {/* Desktop: volume slider + Maloja badge */}
            <div className="hidden items-center gap-3 md:flex">
              <Volume2 size={13} className="flex-shrink-0 text-zinc-500" />
              {/* Volume — same scaleX scrubber pattern; no <input type="range"> */}
              <Scrubber value={volume} onChange={setVolume} className="w-20" />
              {/* scrubber-pulse: opacity breathe on GPU compositor */}
              <span className="scrubber-pulse flex flex-shrink-0 items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Maloja
              </span>
            </div>
          </div>
        </div>
      </div>

      <MobileDock
        playing={playing}
        onTogglePlay={togglePlay}
        activeView={activeView}
        onViewChange={setActiveView}
      />
    </div>
  );
}
