// ── buildAllowedDevOrigins - Tailscale/LAN HMR allowlist (Prompt 9J) ───────────────
// > Lives next to next.config.ts so Next can import without @ path drama.
// > Hostnames only - no protocol, no port. Wildcard: `*.ts.net` per Next docs.

const DEFAULT_DEV_HOSTS = [
  "localhost",
  "127.0.0.1",
  "10.0.0.186",
  "100.111.32.31",
  "*.ts.net",
] as const;

/**
 * Merge baked-in homelab defaults with `NEXT_ALLOWED_DEV_ORIGINS` (comma-separated).
 */
export function buildAllowedDevOrigins(
  env: Record<string, string | undefined> = process.env,
): string[] {
  const raw = env.NEXT_ALLOWED_DEV_ORIGINS?.trim();
  const extra = raw
    ? raw
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
    : [];
  return [...new Set([...DEFAULT_DEV_HOSTS, ...extra])];
}
