import "server-only";
import { createHash, randomUUID } from "node:crypto";
import { existsSync, readFileSync, statSync } from "node:fs";

type Secret = { source: "environment" | "secret_file"; values: Record<string, string | undefined> } | { reason: string };
type Session = { expiresAt: number; serverUrl: string; userId: string; username: string; authorization: string };
type Failed = { ok: false; reason: string };
type Created = { ok: true; id: string; serverUrl: string; userId: string; username: string; maxAgeSeconds: number; source: "environment" | "secret_file" };

const COOKIE_NAME = "spiritflix_e2e_session";
const DEFAULT_SECRET_FILE = "/home/source/.config/spiritos/secrets/spiritflix-e2e.env";
const MAX_AGE_MS = 15 * 60_000;
const sessions = new Map<string, Session>();

function parseEnv(text: string): Record<string, string> {
  return Object.fromEntries(text.split(/\r?\n/).map((line: string) => line.trim()).filter((line: string) => line && !line.startsWith("#")).map((line: string) => {
    const index = line.indexOf("=");
    return index < 0 ? [line, ""] : [line.slice(0, index).trim(), line.slice(index + 1).trim()];
  }));
}

function readSecret(): Secret {
  const secretFile = process.env.SPIRITFLIX_E2E_SECRET_FILE || DEFAULT_SECRET_FILE;
  if (process.env.SPIRITFLIX_E2E_USERNAME && process.env.SPIRITFLIX_E2E_PASSWORD) return { source: "environment", values: process.env };
  if (!existsSync(secretFile)) return { reason: "dedicated_e2e_secret_not_configured" };
  if ((statSync(secretFile).mode & 0o077) !== 0) return { reason: "secret_file_permissions_too_open" };
  return { source: "secret_file", values: parseEnv(readFileSync(secretFile, "utf8")) };
}

export function e2eCookieName() { return COOKIE_NAME; }
export function getE2ESession(id?: string): Session | null {
  const session = id ? sessions.get(id) : undefined;
  if (!session || session.expiresAt <= Date.now()) { if (id) sessions.delete(id); return null; }
  return session;
}

export async function createE2ESession(): Promise<Failed | Created> {
  if (process.env.SPIRITFLIX_E2E_SESSION_ENABLED !== "true") return { ok: false, reason: "e2e_session_mode_disabled" };
  const secret = readSecret();
  if (!("values" in secret)) return { ok: false, reason: secret.reason };
  const username = secret.values.SPIRITFLIX_E2E_USERNAME?.trim();
  const password = secret.values.SPIRITFLIX_E2E_PASSWORD;
  const serverUrl = (secret.values.SPIRITFLIX_E2E_SERVER_URL || "http://127.0.0.1:8096").replace(/\/+$/, "");
  if (!username || !password) return { ok: false, reason: "dedicated_e2e_secret_not_configured" };
  const response = await fetch(serverUrl + "/Users/AuthenticateByName", { method: "POST", headers: { "Content-Type": "application/json", "X-Emby-Authorization": 'MediaBrowser Client="SpiritOS E2E", Device="Campaign 1", DeviceId="spiritos-campaign-1-e2e", Version="1.0"' }, body: JSON.stringify({ Username: username, Pw: password }) });
  if (!response.ok) return { ok: false, reason: "dedicated_e2e_authentication_rejected" };
  const auth = await response.json() as { AccessToken?: string; User?: { Id?: string; Name?: string; Policy?: { IsAdministrator?: boolean } } };
  if (!auth.AccessToken || !auth.User?.Id || auth.User.Policy?.IsAdministrator === true) return { ok: false, reason: "dedicated_e2e_identity_not_least_privileged" };
  const id = randomUUID();
  sessions.set(id, { expiresAt: Date.now() + MAX_AGE_MS, serverUrl, userId: auth.User.Id, username: auth.User.Name || createHash("sha256").update(username).digest("hex").slice(0, 12), authorization: 'MediaBrowser Client="SpiritOS E2E", Device="Campaign 1", DeviceId="spiritos-campaign-1-e2e", Version="1.0", Token="' + auth.AccessToken + '"' });
  return { ok: true, id, serverUrl, userId: auth.User.Id, username: auth.User.Name || "spiritos-e2e", maxAgeSeconds: MAX_AGE_MS / 1000, source: secret.source };
}

export function clearE2ESessionsForTest() { sessions.clear(); }
