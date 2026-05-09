// ── research-source-enforcement - no fake citations when search lied or failed ─────
// > Hermes will still try; this module is policy text + a dumb safety net stripper.

import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import { isVerifiedHttpUrl } from "@/lib/verified-http-url";

export type SpiritSearchStatus =
  | "used"
  | "skipped"
  | "disabled"
  | "failed"
  | "none"
  | string;

export type ResearchSourcePolicyInput = {
  searchStatus: SpiritSearchStatus;
  /** URLs returned from web search (verified http(s)). */
  sources: Array<{ url?: string }>;
  /** User asked for fresh / recent external proof */
  requestedFreshSources?: boolean;
  /** Teacher needs links in Study aids, not buried only under ## Sources. */
  modelProfileId?: ModelProfileId;
};

function countVerifiedHttpUrls(sources: Array<{ url?: string }>): number {
  let n = 0;
  for (const s of sources) {
    if (isVerifiedHttpUrl(s.url)) n += 1;
  }
  return n;
}

export function hasUsableResearchSources(sources: Array<{ url?: string }>): boolean {
  return countVerifiedHttpUrls(sources) > 0;
}

/**
 * Extra system text appended to web-research context so Hermes stops cosplaying PubMed.
 */
export function buildResearchSourcePolicy(input: ResearchSourcePolicyInput): string {
  const urlCount = countVerifiedHttpUrls(input.sources);
  const searchUsed =
    input.searchStatus === "used" && urlCount > 0 ? "yes" : "no";
  const fresh = Boolean(input.requestedFreshSources);

  if (searchUsed === "yes") {
    if (input.modelProfileId === "teacher") {
      return [
        "## Source enforcement (mandatory)",
        "- Search used: yes",
        "- Verified URLs are in the web digest above.",
        '- **Study aids** must include a markdown bullet list: one line per verified URL, each exactly `- [Short label](https://...)` using only URLs from the digest (no invented links).',
        "- Optional: you may repeat the same links under **## Sources** - but Study aids must not be only generic search phrases when URLs exist.",
        `- Verified URL count: ${urlCount}`,
      ].join("\n");
    }
    return [
      "## Source enforcement (mandatory)",
      "- Search used: yes",
      "- You may use numbered citations **only** as [n](url) where url is one listed above.",
      "- End with **## Sources** using those same clickable URLs.",
      `- Verified URL count: ${urlCount}`,
    ].join("\n");
  }

  const lines = [
    "## Source enforcement (mandatory)",
    "- Search used: no",
    "- No verified external URLs were attached for this response.",
    "- State clearly that the answer is **unverified** general background.",
    "- Do **not** include numbered citations like [1], [2], [3].",
    "- Do **not** include **## Sources**, **## References**, or bibliography entries.",
    "- Do **not** invent article titles, journals, DOIs, or URLs from memory.",
  ];
  if (fresh) {
    lines.push(
      "- The user asked for time-bounded external proof: say you **cannot verify** that without attached URLs.",
    );
  } else {
    lines.push('- If you continue from training knowledge, label it **"Unverified background"** - not "Findings".');
  }
  return lines.join("\n");
}

const SOURCES_HEADING = /^#{1,6}\s*sources\s*$/im;
const REFS_HEADING = /^#{1,6}\s*references\s*$/im;

/** Strip [1]..[99] markers (standalone or before punctuation). */
function stripNumberedCitationMarkers(text: string): string {
  return text.replace(/\[\s*\d{1,2}\s*\](?=\s|[.,;:!?)\]]|$)/g, "");
}

function stripMarkdownSectionAfterHeading(text: string, headingLine: RegExp): string {
  const m = headingLine.exec(text);
  if (!m || m.index === undefined) return text;
  const start = m.index;
  const tail = text.slice(start + m[0].length);
  const rel = tail.search(/^\n#{1,6}\s+\S/m);
  const end = rel === -1 ? text.length : start + m[0].length + rel;
  return (text.slice(0, start) + text.slice(end)).replace(/\n{3,}/g, "\n\n").trim();
}

/**
 * Last-resort sanitizer when the model ignored policy - only safe when caller knows URLs were absent.
 */
export function stripFakeCitationsWhenNoSources(text: string): string {
  if (!text.trim()) return text;
  let t = text;
  t = stripMarkdownSectionAfterHeading(t, SOURCES_HEADING);
  t = stripMarkdownSectionAfterHeading(t, REFS_HEADING);
  t = stripNumberedCitationMarkers(t);
  return t.replace(/\n{3,}/g, "\n\n").trim();
}

export function userRequestedFreshExternalSources(text: string): boolean {
  const t = text.toLowerCase();
  return (
    /\b20(2[4-9]|3[0-9])\b/.test(t) &&
    /\b(source|study|studies|paper|peer|journal|doi|verify|evidence|literature)\b/i.test(t)
  );
}
