import "server-only";

import { resolveVerifiedHttpUrl } from "@/lib/verified-http-url";

// Re-export for tests / importers that expect URL helpers from this module.
export { normalizeToHttpUrl, resolveVerifiedHttpUrl, isVerifiedHttpUrl } from "@/lib/verified-http-url";

// ── OpenAI Responses API - web_search tool (isolated from Hermes chat, Prompt 10B) ─
// > If OpenAI changes payload shapes, adjust normalize only - do not leak keys to client.

export type WebSearchSource = {
  title?: string;
  url?: string;
  snippet?: string;
  sourceType?: string;
};

export type OpenAiWebSearchOk = {
  ok: true;
  provider: "openai";
  query: string;
  searched: true;
  sources: WebSearchSource[];
  answerPreview?: string;
  rawCitations?: unknown;
};

export type OpenAiWebSearchFail = {
  ok: false;
  provider: "openai";
  searched: false;
  error: string;
  detail?: string;
};

export type OpenAiWebSearchResult = OpenAiWebSearchOk | OpenAiWebSearchFail;

const DEFAULT_TIMEOUT_MS = 45_000;

function webEnabled(): boolean {
  const v = process.env.WEB_SEARCH_ENABLED?.trim().toLowerCase();
  return v === "1" || v === "true" || v === "yes";
}

/** First non-empty string among common OpenAI / crawler URL field names. */
function pickRawUrlFromRecord(r: Record<string, unknown>): string | undefined {
  const keys = [
    "url",
    "link",
    "href",
    "uri",
    "start_url",
    "end_url",
    "source_url",
    "webpage_url",
    "open_url",
    "page_url",
  ] as const;
  for (const k of keys) {
    const v = r[k];
    if (typeof v === "string" && v.trim()) return v.trim();
  }
  return undefined;
}

function walkForSources(obj: unknown, out: WebSearchSource[], cap: number): void {
  if (out.length >= cap || obj == null) return;
  if (typeof obj !== "object") return;
  if (Array.isArray(obj)) {
    for (const x of obj) walkForSources(x, out, cap);
    return;
  }
  const r = obj as Record<string, unknown>;
  const rawUrl = pickRawUrlFromRecord(r);
  const url = resolveVerifiedHttpUrl(rawUrl);
  const title = typeof r.title === "string" ? r.title : typeof r.name === "string" ? r.name : undefined;
  const snippet =
    typeof r.snippet === "string"
      ? r.snippet
      : typeof r.description === "string"
        ? r.description
        : typeof r.text === "string"
          ? r.text
          : undefined;
  if (url?.trim() || title?.trim()) {
    out.push({
      url: url?.trim(),
      title: title?.trim(),
      snippet: snippet?.trim(),
      sourceType: typeof r.type === "string" ? r.type : undefined,
    });
  }
  for (const k of Object.keys(r)) walkForSources(r[k], out, cap);
}

/** Exported for unit tests - parses Responses `output[]` into deduped sources. */
export function extractWebSearchSourcesFromOpenAiResponseJson(
  json: Record<string, unknown>,
  maxResults: number,
): {
  sources: WebSearchSource[];
  answerPreview?: string;
  rawCitations?: unknown;
} {
  const sources: WebSearchSource[] = [];
  const output = json.output;
  let answerPreview: string | undefined;
  const citations: unknown[] = [];

  if (Array.isArray(output)) {
    for (const item of output) {
      if (!item || typeof item !== "object") continue;
      const it = item as Record<string, unknown>;
      if (it.type === "web_search_call") {
        walkForSources(it, sources, maxResults);
      }
      if (it.type === "message") {
        const content = it.content;
        if (Array.isArray(content)) {
          for (const c of content) {
            if (!c || typeof c !== "object") continue;
            const cc = c as Record<string, unknown>;
            if (cc.type === "output_text" && typeof cc.text === "string") {
              answerPreview = (answerPreview ?? "") + cc.text;
            }
            if (Array.isArray(cc.annotations)) {
              citations.push(...cc.annotations);
              for (const a of cc.annotations) {
                if (!a || typeof a !== "object") continue;
                const ann = a as Record<string, unknown>;
                if (ann.type === "url_citation" || ann.type === "citation") {
                  const rawU = pickRawUrlFromRecord(ann);
                  const u = resolveVerifiedHttpUrl(rawU);
                  const t = typeof ann.title === "string" ? ann.title : undefined;
                  if (u || t) sources.push({ url: u, title: t, sourceType: String(ann.type) });
                }
              }
            }
          }
        }
      }
    }
  }

  const dedup: WebSearchSource[] = [];
  const seen = new Set<string>();
  for (const s of sources) {
    const key = `${s.url ?? ""}|${s.title ?? ""}`;
    if (seen.has(key)) continue;
    seen.add(key);
    dedup.push(s);
    if (dedup.length >= maxResults) break;
  }

  if (answerPreview && answerPreview.length > 1200) {
    answerPreview = `${answerPreview.slice(0, 1199)}…`;
  }

  return {
    sources: dedup,
    answerPreview,
    rawCitations: citations.length ? citations : undefined,
  };
}

/**
 * OpenAI sometimes omits structured URLs but embeds https links in grounded preview text.
 * Same resolveVerifiedHttpUrl gate as walk/citations - keeps digest + headers aligned.
 */
export function appendVerifiedUrlsFromAnswerPreview(
  sources: WebSearchSource[],
  answerPreview: string | undefined,
  maxResults: number,
): WebSearchSource[] {
  if (sources.some((s) => Boolean(resolveVerifiedHttpUrl(s.url)))) return sources;
  const preview = answerPreview?.trim();
  if (!preview) return sources;

  const extra: WebSearchSource[] = [];
  const seen = new Set<string>();
  for (const s of sources) {
    const u = resolveVerifiedHttpUrl(s.url);
    if (u) seen.add(u);
  }

  const re = /https?:\/\/[^\s)\]>"']+/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(preview)) !== null && extra.length < maxResults) {
    const raw = m[0].replace(/[.,;:)\]]+$/g, "");
    const url = resolveVerifiedHttpUrl(raw);
    if (!url || seen.has(url)) continue;
    seen.add(url);
    extra.push({ url, title: undefined, sourceType: "answer_preview" });
  }
  if (extra.length === 0) return sources;

  const merged = [...sources, ...extra];
  const dedup: WebSearchSource[] = [];
  const used = new Set<string>();
  for (const s of merged) {
    const u = resolveVerifiedHttpUrl(s.url);
    if (!u) continue;
    if (used.has(u)) continue;
    used.add(u);
    dedup.push({ ...s, url: u });
    if (dedup.length >= maxResults) break;
  }
  return dedup;
}

export async function runOpenAiWebSearch(opts: {
  query: string;
  maxResults?: number;
  timeoutMs?: number;
}): Promise<OpenAiWebSearchResult> {
  const query = opts.query.trim();
  if (!query) {
    return { ok: false, provider: "openai", searched: false, error: "empty_query", detail: "Query is empty" };
  }

  if (!webEnabled()) {
    return {
      ok: false,
      provider: "openai",
      searched: false,
      error: "disabled",
      detail: "WEB_SEARCH_ENABLED is not true - web search is off.",
    };
  }

  const key = process.env.OPENAI_API_KEY?.trim();
  if (!key) {
    return {
      ok: false,
      provider: "openai",
      searched: false,
      error: "missing_key",
      detail: "OPENAI_API_KEY is not configured",
    };
  }

  const model =
    process.env.WEB_SEARCH_MODEL?.trim() ||
    process.env.OPENAI_WEB_SEARCH_MODEL?.trim() ||
    "gpt-4o";

  const maxResultsRaw = process.env.WEB_SEARCH_MAX_RESULTS?.trim();
  const maxResults =
    typeof opts.maxResults === "number" && opts.maxResults > 0
      ? Math.min(opts.maxResults, 12)
      : Math.min(Math.max(Number.parseInt(maxResultsRaw ?? "8", 10) || 8, 1), 12);

  const toolType = process.env.WEB_SEARCH_TOOL_TYPE?.trim() || "web_search";

  const controller = new AbortController();
  const to = setTimeout(() => controller.abort(), opts.timeoutMs ?? DEFAULT_TIMEOUT_MS);
  try {
    const res = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model,
        input: query,
        tools: [{ type: toolType }],
        tool_choice: "auto",
        // action.sources + results: OpenAI intermittently omits one shape - ask for both.
        include: ["web_search_call.action.sources", "web_search_call.results"],
      }),
      signal: controller.signal,
    });

    const rawText = await res.text();
    let json: unknown;
    try {
      json = JSON.parse(rawText) as unknown;
    } catch {
      return {
        ok: false,
        provider: "openai",
        searched: false,
        error: "invalid_json",
        detail: rawText.slice(0, 200),
      };
    }

    if (!res.ok) {
      const errObj = json && typeof json === "object" ? (json as Record<string, unknown>) : {};
      const msg =
        typeof errObj.error === "object" && errObj.error && "message" in (errObj.error as object)
          ? String((errObj.error as { message?: string }).message ?? res.statusText)
          : res.statusText;
      return {
        ok: false,
        provider: "openai",
        searched: false,
        error: `openai_${res.status}`,
        detail: msg.slice(0, 400),
      };
    }

    if (!json || typeof json !== "object") {
      return { ok: false, provider: "openai", searched: false, error: "bad_response", detail: "Empty JSON" };
    }

    const extracted = extractWebSearchSourcesFromOpenAiResponseJson(json as Record<string, unknown>, maxResults);
    const sources = appendVerifiedUrlsFromAnswerPreview(
      extracted.sources,
      extracted.answerPreview,
      maxResults,
    );
    return {
      ok: true,
      provider: "openai",
      query,
      searched: true,
      sources,
      answerPreview: extracted.answerPreview,
      rawCitations: extracted.rawCitations,
    };
  } catch (e) {
    const aborted = e instanceof Error && e.name === "AbortError";
    return {
      ok: false,
      provider: "openai",
      searched: false,
      error: aborted ? "timeout" : "fetch_failed",
      detail: e instanceof Error ? e.message : String(e),
    };
  } finally {
    clearTimeout(to);
  }
}
