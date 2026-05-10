import "server-only";

import { runOpenAiWebSearch } from "@/lib/server/openai-web-search";
import { normalizeWebSearchSources } from "@/lib/server/web-search/source-normalizer";
import type { WebSearchAdapter, WebSearchResult } from "@/lib/server/web-search/types";

export async function runOpenAiFallbackWebSearch(opts: {
  query: string;
  maxResults: number;
  timeoutMs?: number;
}): Promise<WebSearchResult> {
  const startedAt = Date.now();
  const result = await runOpenAiWebSearch({
    query: opts.query,
    maxResults: opts.maxResults,
    timeoutMs: opts.timeoutMs,
  });

  if (!result.ok) {
    return {
      ok: false,
      searched: result.searched,
      provider: "openai",
      error: result.error,
      ...(result.detail ? { detail: result.detail } : {}),
      elapsedMs: Date.now() - startedAt,
      providerTrace: [],
    };
  }

  const sources = normalizeWebSearchSources(
    result.sources.map((source) => ({
      title: source.title,
      url: source.url,
      snippet: source.snippet,
      provider: "openai",
    })),
    { maxResults: opts.maxResults, provider: "openai" },
  );

  return {
    ok: true,
    searched: true,
    provider: "openai",
    query: result.query,
    sources,
    ...(result.answerPreview ? { answerPreview: result.answerPreview } : {}),
    elapsedMs: Date.now() - startedAt,
    providerTrace: [],
  };
}

export const openAiWebSearchProvider: WebSearchAdapter = {
  provider: "openai",
  search: ({ query, maxResults }) => runOpenAiFallbackWebSearch({ query, maxResults }),
};
