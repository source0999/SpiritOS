"use client";

import { useState } from "react";
import type { ReactElement } from "react";
import {
  PanelLeft, X, Plus, TerminalSquare, GitBranch,
  Code, Circle, BookOpen, Sparkles, FolderOpen,
} from "lucide-react";
import { PROJECTS } from "@/lib/mockProjects";
import type { ProjectStatus } from "@/lib/mockProjects";

// ─── Utility ──────────────────────────────────────────────────────────────────

function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

// ─── Shared helpers ───────────────────────────────────────────────────────────

function statusDot(s: ProjectStatus) {
  if (s === "active") return "bg-emerald-400";
  if (s === "paused") return "bg-amber-400";
  return "bg-zinc-600";
}

function barColor(pct: number) {
  if (pct >= 70) return "bg-emerald-500/70";
  if (pct >= 40) return "bg-violet-500/70";
  return "bg-amber-500/60";
}

function barTextColor(pct: number) {
  if (pct >= 70) return "text-emerald-400";
  if (pct >= 40) return "text-violet-400";
  return "text-amber-400";
}

// Full class strings — Tailwind purge requires static strings per variant.
function langColor(lang: string): string {
  switch (lang.toLowerCase()) {
    case "typescript": return "border-sky-500/30 bg-sky-500/10 text-sky-400";
    case "python":     return "border-amber-500/30 bg-amber-500/10 text-amber-400";
    case "shell":
    case "bash":       return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
    case "react":      return "border-cyan-500/30 bg-cyan-500/10 text-cyan-400";
    default:           return "border-white/[0.08] bg-white/[0.04] text-zinc-500";
  }
}

// ─── README Renderer ──────────────────────────────────────────────────────────
//
// Lightweight line-by-line parser for the mock README strings.
// Handles: # h1, ## h2, - bullets, `inline code`, empty lines, plain text.
//

function renderInlineCode(text: string): (string | ReactElement)[] {
  const parts = text.split(/(`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={i}
          className="rounded bg-white/[0.08] px-1.5 py-px font-mono text-[11px] text-violet-300"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

function ReadmeRenderer({ content }: { content: string }) {
  const lines = content.split("\n");
  return (
    <div>
      {lines.map((line, i) => {
        if (line.startsWith("# ")) {
          return (
            <h1
              key={i}
              className="mb-3 mt-0 text-lg font-bold tracking-tight text-zinc-100"
            >
              {line.slice(2)}
            </h1>
          );
        }
        if (line.startsWith("## ")) {
          return (
            <h2
              key={i}
              className="mb-2 mt-5 text-[11px] font-semibold uppercase tracking-widest text-zinc-500"
            >
              {line.slice(3)}
            </h2>
          );
        }
        if (line.startsWith("- ")) {
          return (
            <div key={i} className="flex items-start gap-2 py-0.5">
              <span className="mt-[7px] h-1 w-1 flex-shrink-0 rounded-full bg-zinc-700" />
              <span className="text-sm leading-relaxed text-zinc-400">
                {renderInlineCode(line.slice(2))}
              </span>
            </div>
          );
        }
        if (line.trim() === "") {
          return <div key={i} className="h-3" />;
        }
        return (
          <p key={i} className="text-sm leading-relaxed text-zinc-400">
            {renderInlineCode(line)}
          </p>
        );
      })}
    </div>
  );
}

// ─── ProjectSidebar ───────────────────────────────────────────────────────────
//
// Used twice: inline desktop aside + inside the mobile overlay.
// `onClose` is only passed in the mobile context.
//
function ProjectSidebar({
  activeRepo,
  onSelect,
  onClose,
}: {
  activeRepo: string;
  onSelect:   (repo: string) => void;
  onClose?:   () => void;
}) {
  const [filter, setFilter] = useState<"all" | ProjectStatus>("all");

  const visible = filter === "all"
    ? PROJECTS
    : PROJECTS.filter((p) => p.status === filter);

  function pick(repo: string) {
    onSelect(repo);
    onClose?.();
  }

  return (
    <div className="flex h-full flex-col">

      {/* ── Header ── */}
      <div className="flex flex-shrink-0 items-center justify-between px-4 pb-3 pt-4">
        <div className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded-md border border-violet-500/30 bg-violet-500/15">
            <TerminalSquare size={10} className="text-violet-400" aria-hidden />
          </div>
          <span className="text-[11px] font-semibold tracking-tight text-zinc-400">
            Projects & IDE
          </span>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            onTouchEnd={(e) => { e.preventDefault(); onClose(); }}
            aria-label="Close sidebar"
            className="flex h-7 w-7 cursor-pointer touch-manipulation items-center justify-center rounded-lg text-zinc-600 transition-colors hover:text-zinc-300"
          >
            <X size={14} className="pointer-events-none" aria-hidden />
          </button>
        )}
      </div>

      {/* ── New Project CTA ── */}
      <div className="flex-shrink-0 px-3 pb-3">
        <button
          type="button"
          className="group flex w-full cursor-pointer touch-manipulation items-center gap-2.5 rounded-xl border border-white/[0.07] bg-white/[0.04] px-3 py-2.5 text-left transition-all hover:border-violet-500/25 hover:bg-violet-500/[0.07]"
        >
          <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg border border-violet-500/30 bg-violet-500/15 transition-colors group-hover:border-violet-500/50 group-hover:bg-violet-500/25">
            <Plus size={12} className="pointer-events-none text-violet-400" aria-hidden />
          </div>
          <span className="text-[12px] font-semibold text-zinc-400 transition-colors group-hover:text-zinc-100">
            New Project
          </span>
        </button>
      </div>

      {/* ── Filter tabs ── */}
      <div className="flex-shrink-0 flex flex-wrap gap-1 border-t border-white/[0.05] px-3 py-2.5">
        {(["all", "active", "paused", "idle"] as const).map((f) => (
          <button
            key={f}
            type="button"
            onClick={() => setFilter(f)}
            onTouchEnd={(e) => { e.preventDefault(); setFilter(f); }}
            className={cn(
              "rounded-lg border px-2.5 py-1 font-mono text-[10px] capitalize transition-colors",
              filter === f
                ? "border-violet-500/40 bg-violet-500/15 text-violet-300"
                : "border-white/[0.06] text-zinc-600 hover:text-zinc-400",
            )}
          >
            {f}
          </button>
        ))}
        <span className="ml-auto self-center font-mono text-[10px] text-zinc-700">
          {visible.length} of {PROJECTS.length}
        </span>
      </div>

      {/* ── Project list ── */}
      <div className="flex-1 overflow-y-auto px-2 pb-2 pt-1">
        {visible.map((proj) => {
          const isActive = proj.repo === activeRepo;
          return (
            <button
              key={proj.repo}
              type="button"
              onClick={() => pick(proj.repo)}
              onTouchEnd={(e) => { e.preventDefault(); pick(proj.repo); }}
              className={cn(
                "mb-1 w-full cursor-pointer touch-manipulation rounded-xl px-3 py-3 text-left transition-colors",
                isActive
                  ? "border border-violet-500/20 bg-violet-500/[0.06]"
                  : "border border-transparent hover:bg-white/[0.04] active:bg-white/[0.06]",
              )}
            >
              {/* Row 1: status dot · title · last commit */}
              <div className="mb-2 flex items-center gap-2">
                <span className={cn("h-1.5 w-1.5 flex-shrink-0 rounded-full", statusDot(proj.status))} />
                <span className={cn(
                  "flex-1 truncate text-[13px] font-semibold leading-none",
                  isActive ? "text-zinc-100" : "text-zinc-300",
                )}>
                  {proj.name}
                </span>
                <span className="flex-shrink-0 font-mono text-[9px] text-zinc-700">
                  {proj.lastCommit}
                </span>
              </div>

              {/* Row 2: language badge · branch */}
              <div className="mb-2.5 flex items-center gap-2 pl-3.5">
                <span className={cn(
                  "rounded-md border px-1.5 py-px font-mono text-[9px] font-bold uppercase tracking-wide",
                  langColor(proj.lang),
                )}>
                  {proj.lang}
                </span>
                <span className="flex items-center gap-0.5 font-mono text-[10px] text-zinc-700">
                  <GitBranch size={9} className="flex-shrink-0" aria-hidden />
                  <span className="truncate max-w-[90px]">{proj.branch}</span>
                </span>
              </div>

              {/* Row 3: progress bar with % and TODO count */}
              <div className="pl-3.5">
                <div className="mb-1 flex items-center justify-between">
                  <span className={cn("font-mono text-[10px] font-semibold tabular-nums", barTextColor(proj.completion))}>
                    {proj.completion}%
                  </span>
                  <span className={cn(
                    "rounded-full border px-1.5 py-px font-mono text-[9px] font-semibold",
                    proj.todos.length > 5
                      ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                      : "border-white/[0.07] bg-white/[0.03] text-zinc-600",
                  )}>
                    {proj.todos.length} TODO{proj.todos.length !== 1 ? "s" : ""}
                  </span>
                </div>
                <div className="relative h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                  <div
                    className={cn("absolute inset-y-0 left-0 rounded-full", barColor(proj.completion))}
                    style={{ width: `${proj.completion}%` }}
                  />
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* ── Open Workspace Directory ─────────────────────────────────────────
        Lightweight footer CTA — primary action ("Launch in Cursor") lives in
        the right-panel header, so this is intentionally secondary in weight.
        Solid bg-zinc-950 satisfies iOS WebKit solid-background requirement.
      ─────────────────────────────────────────────────────────────────────── */}
      <div className="flex-shrink-0 border-t border-white/[0.05] px-3 py-3">
        <button
          type="button"
          className="group flex w-full cursor-pointer touch-manipulation items-center gap-2.5 rounded-xl border border-white/[0.06] bg-zinc-950 px-3 py-2.5 text-left transition-colors hover:border-white/[0.10] hover:bg-white/[0.04] active:scale-[0.98]"
        >
          <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.04] transition-colors group-hover:border-white/[0.14]">
            <FolderOpen size={13} className="pointer-events-none text-zinc-500 group-hover:text-zinc-300" aria-hidden />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[12px] font-semibold text-zinc-500 transition-colors group-hover:text-zinc-300">
              Open Workspace Directory
            </p>
            <p className="mt-0.5 truncate font-mono text-[10px] text-zinc-700">
              {PROJECTS.find((p) => p.repo === activeRepo)?.dir ?? "~"}
            </p>
          </div>
        </button>

        <p className="mt-2.5 text-center font-mono text-[9px] text-zinc-700">
          {PROJECTS.filter((p) => p.status === "active").length} active ·{" "}
          {PROJECTS.reduce((s, p) => s + p.todos.length, 0)} open TODOs
        </p>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ProjectsPage() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [activeRepo, setActiveRepo] = useState(PROJECTS[0].repo);

  const proj = PROJECTS.find((p) => p.repo === activeRepo) ?? PROJECTS[0];

  return (
    /*
      Outer shell: dual-panel, iOS-safe.
      h-[calc(100dvh-60px)] → subtracts the 60px fixed mobile nav header.
      md:h-[100dvh]         → desktop: full viewport, no top offset.
      relative              → stacking context for the mobile overlay.
      No backdrop-blur. No overflow-hidden on ancestors.
    */
    <div className="relative flex h-[calc(100dvh-60px)] flex-row bg-zinc-950 md:h-[100dvh]">

      {/* ── Desktop Sidebar (w-80) ───────────────────────────────────────── */}
      <aside
        className="hidden md:flex md:w-80 md:flex-shrink-0 md:flex-col border-r border-white/[0.05]"
        style={{ background: "#09090b" }}
      >
        <ProjectSidebar activeRepo={activeRepo} onSelect={setActiveRepo} />
      </aside>

      {/* ── Details Panel ───────────────────────────────────────────────── */}
      <div className="flex min-w-0 flex-1 flex-col">

        {/* ── Details Header ─────────────────────────────────────────────────
          relative z-10 + bg-zinc-950 — prevents terminal-style text bleed
          during iOS momentum scroll on this panel.
        ─────────────────────────────────────────────────────────────────── */}
        <header className="relative z-10 flex flex-shrink-0 items-center gap-3 border-b border-white/[0.07] bg-zinc-950 px-5 py-4">

          {/* Mobile sidebar toggle */}
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            onTouchEnd={(e) => { e.preventDefault(); setMobileOpen(true); }}
            aria-label="Open project list"
            className="flex h-9 w-9 cursor-pointer touch-manipulation items-center justify-center rounded-xl border border-white/[0.07] bg-white/5 text-zinc-500 transition-colors hover:text-zinc-300 md:hidden"
          >
            <PanelLeft size={15} className="pointer-events-none" aria-hidden />
          </button>

          {/* Title + meta */}
          <div className="min-w-0 flex-1">
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <span className={cn(
                "rounded-md border px-1.5 py-px font-mono text-[9px] font-bold uppercase tracking-wide",
                langColor(proj.lang),
              )}>
                {proj.lang}
              </span>
              <span className="flex items-center gap-1 font-mono text-[10px] text-zinc-600">
                <GitBranch size={9} aria-hidden />
                {proj.branch}
              </span>
              <span className="font-mono text-[10px] text-zinc-700">{proj.lastCommit}</span>
            </div>
            <h1 className="truncate text-lg font-bold tracking-tight text-zinc-100 leading-none">
              {proj.name}
            </h1>
          </div>

          {/* Launch in Cursor IDE CTA */}
          <button
            type="button"
            className="flex flex-shrink-0 cursor-pointer touch-manipulation items-center gap-2 rounded-xl border border-violet-500/30 bg-violet-500/10 px-3 py-2 text-violet-300 transition-all hover:border-violet-500/50 hover:bg-violet-500/20 active:scale-[0.97]"
          >
            <Code size={14} className="pointer-events-none" aria-hidden />
            <span className="hidden text-xs font-semibold sm:block">Launch in Cursor</span>
          </button>
        </header>

        {/* ── Scrollable Details Content ──────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto px-4 py-5">
          <div className="mx-auto w-full max-w-2xl space-y-5">

          {/* ── Spirit's Assessment ──────────────────────────────────────────
            High-contrast violet-bordered card for the AI-generated blurb.
            Font-italic + font-mono gives the "Spirit is speaking" register.
          ─────────────────────────────────────────────────────────────────── */}
          <section
            className="rounded-2xl border border-violet-500/30 bg-zinc-900 p-5"
            aria-label="Spirit's Assessment"
          >
            <div className="mb-3 flex items-center gap-2">
              <div className="flex h-5 w-5 items-center justify-center rounded-md border border-violet-500/30 bg-violet-500/15">
                <Sparkles size={10} className="pointer-events-none text-violet-400" aria-hidden />
              </div>
              <span className="font-mono text-[10px] uppercase tracking-widest text-violet-400/70">
                Spirit's Assessment
              </span>
            </div>
            <p className="font-mono text-sm italic leading-relaxed text-zinc-300">
              "{proj.spiritSummary}"
            </p>
          </section>

          {/* ── Active TODOs ─────────────────────────────────────────────────
            Checklist-style list using Circle icons as unchecked states.
            Amber accent when there are many open tasks matches the sidebar.
          ─────────────────────────────────────────────────────────────────── */}
          <section aria-label="Active TODOs">
            <div className="mb-3 flex items-center gap-2">
              <span className="font-mono text-[11px] uppercase tracking-widest text-zinc-600">
                Active TODOs
              </span>
              <span className={cn(
                "rounded-full border px-2 py-px font-mono text-[9px] font-semibold",
                proj.todos.length > 5
                  ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                  : "border-white/[0.08] bg-white/[0.03] text-zinc-600",
              )}>
                {proj.todos.length}
              </span>
            </div>
            <div className="space-y-2">
              {proj.todos.map((todo, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3 transition-colors hover:border-white/[0.10] hover:bg-white/[0.04]"
                >
                  <Circle
                    size={14}
                    className="mt-0.5 flex-shrink-0 text-zinc-700"
                    aria-hidden
                  />
                  <span className="text-sm leading-relaxed text-zinc-300">{todo}</span>
                </div>
              ))}
            </div>
          </section>

          {/* ── README.md ────────────────────────────────────────────────────
            Styled to resemble a GitHub README — monochrome background,
            typography hierarchy for h1/h2/list/inline-code.
          ─────────────────────────────────────────────────────────────────── */}
          <section aria-label="README">
            <div className="mb-3 flex items-center gap-2">
              <BookOpen size={12} className="text-zinc-600" aria-hidden />
              <span className="font-mono text-[11px] uppercase tracking-widest text-zinc-600">
                README.md
              </span>
            </div>
            <div className="rounded-2xl border border-white/[0.07] bg-zinc-900 px-6 py-5">
              <ReadmeRenderer content={proj.readme} />
            </div>
          </section>

          {/* Bottom breathing room for iOS safe area */}
          <div style={{ paddingBottom: "env(safe-area-inset-bottom)" }} />
          </div>{/* end max-w-2xl */}
        </div>
      </div>

      {/* ── Mobile Sidebar Overlay ───────────────────────────────────────── */}
      {/*
        Conditionally mounted — fresh DOM on every open (WebKit compositor
        cache bypass). No CSS opacity/visibility toggle. md:hidden safety valve.
      */}
      {mobileOpen && (
        <>
          <div
            className="absolute inset-0 z-[490] bg-black/80 md:hidden"
            onClick={() => setMobileOpen(false)}
            onTouchEnd={(e) => { e.preventDefault(); setMobileOpen(false); }}
          />
          <aside
            className="absolute left-0 top-0 z-[491] flex h-full w-[280px] flex-col border-r border-white/[0.05] md:hidden"
            style={{ background: "#09090b" }}
          >
            <ProjectSidebar
              activeRepo={activeRepo}
              onSelect={setActiveRepo}
              onClose={() => setMobileOpen(false)}
            />
          </aside>
        </>
      )}
    </div>
  );
}
