import { Agent, fetch } from "undici";
import http from "node:http";
import https from "node:https";

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

/** Options for long JSON calls such as prompt-packet model generation. */
export const SOURCE_PROXY_LONG_JSON_UNDICI_OPTIONS = {
  connectTimeout: 0,
  bodyTimeout: 0,
  headersTimeout: 0,
} as const;

const httpsStreamAgent = new Agent({
  ...SOURCE_PROXY_STREAM_UNDICI_OPTIONS,
  connect: { rejectUnauthorized: false },
});

const httpStreamAgent = new Agent({
  ...SOURCE_PROXY_STREAM_UNDICI_OPTIONS,
});

const httpsLongJsonAgent = new Agent({
  ...SOURCE_PROXY_LONG_JSON_UNDICI_OPTIONS,
  connect: { rejectUnauthorized: false },
});

const httpLongJsonAgent = new Agent({
  ...SOURCE_PROXY_LONG_JSON_UNDICI_OPTIONS,
});

function streamDispatcherForBase(base: string) {
  return base.startsWith("https://") ? httpsStreamAgent : httpStreamAgent;
}

function longJsonDispatcherForBase(base: string) {
  return base.startsWith("https://") ? httpsLongJsonAgent : httpLongJsonAgent;
}

type UndiciFetchInit = NonNullable<Parameters<typeof fetch>[1]>;

type SourceProxyFastJsonFetchOptions = {
  perCandidateTimeoutMs?: number;
};

type NativeFastJsonBody = string | Buffer | Uint8Array;

function sourceProxyFastJsonCandidateTimeoutMs(
  options: SourceProxyFastJsonFetchOptions = {},
) {
  if (options.perCandidateTimeoutMs != null) {
    return Math.max(250, options.perCandidateTimeoutMs);
  }
  const raw = Number(process.env.SOURCE_PROXY_FAST_JSON_CANDIDATE_TIMEOUT_MS ?? "");
  if (Number.isFinite(raw) && raw > 0) return Math.max(250, raw);
  return 5_000;
}

function nativeFastJsonBody(body: UndiciFetchInit["body"]): NativeFastJsonBody | undefined {
  if (body == null) return undefined;
  if (typeof body === "string" || Buffer.isBuffer(body) || body instanceof Uint8Array) {
    return body;
  }
  throw new Error("sourceProxyFastJsonFetch only supports buffered JSON request bodies");
}

function nativeFastJsonHeaders(headers: UndiciFetchInit["headers"]): Record<string, string> {
  const output: Record<string, string> = {};
  if (!headers) return output;
  const entries =
    headers instanceof Headers
      ? [...headers.entries()]
      : Array.isArray(headers)
        ? headers
        : Object.entries(headers as Record<string, string>);
  for (const [key, value] of entries) {
    output[key] = String(value);
  }
  return output;
}

function responseHeadersFromNative(headers: http.IncomingHttpHeaders): Headers {
  const output = new Headers();
  for (const [key, value] of Object.entries(headers)) {
    if (Array.isArray(value)) {
      for (const item of value) output.append(key, item);
    } else if (value != null) {
      output.set(key, String(value));
    }
  }
  return output;
}

function nativeFastJsonFetch(
  url: string,
  init: UndiciFetchInit,
  timeoutMs: number,
): Promise<Response> {
  const parsed = new URL(url);
  const isHttps = parsed.protocol === "https:";
  const body = nativeFastJsonBody(init.body);
  const headers = nativeFastJsonHeaders(init.headers);
  if (body != null && headers["content-length"] == null && headers["Content-Length"] == null) {
    headers["content-length"] = String(Buffer.byteLength(body));
  }

  return new Promise((resolve, reject) => {
    const request = (isHttps ? https : http).request(
      {
        headers,
        hostname: parsed.hostname,
        method: String(init.method ?? "GET"),
        path: `${parsed.pathname}${parsed.search}`,
        port: parsed.port,
        rejectUnauthorized: false,
      },
      (response) => {
        const chunks: Buffer[] = [];
        response.on("data", (chunk) => chunks.push(Buffer.from(chunk)));
        response.on("end", () => {
          resolve(
            new Response(Buffer.concat(chunks), {
              headers: responseHeadersFromNative(response.headers),
              status: response.statusCode ?? 502,
              statusText: response.statusMessage,
            }),
          );
        });
      },
    );
    request.setTimeout(timeoutMs, () => {
      request.destroy(new Error("source_proxy_candidate_timeout"));
    });
    request.on("error", reject);
    if (init.signal) {
      const signal = init.signal as AbortSignal;
      if (signal.aborted) {
        request.destroy(new Error("source_proxy_request_aborted"));
      } else {
        signal.addEventListener(
          "abort",
          () => request.destroy(new Error("source_proxy_request_aborted")),
          { once: true },
        );
      }
    }
    if (body != null) request.write(body);
    request.end();
  });
}

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
 * Fast JSON hop for short control-plane calls. The default HTTP->HTTPS fallback
 * can hang on a TLS-only proxy when the first plain HTTP candidate accepts the
 * socket but never sends HTTP headers. Task creation must return an id quickly,
 * so each candidate gets a small deadline before trying the next base.
 */
export async function sourceProxyFastJsonFetch(
  pathAndQuery: string,
  init: UndiciFetchInit = {},
  options: SourceProxyFastJsonFetchOptions = {},
): Promise<Response> {
  if (!pathAndQuery.startsWith("/")) {
    throw new Error(
      `sourceProxyFastJsonFetch path must start with /, got: ${pathAndQuery.slice(0, 80)}`,
    );
  }
  const bases = [...getSourceProxyBases()].sort((left, right) => {
    if (left.startsWith("https://") === right.startsWith("https://")) return 0;
    return left.startsWith("https://") ? -1 : 1;
  });
  const perCandidateTimeoutMs = sourceProxyFastJsonCandidateTimeoutMs(options);
  let lastError: unknown;
  for (const base of bases) {
    const url = `${trimTrailingSlash(base)}${pathAndQuery}`;
    try {
      return await nativeFastJsonFetch(url, init, perCandidateTimeoutMs);
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

/**
 * Same multi-base fallback as {@link sourceProxyFetch}, but intended for
 * long-running JSON responses where the browser owns the user-facing timeout.
 */
export async function sourceProxyLongJsonFetch(
  pathAndQuery: string,
  init: UndiciFetchInit = {},
): Promise<Awaited<ReturnType<typeof fetch>>> {
  if (!pathAndQuery.startsWith("/")) {
    throw new Error(
      `sourceProxyLongJsonFetch path must start with /, got: ${pathAndQuery.slice(0, 80)}`,
    );
  }
  const bases = getSourceProxyBases();
  let lastError: unknown;
  for (const base of bases) {
    const url = `${trimTrailingSlash(base)}${pathAndQuery}`;
    try {
      const dispatcher = longJsonDispatcherForBase(base);
      return await fetch(url, { ...init, dispatcher });
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}
