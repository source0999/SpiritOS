import { SPIRITFLIX_MEDIA_ROOT } from "./constants";

/** Top-level library folders and media root — never rename/move/soft-delete these. */
export const SPIRITFLIX_ADMIN_PROTECTED_PATHS = [
  SPIRITFLIX_MEDIA_ROOT,
  `${SPIRITFLIX_MEDIA_ROOT}/yes`,
  `${SPIRITFLIX_MEDIA_ROOT}/anime`,
  `${SPIRITFLIX_MEDIA_ROOT}/movies`,
  `${SPIRITFLIX_MEDIA_ROOT}/tv`,
  `${SPIRITFLIX_MEDIA_ROOT}/music`,
  `${SPIRITFLIX_MEDIA_ROOT}/other`,
];

export function normalizeSpiritFlixAdminPath(candidate: string): string {
  return candidate.replace(/\\/g, "/").replace(/\/+$/, "");
}

export function isProtectedSpiritFlixAdminPath(candidate: string): boolean {
  const normalized = normalizeSpiritFlixAdminPath(candidate);
  return SPIRITFLIX_ADMIN_PROTECTED_PATHS.some((protectedPath) => normalizeSpiritFlixAdminPath(protectedPath) === normalized);
}

export function isSpiritFlixAdminTrashPath(candidate: string): boolean {
  return normalizeSpiritFlixAdminPath(candidate).includes("/.trash/");
}

export function assertWritableSpiritFlixAdminPath(candidate: string, operation: string): void {
  if (isProtectedSpiritFlixAdminPath(candidate)) {
    throw new Error(`Cannot ${operation} protected library path.`);
  }

  const normalized = normalizeSpiritFlixAdminPath(candidate);
  const jellyfinSystemPatterns = [/jellyfin/i, /library\.db$/i, /system\.xml$/i, /\.sqlite$/i];
  if (jellyfinSystemPatterns.some((pattern) => pattern.test(normalized))) {
    throw new Error(`Cannot ${operation} Jellyfin system path.`);
  }
}
