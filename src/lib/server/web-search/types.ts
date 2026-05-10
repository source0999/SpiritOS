import "server-only";

export type WebSearchProvider =
  | "cache"
  | "searxng"
  | "ddgs"
  | "fetch"
  | "openai"
  | "manual";

export type WebSearchStatus = "used" | "skipped" | "disabled" | "failed";

export type WebSearchProviderTrace = {
  provider: string;
  status: "skipped" | "attempted" | "used" | "failed";
  reason?: string;
  elapsedMs?: number;
  sourceCount?: number;
};

export type WebSearchSource = {
  title: string;
  url: string;
  snippet?: string;
  publishedAt?: string;
  provider?: WebSearchProvider;
};

export type WebSearchOk = {
  ok: true;
  searched: true;
  provider: WebSearchProvider;
  query: string;
  sources: WebSearchSource[];
  answerPreview?: string;
  elapsedMs: number;
  providerTrace: WebSearchProviderTrace[];
};

export type WebSearchFail = {
  ok: false;
  searched: boolean;
  provider: WebSearchProvider;
  error: string;
  detail?: string;
  elapsedMs: number;
  providerTrace: WebSearchProviderTrace[];
};

export type WebSearchResult = WebSearchOk | WebSearchFail;

export type WebSearchProviderConfig = {
  enabled: boolean;
  providerOrder: string[];
  maxResults: number;
  cache: {
    enabled: boolean;
    ttlSeconds: number;
  };
  searxng: {
    url: string;
    maxResults: number;
    timeoutMs: number;
  };
  fetchPage: {
    enabled: boolean;
    timeoutMs: number;
    respectRobots: boolean;
    userAgent: string;
  };
  paidFallback: {
    enabled: boolean;
    requireApproval: boolean;
  };
};

export type WebSearchAdapterRequest = {
  query: string;
  maxResults: number;
  config: WebSearchProviderConfig;
};

export type WebSearchAdapter = {
  provider: WebSearchProvider;
  search: (request: WebSearchAdapterRequest) => Promise<WebSearchResult>;
};
