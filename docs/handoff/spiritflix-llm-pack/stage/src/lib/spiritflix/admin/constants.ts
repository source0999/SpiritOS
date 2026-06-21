export const SPIRITFLIX_DATA_ROOT = "/mnt/spirit-8tb";
export const SPIRITFLIX_MEDIA_ROOT = "/mnt/spirit-8tb/media";
export const SPIRITFLIX_MEDIA_INBOX = "/mnt/spirit-8tb/media-inbox";
export const SPIRITFLIX_ADMIN_THUMBNAIL_CACHE_ROOT = "/mnt/spirit-8tb/media/.spiritflix-admin/thumbnails";

/** Level 1R4 passed — Level 2 guarded CRUD is active. */
export const SPIRITFLIX_ADMIN_LEVEL2_GATED = false;
export const SPIRITFLIX_ADMIN_LEVEL2_GATE_MESSAGE = "Level 2 management is gated until file view passes.";

export interface SpiritFlixAdminNavEntry {
  path: string;
  label: string;
}

/** Sidebar quick-nav: media root first, then library folders. */
export const SPIRITFLIX_ADMIN_NAV: SpiritFlixAdminNavEntry[] = [
  { path: SPIRITFLIX_MEDIA_ROOT, label: "media" },
  { path: `${SPIRITFLIX_MEDIA_ROOT}/yes`, label: "yes" },
  { path: `${SPIRITFLIX_MEDIA_ROOT}/anime`, label: "anime" },
  { path: `${SPIRITFLIX_MEDIA_ROOT}/movies`, label: "movies" },
  { path: `${SPIRITFLIX_MEDIA_ROOT}/tv`, label: "tv" },
  { path: `${SPIRITFLIX_MEDIA_ROOT}/music`, label: "music" },
  { path: `${SPIRITFLIX_MEDIA_ROOT}/other`, label: "other" },
  { path: SPIRITFLIX_MEDIA_INBOX, label: "media-inbox" },
];

export function activeAdminNavPath(currentPath: string, entries: SpiritFlixAdminNavEntry[] = SPIRITFLIX_ADMIN_NAV): string {
  const normalized = currentPath.replace(/\\/g, "/").replace(/\/+$/, "");
  const sorted = [...entries].sort((left, right) => right.path.length - left.path.length);
  return sorted.find((entry) => normalized === entry.path || normalized.startsWith(`${entry.path}/`))?.path ?? "";
}
