import "server-only";

import type { WebSearchProviderConfig } from "@/lib/server/web-search/types";

const DEFAULT_PROVIDER_ORDER = ["cache", "searxng"];
const DEFAULT_SEARXNG_URL = "";
const DEFAULT_MAX_RESULTS = 8;

function readBoolean(raw: string | undefined, defaultValue: boolean): boolean {
  const value = raw?.trim().toLowerCase();
  if (!value) return defaultValue;
  if (value === "1" || value === "true" || value === "yes" || value === "on") return true;
  if (value === "0" || value === "false" || value === "no" || value === "off") return false;
  return defaultValue;
}

function readPositiveInt(raw: string | undefined, defaultValue: number, maxValue?: number): number {
  const parsed = Number.parseInt(raw?.trim() ?? "", 10);
  if (!Number.isFinite(parsed) || parsed <= 0) return defaultValue;
  return typeof maxValue === "number" ? Math.min(parsed, maxValue) : parsed;
}

function readProviderOrder(raw: string | undefined): string[] {
  const providers = (raw ?? DEFAULT_PROVIDER_ORDER.join(","))
    .split(",")
    .map((provider) => provider.trim().toLowerCase())
    .filter(Boolean);
  return providers.length ? providers : [...DEFAULT_PROVIDER_ORDER];
}

export function getWebSearchProviderConfig(
  env: Partial<Record<string, string | undefined>> = process.env,
): WebSearchProviderConfig {
  const maxResults = readPositiveInt(env.WEB_SEARCH_MAX_RESULTS, DEFAULT_MAX_RESULTS, 12);

  return {
    enabled: readBoolean(env.WEB_SEARCH_ENABLED, false),
    providerOrder: readProviderOrder(env.WEB_SEARCH_PROVIDER_ORDER),
    maxResults,
    cache: {
      enabled: readBoolean(env.WEB_SEARCH_CACHE_ENABLED, true),
      ttlSeconds: readPositiveInt(env.WEB_SEARCH_CACHE_TTL_SECONDS, 86_400),
    },
    searxng: {
      url: env.SEARXNG_URL?.trim() || DEFAULT_SEARXNG_URL,
      maxResults: readPositiveInt(env.SEARXNG_MAX_RESULTS, maxResults, 12),
      timeoutMs: readPositiveInt(env.SEARXNG_TIMEOUT_MS, 10_000),
    },
    fetchPage: {
      enabled: readBoolean(env.WEB_SEARCH_FETCH_PAGE_ENABLED, false),
      timeoutMs: readPositiveInt(env.WEB_SEARCH_FETCH_TIMEOUT_MS, 10_000),
      respectRobots: readBoolean(env.WEB_SEARCH_RESPECT_ROBOTS, true),
      userAgent: env.WEB_SEARCH_USER_AGENT?.trim() || "SpiritOSLocalSearch/0.1",
    },
    paidFallback: {
      enabled: readBoolean(env.WEB_SEARCH_PAID_FALLBACK_ENABLED, false),
      requireApproval: readBoolean(
        env.WEB_SEARCH_PAID_FALLBACK_REQUIRES_APPROVAL ?? env.WEB_SEARCH_REQUIRE_APPROVAL_FOR_PAID,
        true,
      ),
    },
  };
}
