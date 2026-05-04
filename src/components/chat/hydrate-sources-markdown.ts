// ── hydrate-sources-markdown — fix cosplay Sources when header has real URLs ─────
// > Colocated with MessageMarkdown so the client bundle always resolves this module
//   (avoids “hydrateDegenerateSourcesMarkdown is not defined” from path/bundler drift).

import type { SpiritWebSourcesHeaderPayload } from "@/lib/spirit/spirit-web-sources";

function pickSourceLabel(title: string, url: string): string {
  const t = title?.trim().replace(/[\[\]]/g, "");
  if (t && t.length > 0) return t.length > 120 ? `${t.slice(0, 117)}…` : t;
  try {
    const u = new URL(url);
    const host = u.hostname.replace(/^www\./, "");
    const path = u.pathname === "/" ? "" : u.pathname;
    const s = (host + path).replace(/\/$/, "");
    return s.length > 120 ? `${s.slice(0, 117)}…` : s || host;
  } catch {
    return url.length > 100 ? `${url.slice(0, 97)}…` : url;
  }
}

/** True when Sources body looks like citation stubs (1 / 2 / [1](url)) with no real titles. */
export function isDegenerateSourcesBlock(section: string): boolean {
  const lines = section
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.length > 0);
  if (lines.length === 0) return true;
  let good = 0;
  let bad = 0;
  for (const line of lines) {
    if (/^\d+\.\s*\[[^\d\]]/.test(line) || /^\d+\.\s*https?:\/\//i.test(line) || /^[-*]\s*\[[^\d\]]/.test(line)) {
      good++;
    } else if (
      /^\d+\.\s*\d+\s*$/.test(line) ||
      /^\d+\.\s*\[\d{1,2}\]\(https?:/i.test(line) ||
      /^\d+\.\s*$/.test(line) ||
      /^[-*]\s*\d{1,2}\s*$/.test(line)
    ) {
      bad++;
    } else {
      return false;
    }
  }
  return good === 0 && bad > 0;
}

/**
 * If `## Sources` is degenerate and we have server header sources, replace that block
 * with markdown link bullets so MessageMarkdown shows real labels, not bare `1` / `2`.
 */
export function hydrateDegenerateSourcesMarkdown(
  md: string,
  payload: SpiritWebSourcesHeaderPayload | null | undefined,
): string {
  if (!payload?.sources?.length) return md;
  const m = md.match(/(?:^|\n)(##\s*sources\s*\n)/im);
  if (!m || m.index === undefined) return md;
  const headingLen = m[0].length;
  const introEnd = m.index + headingLen;
  const rest = md.slice(introEnd);
  const nextH2 = rest.search(/\n##\s+/i);
  const blockEnd = nextH2 === -1 ? md.length : introEnd + nextH2;
  const section = md.slice(introEnd, blockEnd).trimEnd();
  if (!isDegenerateSourcesBlock(section)) return md;

  const bullets = payload.sources
    .filter((s) => /^https?:\/\//i.test((s.url ?? "").trim()))
    .map((s) => {
      const url = (s.url ?? "").trim();
      const label = pickSourceLabel(s.title ?? "", url);
      return `- [${label}](${url})`;
    })
    .join("\n");
  if (!bullets) return md;

  const prefix = md.slice(m.index, introEnd);
  const tail = md.slice(blockEnd);
  return `${md.slice(0, m.index)}${prefix}${bullets}\n${tail.replace(/^\n+/, "")}`.replace(
    /\n{3,}/g,
    "\n\n",
  );
}
