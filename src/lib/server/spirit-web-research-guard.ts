import "server-only";

import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import { shouldPrefetchOpenAiWebForResearcher } from "@/lib/spirit/spirit-route-decision";
import { resolveVerifiedHttpUrl } from "@/lib/verified-http-url";

import type { OpenAiWebSearchResult } from "@/lib/server/openai-web-search";

export function isWebSearchGloballyEnabled(): boolean {
  const v = process.env.WEB_SEARCH_ENABLED?.trim().toLowerCase();
  return v === "1" || v === "true" || v === "yes";
}

/** Hermes researcher lane — thin wrapper for diagnostics/tests. */
export function shouldRunResearcherWebSearch(opts: {
  modelProfileId: ModelProfileId;
  lastUserText: string;
  webSearchOptOut?: boolean;
}): boolean {
  return shouldPrefetchOpenAiWebForResearcher({
    modelProfileId: opts.modelProfileId,
    lastUserText: opts.lastUserText,
    webSearchOptOut: opts.webSearchOptOut,
    webSearchGloballyEnabled: isWebSearchGloballyEnabled(),
  });
}

export function formatResearchSkippedBanner(reason: string): string {
  return `## Web research status
Search used: no (${reason})
No verified external sources were available for this response.
Do not claim you ran a web search. Do **not** add [1], [2], numbered citations, **## Sources**, or **## References**. Answer as **Unverified background** only; if live facts are uncertain, say so.`;
}

export function formatResearchContextForHermes(query: string, search: OpenAiWebSearchResult): string {
  if (!search.ok || !search.searched) {
    return `## Web research status
Search used: no (${"error" in search ? search.error : "unknown"}${"detail" in search && search.detail ? ` — ${search.detail}` : ""})
Answer from general knowledge only; label uncertain claims as unverified.`;
  }

  // Digest rows use resolveVerifiedHttpUrl so bare hosts match policy + Teacher budget counts.
  type DigestRow = { title: string; url: string; snippet?: string };
  const withUrls: DigestRow[] = [];
  for (const s of search.sources) {
    const url = resolveVerifiedHttpUrl(s.url);
    if (!url) continue;
    withUrls.push({
      title: s.title?.trim() || "Untitled",
      url,
      ...(s.snippet?.trim() ? { snippet: s.snippet.trim() } : {}),
    });
  }
  if (withUrls.length === 0) {
    return `## Web research status (OpenAI Responses + web_search)
Search used: yes (provider: OpenAI) but **no verified external URLs** were returned for this query.
Do not invent URLs or paper titles. If the user asked for 2024–2026 studies or other time-bounded claims, say you **cannot verify** without attached sources.
User query: ${query.slice(0, 800)}`;
  }

  const lines = withUrls.map((row, i) => {
    const sn = row.snippet ? ` — snippet: ${row.snippet.slice(0, 320)}` : "";
    return `${i + 1}. **${row.title}** | url: ${row.url}${sn}`;
  });

  const preview = search.answerPreview?.trim()
    ? `\nOpenAI grounded preview (trimmed; verify before citing):\n${search.answerPreview.trim().slice(0, 2000)}`
    : "";

  return `## Web research digest (OpenAI Responses + web_search)
Provider: OpenAI
Search used: yes
User query: ${query.slice(0, 800)}
Verified URL sources (${withUrls.length}):
${lines.join("\n")}
${preview}

Instructions: Only claim facts supported by the digest above. Use [n](url) inline only for URLs listed. Your final answer must include **## Sources** with those same URLs. If the user asked for recent studies and this digest is empty of usable links, say you cannot verify that request.`;
}

/** Compact JSON for `x-spirit-web-sources` — keep under typical proxy header limits. */
export function buildWebSearchSourcesHeader(search: OpenAiWebSearchResult): string | null {
  if (!search.ok || !search.searched) return null;
  const items: { title: string; url: string; snippet: string }[] = [];
  for (const s of search.sources) {
    const url = resolveVerifiedHttpUrl(s.url);
    if (!url) continue;
    items.push({
      title: (s.title ?? "").trim().slice(0, 180),
      url: url.slice(0, 900),
      snippet: (s.snippet ?? "").trim().slice(0, 240),
    });
    if (items.length >= 10) break;
  }
  let payload = {
    provider: "openai" as const,
    count: items.length,
    sources: items,
  };
  let json = JSON.stringify(payload);
  while (json.length > 3600 && payload.sources.length > 1) {
    payload = {
      ...payload,
      sources: payload.sources.slice(0, -1),
    };
    json = JSON.stringify(payload);
  }
  return json.length > 4000 ? null : json;
}
