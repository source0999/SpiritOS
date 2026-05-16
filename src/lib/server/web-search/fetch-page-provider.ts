import "server-only";

import { resolveVerifiedHttpUrl } from "@/lib/verified-http-url";
import { normalizeWebSearchSources } from "@/lib/server/web-search/source-normalizer";
import type {
  WebSearchAdapter,
  WebSearchProviderConfig,
  WebSearchResult,
} from "@/lib/server/web-search/types";

type RobotsRule = {
  directive: "allow" | "disallow";
  path: string;
};

type RobotsGroup = {
  agents: string[];
  rules: RobotsRule[];
};

function elapsedSince(startedAt: number): number {
  return Date.now() - startedAt;
}

function failure(opts: {
  startedAt: number;
  error: string;
  detail?: string;
  searched?: boolean;
}): WebSearchResult {
  return {
    ok: false,
    searched: opts.searched ?? true,
    provider: "fetch",
    error: opts.error,
    ...(opts.detail ? { detail: opts.detail } : {}),
    elapsedMs: elapsedSince(opts.startedAt),
    providerTrace: [],
  };
}

function stripHtml(value: string): string {
  return value
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function decodeHtmlEntities(value: string): string {
  return value
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, "\"")
    .replace(/&#39;/g, "'");
}

function extractFirstMatch(html: string, regex: RegExp): string | undefined {
  const match = regex.exec(html);
  const value = match?.[1]?.trim();
  return value ? decodeHtmlEntities(stripHtml(value)) : undefined;
}

function extractMetaContent(html: string, name: string): string | undefined {
  const escapedName = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const metaRegex = new RegExp(
    `<meta\\s+[^>]*(?:name|property)=["']${escapedName}["'][^>]*content=["']([^"']+)["'][^>]*>`,
    "i",
  );
  return extractFirstMatch(html, metaRegex);
}

function extractCanonicalUrl(html: string): string | undefined {
  return extractFirstMatch(html, /<link\s+[^>]*rel=["']canonical["'][^>]*href=["']([^"']+)["'][^>]*>/i);
}

function extractReadableSnippet(html: string): string | undefined {
  const paragraphs = html.match(/<p\b[^>]*>[\s\S]*?<\/p>/gi) ?? [];
  for (const paragraph of paragraphs) {
    const text = decodeHtmlEntities(stripHtml(paragraph));
    if (text.length >= 40) return text.slice(0, 500).trim();
  }
  const body = extractFirstMatch(html, /<body\b[^>]*>([\s\S]*?)<\/body>/i);
  return body ? body.slice(0, 500).trim() : undefined;
}

function parseRobotsTxt(text: string): RobotsGroup[] {
  const groups: RobotsGroup[] = [];
  let current: RobotsGroup | undefined;

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.replace(/#.*$/, "").trim();
    if (!line) continue;
    const separator = line.indexOf(":");
    if (separator < 0) continue;

    const key = line.slice(0, separator).trim().toLowerCase();
    const value = line.slice(separator + 1).trim();

    if (key === "user-agent") {
      if (!current || current.rules.length > 0) {
        current = { agents: [], rules: [] };
        groups.push(current);
      }
      current.agents.push(value.toLowerCase());
      continue;
    }

    if ((key === "allow" || key === "disallow") && current) {
      current.rules.push({ directive: key, path: value });
    }
  }

  return groups;
}

function productToken(userAgent: string): string {
  return userAgent.split(/[\/\s;]/)[0]?.toLowerCase() || "*";
}

function ruleMatches(rulePath: string, pathWithQuery: string): boolean {
  if (!rulePath) return false;
  const escaped = rulePath
    .replace(/[.+?^${}()|[\]\\]/g, "\\$&")
    .replace(/\*/g, ".*")
    .replace(/\\\$$/, "$");
  return new RegExp(`^${escaped}`).test(pathWithQuery);
}

export function isAllowedByRobotsTxt(text: string, targetUrl: string, userAgent: string): boolean {
  const groups = parseRobotsTxt(text);
  if (groups.length === 0) return true;

  const token = productToken(userAgent);
  const exactGroups = groups.filter((group) => group.agents.some((agent) => agent === token));
  const wildcardGroups = groups.filter((group) => group.agents.some((agent) => agent === "*"));
  const applicable = exactGroups.length ? exactGroups : wildcardGroups;
  if (applicable.length === 0) return true;

  const url = new URL(targetUrl);
  const pathWithQuery = `${url.pathname}${url.search}`;
  let best: RobotsRule | undefined;

  for (const group of applicable) {
    for (const rule of group.rules) {
      if (!ruleMatches(rule.path, pathWithQuery)) continue;
      if (!best || rule.path.length > best.path.length || (rule.path.length === best.path.length && rule.directive === "allow")) {
        best = rule;
      }
    }
  }

  return best?.directive !== "disallow";
}

async function fetchTextWithTimeout(
  fetchImpl: typeof fetch,
  url: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetchImpl(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function robotsAllows(opts: {
  targetUrl: string;
  config: WebSearchProviderConfig;
  fetchImpl: typeof fetch;
}): Promise<{ allowed: true } | { allowed: false; reason: string }> {
  if (!opts.config.fetchPage.respectRobots) return { allowed: true };

  const url = new URL(opts.targetUrl);
  const robotsUrl = `${url.origin}/robots.txt`;

  try {
    const response = await fetchTextWithTimeout(
      opts.fetchImpl,
      robotsUrl,
      {
        method: "GET",
        headers: { "User-Agent": opts.config.fetchPage.userAgent },
        redirect: "follow",
      },
      opts.config.fetchPage.timeoutMs,
    );

    // Conservative best-effort robots handling:
    // - 4xx means no robots policy was found for this origin, so access may proceed.
    // - 5xx, network errors, and timeouts are treated as unreachable and block fetch.
    if (response.status >= 400 && response.status < 500) return { allowed: true };
    if (!response.ok) return { allowed: false, reason: "robots_unreachable" };

    const text = await response.text();
    return isAllowedByRobotsTxt(text, opts.targetUrl, opts.config.fetchPage.userAgent)
      ? { allowed: true }
      : { allowed: false, reason: "robots_disallowed" };
  } catch {
    return { allowed: false, reason: "robots_unreachable" };
  }
}

export async function runFetchPageWebSearch(opts: {
  query: string;
  maxResults: number;
  config: WebSearchProviderConfig;
  fetchImpl?: typeof fetch;
}): Promise<WebSearchResult> {
  const startedAt = Date.now();
  if (!opts.config.fetchPage.enabled) {
    return failure({ startedAt, error: "fetch_page_disabled", searched: false });
  }

  const targetUrl = resolveVerifiedHttpUrl(opts.query);
  if (!targetUrl) {
    return failure({
      startedAt,
      error: "fetch_query_not_url",
      detail: "Direct page fetch only accepts an HTTP(S) URL.",
      searched: false,
    });
  }

  const fetchImpl = opts.fetchImpl ?? fetch;
  const robots = await robotsAllows({ targetUrl, config: opts.config, fetchImpl });
  if (!robots.allowed) {
    return failure({ startedAt, error: robots.reason, searched: false });
  }

  try {
    const response = await fetchTextWithTimeout(
      fetchImpl,
      targetUrl,
      {
        method: "GET",
        headers: {
          Accept: "text/html,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.5",
          "User-Agent": opts.config.fetchPage.userAgent,
        },
        redirect: "follow",
      },
      opts.config.fetchPage.timeoutMs,
    );

    const text = await response.text();
    if (!response.ok) {
      return failure({ startedAt, error: `fetch_${response.status}`, detail: text.slice(0, 400) });
    }

    const canonical = resolveVerifiedHttpUrl(extractCanonicalUrl(text)) ?? targetUrl;
    const title = extractMetaContent(text, "og:title") ?? extractFirstMatch(text, /<title\b[^>]*>([\s\S]*?)<\/title>/i);
    const snippet = extractMetaContent(text, "description") ?? extractMetaContent(text, "og:description") ?? extractReadableSnippet(text);
    const sources = normalizeWebSearchSources(
      [{ title, url: canonical, snippet, provider: "fetch" }],
      { maxResults: opts.maxResults, provider: "fetch" },
    );

    return {
      ok: true,
      searched: true,
      provider: "fetch",
      query: opts.query.trim(),
      sources,
      answerPreview: snippet,
      elapsedMs: elapsedSince(startedAt),
      providerTrace: [],
    };
  } catch (error) {
    const aborted = error instanceof Error && error.name === "AbortError";
    return failure({
      startedAt,
      error: aborted ? "fetch_timeout" : "fetch_failed",
      detail: error instanceof Error ? error.message : String(error),
    });
  }
}

export const fetchPageProvider: WebSearchAdapter = {
  provider: "fetch",
  search: ({ query, maxResults, config }) => runFetchPageWebSearch({ query, maxResults, config }),
};
