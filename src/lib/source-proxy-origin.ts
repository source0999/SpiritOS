import { Agent, fetch } from "undici";

// ── Source proxy URL for Next.js → FastAPI hops ─────────────────────────────
// `proxy:dev` = HTTP; `proxy:https` = HTTPS on the same port. Without
// SOURCE_PROXY_ORIGIN we try HTTP then HTTPS so both setups work locally.
const httpsAgent = new Agent({
  connect: { rejectUnauthorized: false },
});

// ── Long-lived SSE / streaming hops ─────────────────────────────────────────
// undici `buildConnector` defaults connect `timeout` to 10s when omitted (see
// node_modules/undici/lib/core/connect.js). JSON hops are fine; bridging
// `/v1/tasks/.../stream` is not — slow accept or queue behind burst traffic hit
// UND_ERR_CONNECT_TIMEOUT and Next returns 500 while the proxy is healthy.
/** Options merged into dedicated stream Agents (exported for unit tests). */
export const SOURCE_PROXY_STREAM_UNDICI_OPTIONS = {
  connectTimeout: 0,
  bodyTimeout: 0,
} as const;

const httpsStreamAgent = new Agent({
  ...SOURCE_PROXY_STREAM_UNDICI_OPTIONS,
  connect: { rejectUnauthorized: false },
});

const httpStreamAgent = new Agent({
  ...SOURCE_PROXY_STREAM_UNDICI_OPTIONS,
});

function streamDispatcherForBase(base: string) {
  return base.startsWith("https://") ? httpsStreamAgent : httpStreamAgent;
}

type UndiciFetchInit = NonNullable<Parameters<typeof fetch>[1]>;

function trimTrailingSlash(base: string): string {
  return base.replace(/\/+$/, "");
}

/** Ordered bases to try when connecting to the source proxy. */
export function getSourceProxyBases(): string[] {
  const explicit = process.env.SOURCE_PROXY_ORIGIN?.trim();
  if (explicit) {
    return [trimTrailingSlash(explicit)];
  }
  const tlsOnly =
    process.env.SOURCE_PROXY_TLS === "true" ||
    process.env.SOURCE_PROXY_USE_HTTPS === "true";
  const host = process.env.SOURCE_PROXY_HOST ?? "127.0.0.1";
  const port = process.env.SOURCE_PROXY_PORT ?? "8787";
  if (tlsOnly) {
    return [`https://${host}:${port}`];
  }
  return [`http://${host}:${port}`, `https://${host}:${port}`];
}

/** First candidate base (for legacy call sites that need a single string). */
export function getSourceProxyOrigin(): string {
  const bases = getSourceProxyBases();
  return bases[0] ?? "http://127.0.0.1:8787";
}

export function getSourceProxyUndiciDispatcher(originOrUrl: string) {
  const scheme = originOrUrl.startsWith("https://") ? "https" : "http";
  return scheme === "https" ? httpsAgent : undefined;
}

/**
 * GET/POST/etc. to the source proxy. When `SOURCE_PROXY_ORIGIN` is unset,
 * tries HTTP then HTTPS so `npm run proxy:dev` and `npm run proxy:https` both work.
 *
 * @param pathAndQuery must start with `/` (e.g. `/v1/self/status` or `/v1/foo?x=1`)
 */
export async function sourceProxyFetch(
  pathAndQuery: string,
  init: UndiciFetchInit = {},
): Promise<Awaited<ReturnType<typeof fetch>>> {
  if (!pathAndQuery.startsWith("/")) {
    throw new Error(
      `sourceProxyFetch path must start with /, got: ${pathAndQuery.slice(0, 80)}`,
    );
  }
  const bases = getSourceProxyBases();
  let lastError: unknown;
  for (const base of bases) {
    const url = `${trimTrailingSlash(base)}${pathAndQuery}`;
    try {
      const dispatcher = getSourceProxyUndiciDispatcher(base);
      return await fetch(url, { ...init, dispatcher });
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}

/**
 * Same multi-base fallback as {@link sourceProxyFetch}, but undici timeouts suit
 * open-ended SSE (no default 10s connect cap; no body idle cap between events).
 */
export async function sourceProxyStreamFetch(
  pathAndQuery: string,
  init: UndiciFetchInit = {},
): Promise<Awaited<ReturnType<typeof fetch>>> {
  if (!pathAndQuery.startsWith("/")) {
    throw new Error(
      `sourceProxyStreamFetch path must start with /, got: ${pathAndQuery.slice(0, 80)}`,
    );
  }
  const bases = getSourceProxyBases();
  let lastError: unknown;
  for (const base of bases) {
    const url = `${trimTrailingSlash(base)}${pathAndQuery}`;
    try {
      const dispatcher = streamDispatcherForBase(base);
      return await fetch(url, { ...init, dispatcher });
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}
