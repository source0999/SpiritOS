const HOST_MEDIA_PREFIX = "/mnt/spirit-8tb/media";
const CONTAINER_MEDIA_PREFIX = "/media";
const HOST_INBOX_PREFIX = "/mnt/spirit-8tb/media-inbox";
const CONTAINER_INBOX_PREFIX = "/media-inbox";

export function normalizeAdminPath(value?: string): string {
  return (value ?? "")
    .trim()
    .replace(/\\/g, "/")
    .replace(/\/+/g, "/")
    .replace(/\/$/, "")
    .toLowerCase();
}

/** Host/container alias expansion for Jellyfin path matching. */
export function expandSpiritFlixPathAliases(value?: string): string[] {
  const normalized = normalizeAdminPath(value);
  if (!normalized) return [];

  const aliases = new Set<string>([normalized]);

  if (normalized === HOST_MEDIA_PREFIX || normalized.startsWith(`${HOST_MEDIA_PREFIX}/`)) {
    aliases.add(CONTAINER_MEDIA_PREFIX + normalized.slice(HOST_MEDIA_PREFIX.length));
  } else if (normalized === CONTAINER_MEDIA_PREFIX || normalized.startsWith(`${CONTAINER_MEDIA_PREFIX}/`)) {
    aliases.add(HOST_MEDIA_PREFIX + normalized.slice(CONTAINER_MEDIA_PREFIX.length));
  }

  if (normalized === HOST_INBOX_PREFIX || normalized.startsWith(`${HOST_INBOX_PREFIX}/`)) {
    aliases.add(CONTAINER_INBOX_PREFIX + normalized.slice(HOST_INBOX_PREFIX.length));
  } else if (normalized === CONTAINER_INBOX_PREFIX || normalized.startsWith(`${CONTAINER_INBOX_PREFIX}/`)) {
    aliases.add(HOST_INBOX_PREFIX + normalized.slice(CONTAINER_INBOX_PREFIX.length));
  }

  return [...aliases];
}

export function adminPathsEquivalent(left?: string, right?: string): boolean {
  const leftAliases = expandSpiritFlixPathAliases(left);
  const rightAliases = expandSpiritFlixPathAliases(right);
  return leftAliases.some((alias) => rightAliases.includes(alias));
}
