// Server-only module. Never import from a "use client" component.
// Node.js `fs` is only available server-side — any accidental client-side
// import will fail loudly at build time, which is intentional.

import fs   from "fs";
import path from "path";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface SectionProgress {
  /** H3 section heading text (### stripped) */
  heading: string;
  done:    number;
  total:   number;
  pct:     number;
}

export interface ReadmeProgress {
  /** Scoped totals across all active-sprint H3 sections */
  done:     number;
  total:    number;
  pct:      number;
  /** Per-H3 breakdown — useful for the /projects detail view */
  sections: SectionProgress[];
}

// ─── Scope configuration ──────────────────────────────────────────────────────
//
// "Active sprint" for Spirit OS UI = Phases 0–2 + Navigation.
// Phase 3 (App Ecosystem) and Phase 4 (Security Bunker) are roadmap items;
// including them would add ~53 unchecked boxes and understate real progress.
//
const ACTIVE_SPRINT_PREFIXES = ["Phase 0", "Phase 1", "Phase 2", "Navigation"];

// Map: repo slug → list of H3-heading substrings that are in scope.
// Only repos listed here receive dynamic progress; others fall back to the
// hardcoded value in lib/mockProjects.ts.
const REPO_SCOPE: Record<string, string[]> = {
  "spirit-os-dashboard": ACTIVE_SPRINT_PREFIXES,
};

// ─── Internal parser ──────────────────────────────────────────────────────────

function readLines(): string[] {
  const raw = fs.readFileSync(
    path.join(process.cwd(), "README.md"),
    "utf-8"
  );
  return raw.split("\n");
}

function extractProgress(lines: string[], scopePrefixes: string[]): ReadmeProgress {
  let inScoped       = false;
  const sections: SectionProgress[] = [];
  let cur: SectionProgress | null   = null;

  for (const line of lines) {
    // ── H3 headings change the active section ──────────────────────────────
    if (line.startsWith("### ")) {
      if (cur) sections.push(cur);
      const heading = line.replace(/^###\s+/, "").trim();
      inScoped = scopePrefixes.some((p) => heading.includes(p));
      cur = inScoped ? { heading, done: 0, total: 0, pct: 0 } : null;
      continue;
    }

    // ── H2 headings exit all H3 context ────────────────────────────────────
    if (line.startsWith("## ")) {
      if (cur) sections.push(cur);
      inScoped = false;
      cur = null;
      continue;
    }

    // ── H4 headings (####) are sub-sections inside a Phase; they do NOT
    //    change inScoped — checkboxes beneath them still count. ─────────────
    if (!inScoped || !cur) continue;

    // GFM task-list item: "- [x]" (checked) or "- [ ]" (unchecked).
    // The /i flag handles "- [X]" edge cases.
    if (/^- \[x\]/i.test(line)) {
      cur.done++;
      cur.total++;
    } else if (/^- \[ \]/.test(line)) {
      cur.total++;
    }
  }

  // Flush the final open section
  if (cur) sections.push(cur);

  // Compute per-section percentage
  for (const s of sections) {
    s.pct = s.total > 0 ? Math.round((s.done / s.total) * 100) : 0;
  }

  const done  = sections.reduce((a, s) => a + s.done,  0);
  const total = sections.reduce((a, s) => a + s.total, 0);

  return {
    done,
    total,
    pct:      total > 0 ? Math.round((done / total) * 100) : 0,
    sections,
  };
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Returns the scoped completion percentage (0–100) for a given repo slug,
 * or null if that repo has no README tracking configured.
 *
 * Designed for use in async Server Components only.
 */
export function getReadmeCompletion(repo: string): number | null {
  const scope = REPO_SCOPE[repo];
  if (!scope) return null;
  return extractProgress(readLines(), scope).pct;
}

/**
 * Returns the full scoped progress breakdown (done / total / pct per H3
 * section) for a given repo slug, or null if unconfigured.
 *
 * Useful for the /projects detail view's progress card.
 */
export function getSectionBreakdown(repo: string): ReadmeProgress | null {
  const scope = REPO_SCOPE[repo];
  if (!scope) return null;
  return extractProgress(readLines(), scope);
}
