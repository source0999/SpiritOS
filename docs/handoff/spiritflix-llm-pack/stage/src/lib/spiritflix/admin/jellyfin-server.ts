import { normalizeJellyfinServerUrl } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";

const DEFAULT_SERVER = "http://127.0.0.1:8096";

const allowedHosts = new Set([
  "spirit.tailb69ea6.ts.net:8096",
  "100.111.32.31:8096",
  "127.0.0.1:8096",
  "localhost:8096",
]);

export interface SpiritFlixServerJellyfinCredentials {
  serverUrl: string;
  accessToken: string;
  userId: string;
}

function isAllowedServer(serverUrl: string): boolean {
  try {
    const parsed = new URL(serverUrl);
    return (parsed.protocol === "http:" || parsed.protocol === "https:") && allowedHosts.has(parsed.host);
  } catch {
    return false;
  }
}

export function getServerJellyfinCredentials(): SpiritFlixServerJellyfinCredentials | null {
  const accessToken = process.env.JELLYFIN_API_KEY?.trim();
  const serverUrl = normalizeJellyfinServerUrl(process.env.JELLYFIN_URL?.trim() || DEFAULT_SERVER);
  const userId = process.env.JELLYFIN_USER_ID?.trim();

  if (!accessToken || !isAllowedServer(serverUrl)) return null;

  return { serverUrl, accessToken, userId: userId || "" };
}

async function jellyfinRequest<T>(credentials: SpiritFlixServerJellyfinCredentials, path: string): Promise<T> {
  const response = await fetch(`${credentials.serverUrl}${path}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      "X-Emby-Token": credentials.accessToken,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Jellyfin server request failed with status ${response.status}.`);
  }

  return (await response.json()) as T;
}

export async function resolveServerJellyfinUserId(credentials: SpiritFlixServerJellyfinCredentials): Promise<string> {
  if (credentials.userId) return credentials.userId;
  const users = await jellyfinRequest<Array<{ Id: string }>>(credentials, "/Users");
  const userId = users[0]?.Id;
  if (!userId) throw new Error("No Jellyfin users available for SpiritFlix admin.");
  return userId;
}

export async function listServerJellyfinVideoItems(credentials: SpiritFlixServerJellyfinCredentials, userId: string): Promise<JellyfinItem[]> {
  const query = new URLSearchParams({
    Recursive: "true",
    IncludeItemTypes: "Movie,Episode,Video",
    Fields: "Path,MediaSources,ImageTags,BackdropImageTags,DateCreated",
    ImageTypeLimit: "1",
    EnableImageTypes: "Primary,Backdrop,Thumb",
    Limit: "500",
  });

  const payload = await jellyfinRequest<{ Items?: JellyfinItem[] }>(credentials, `/Users/${userId}/Items?${query}`);
  return payload.Items ?? [];
}

export function jellyfinImagePath(
  itemId: string,
  imageType: "Primary" | "Thumb" | "Backdrop",
  tag: string | undefined,
  width = 360,
): string {
  const query = new URLSearchParams({
    maxWidth: String(width),
    quality: "88",
    ...(tag ? { tag } : {}),
  });
  return `/Items/${itemId}/Images/${imageType}?${query}`;
}
