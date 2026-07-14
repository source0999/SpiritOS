import "server-only";

import { randomBytes, randomUUID } from "node:crypto";

import { e2eCookieName, getE2ESession } from "./e2e-session";

export const SPIRITFLIX_SESSION_COOKIE = "spiritflix_session";
export const SPIRITFLIX_SESSION_USER = "__spiritflix_session__";
export const SPIRITFLIX_SESSION_TTL_SECONDS = 15 * 60;
export const ALLOWED_JELLYFIN_HOSTS = new Set([
  "10.0.0.186:8096",
  "spirit.tailb69ea6.ts.net:8096",
  "100.111.32.31:8096",
  "127.0.0.1:8096",
  "localhost:8096",
]);

type StoredSession = {
  authorization: string;
  csrf: string;
  expiresAt: number;
  serverUrl: string;
  userId: string;
  username: string;
};

export type SpiritFlixMediaSession = {
  authorization: string;
  csrf?: string;
  kind: "e2e" | "ordinary";
  serverUrl: string;
  userId: string;
};

const sessions = new Map<string, StoredSession>();

export function normalizeSpiritFlixServer(serverUrl: string) {
  try {
    const parsed = new URL(serverUrl.trim());
    if ((parsed.protocol !== "http:" && parsed.protocol !== "https:") || !ALLOWED_JELLYFIN_HOSTS.has(parsed.host)) return null;
    return `${parsed.protocol}//${parsed.host}`;
  } catch {
    return null;
  }
}

export function isAllowedSpiritFlixPath(path: string) {
  return path.startsWith("/") && !path.startsWith("//") && !path.includes("://") && !path.includes("\\");
}

function expired(id: string, session: StoredSession | undefined) {
  if (!session || session.expiresAt <= Date.now()) {
    if (id) sessions.delete(id);
    return true;
  }
  return false;
}

export function resolveOrdinarySession(id?: string) {
  const session = id ? sessions.get(id) : undefined;
  return expired(id ?? "", session) ? null : session!;
}

export async function createOrdinarySession(input: { password: string; serverUrl: string; username: string }) {
  const serverUrl = normalizeSpiritFlixServer(input.serverUrl);
  if (!serverUrl) return { ok: false as const, reason: "spiritflix_server_origin_forbidden" };
  if (!input.username.trim() || !input.password) return { ok: false as const, reason: "spiritflix_login_invalid" };
  const response = await fetch(`${serverUrl}/Users/AuthenticateByName`, {
    body: JSON.stringify({ Pw: input.password, Username: input.username.trim() }),
    headers: {
      "Content-Type": "application/json",
      "X-Emby-Authorization": 'MediaBrowser Client="SpiritFlix", Device="SpiritFlix Web", DeviceId="spiritflix-bff", Version="1.0"',
    },
    method: "POST",
  });
  if (!response.ok) return { ok: false as const, reason: "spiritflix_login_rejected" };
  const body = await response.json() as { AccessToken?: string; User?: { Id?: string; Name?: string } };
  if (!body.AccessToken || !body.User?.Id) return { ok: false as const, reason: "spiritflix_login_response_invalid" };
  const id = randomUUID();
  const csrf = randomBytes(32).toString("base64url");
  sessions.set(id, {
    authorization: `MediaBrowser Client="SpiritFlix", Device="SpiritFlix Web", DeviceId="spiritflix-bff", Version="1.0", Token="${body.AccessToken}"`,
    csrf,
    expiresAt: Date.now() + SPIRITFLIX_SESSION_TTL_SECONDS * 1000,
    serverUrl,
    userId: body.User.Id,
    username: body.User.Name || "SpiritFlix user",
  });
  return { ok: true as const, id, session: sessionPublic(sessions.get(id)!) };
}

export function sessionPublic(session: StoredSession) {
  return { csrf: session.csrf, serverUrl: session.serverUrl, userId: SPIRITFLIX_SESSION_USER, username: session.username };
}

export function revokeOrdinarySession(id?: string) {
  if (id) sessions.delete(id);
}

export function resolveMediaSession(input: { e2eId?: string; ordinaryId?: string }): SpiritFlixMediaSession | null {
  const ordinary = resolveOrdinarySession(input.ordinaryId);
  if (ordinary) return { authorization: ordinary.authorization, csrf: ordinary.csrf, kind: "ordinary", serverUrl: ordinary.serverUrl, userId: ordinary.userId };
  const e2e = getE2ESession(input.e2eId);
  return e2e ? { authorization: e2e.authorization, kind: "e2e", serverUrl: e2e.serverUrl, userId: e2e.userId } : null;
}

export function resolveRequestMediaSession(cookies: { get(name: string): { value?: string } | undefined }) {
  return resolveMediaSession({
    e2eId: cookies.get(e2eCookieName())?.value,
    ordinaryId: cookies.get(SPIRITFLIX_SESSION_COOKIE)?.value,
  });
}

export function bindSpiritFlixSessionPath(path: string, session: SpiritFlixMediaSession) {
  return path.replaceAll(SPIRITFLIX_SESSION_USER, session.userId);
}

export function trustedSpiritFlixMutation(request: { headers: Headers; nextUrl: URL }) {
  const origin = request.headers.get("origin");
  const host = request.headers.get("host");
  if (!origin || !host) return false;
  try {
    return new URL(origin).host === host && request.nextUrl.host === host;
  } catch {
    return false;
  }
}

export function trustedSpiritFlixMediaMutation(request: { headers: Headers; nextUrl: URL }, session: SpiritFlixMediaSession | null) {
  return Boolean(session && trustedSpiritFlixMutation(request) && (session.kind !== "ordinary" || request.headers.get("x-spiritflix-csrf") === session.csrf));
}

export function clearSpiritFlixSessionsForTest() {
  sessions.clear();
}
