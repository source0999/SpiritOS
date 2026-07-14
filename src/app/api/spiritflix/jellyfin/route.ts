import { NextRequest, NextResponse } from "next/server";

import {
  bindSpiritFlixSessionPath,
  isAllowedSpiritFlixPath,
  resolveRequestMediaSession,
  trustedSpiritFlixMediaMutation,
} from "@/lib/spiritflix/server-session";

const JELLYFIN_LOCAL_ORIGIN = "http://127.0.0.1:8096";
const JELLYFIN_PROXY_TIMEOUT_MS = 8000;
type ProxyBody = { body?: unknown; method?: unknown; path?: unknown };

export async function POST(request: NextRequest) {
  let payload: ProxyBody;
  try { payload = await request.json(); } catch { return NextResponse.json({ reason_code: "spiritflix_request_invalid" }, { status: 400 }); }
  if (Object.keys(payload).some((key) => !["body", "method", "path"].includes(key)) || typeof payload.path !== "string" || (payload.method !== undefined && typeof payload.method !== "string")) return NextResponse.json({ reason_code: "spiritflix_client_authority_forbidden" }, { status: 400 });
  const method = (payload.method ?? "GET").toUpperCase();
  if (!isAllowedSpiritFlixPath(payload.path) || !["DELETE", "GET", "POST"].includes(method)) return NextResponse.json({ reason_code: "spiritflix_request_invalid" }, { status: 400 });
  const session = resolveRequestMediaSession(request.cookies);
  const publicInfo = method === "GET" && payload.path === "/System/Info/Public";
  if (!session && !publicInfo) return NextResponse.json({ reason_code: "spiritflix_session_missing" }, { status: 401 });
  if (method !== "GET" && !trustedSpiritFlixMediaMutation(request, session)) return NextResponse.json({ reason_code: "spiritflix_mutation_untrusted" }, { status: 403 });
  const path = session ? bindSpiritFlixSessionPath(payload.path, session) : payload.path;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), JELLYFIN_PROXY_TIMEOUT_MS);
  try {
    const response = await fetch(`${JELLYFIN_LOCAL_ORIGIN}${path}`, {
      body: method === "POST" ? JSON.stringify(payload.body ?? {}) : undefined,
      headers: { Accept: "application/json", "Content-Type": "application/json", ...(session ? { "X-Emby-Authorization": session.authorization } : {}) },
      method,
      signal: controller.signal,
    });
    if (response.status === 204) return new NextResponse(null, { status: 204 });
    return new NextResponse(await response.text(), { headers: { "Content-Type": response.headers.get("Content-Type") ?? "application/json" }, status: response.status });
  } catch (error) {
    return NextResponse.json({ reason_code: error instanceof DOMException && error.name === "AbortError" ? "spiritflix_upstream_timeout" : "spiritflix_upstream_failed" }, { status: error instanceof DOMException && error.name === "AbortError" ? 504 : 502 });
  } finally { clearTimeout(timeout); }
}
