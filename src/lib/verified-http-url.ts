// ── verified-http-url - shared digest / policy / header URL gate ─────────────────
// > Client-safe: `research-source-enforcement` is imported by SpiritChat; do not
//   depend on `server-only` OpenAI modules here.

/**
 * Bare host / protocol-relative → https so OpenAI payload quirks still produce
 * one canonical string for digest lines and `x-spirit-web-sources`.
 */
export function normalizeToHttpUrl(raw: string | undefined): string | undefined {
  let t = (raw ?? "").trim();
  // OpenAI / markdown sometimes wraps links - strip before host detection.
  t = t.replace(/^<+/, "").replace(/>+$/, "").trim();
  if (!t) return undefined;
  if (/^(javascript|data|mailto|vbscript):/i.test(t)) return undefined;
  if (/^https?:\/\//i.test(t)) return t;
  if (t.startsWith("//")) {
    const host = t.slice(2).replace(/^\/+/, "");
    return host ? `https://${host}` : undefined;
  }
  if (/[\s<>"]/.test(t)) return undefined;
  if (!/^[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}/.test(t)) return undefined;
  return `https://${t}`;
}

/**
 * After normalization, only true http(s) origins count as “verified” everywhere:
 * digest, Teacher budget, policy `searchUsed`, telemetry headers.
 */
export function resolveVerifiedHttpUrl(raw: string | undefined): string | undefined {
  const n = normalizeToHttpUrl(raw);
  if (!n) return undefined;
  return /^https?:\/\//i.test(n) ? n : undefined;
}

/** `normalizeToHttpUrl` then strict `^https?:` - post-normalize bare hosts count as verified. */
export function isVerifiedHttpUrl(url: string | undefined): boolean {
  return Boolean(resolveVerifiedHttpUrl(url));
}
