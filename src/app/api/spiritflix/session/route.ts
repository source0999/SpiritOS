import { NextRequest, NextResponse } from "next/server";

import {
  createOrdinarySession,
  revokeOrdinarySession,
  resolveOrdinarySession,
  sessionPublic,
  SPIRITFLIX_SESSION_COOKIE,
  SPIRITFLIX_SESSION_TTL_SECONDS,
  trustedSpiritFlixMutation,
} from "@/lib/spiritflix/server-session";

export const runtime = "nodejs";

function noStore(body: Record<string, unknown>, status: number) {
  return NextResponse.json(body, { headers: { "Cache-Control": "no-store" }, status });
}

function sessionCookie(request: NextRequest, value: string) {
  return {
    httpOnly: true,
    maxAge: SPIRITFLIX_SESSION_TTL_SECONDS,
    path: "/api/spiritflix",
    name: SPIRITFLIX_SESSION_COOKIE,
    sameSite: "strict" as const,
    secure: request.nextUrl.protocol === "https:",
    value,
  };
}

export async function GET(request: NextRequest) {
  const session = resolveOrdinarySession(request.cookies.get(SPIRITFLIX_SESSION_COOKIE)?.value);
  return session ? noStore({ authenticated: true, session: sessionPublic(session) }, 200) : noStore({ authenticated: false, reason_code: "spiritflix_session_missing" }, 401);
}

export async function POST(request: NextRequest) {
  if (!trustedSpiritFlixMutation(request)) return noStore({ reason_code: "spiritflix_origin_untrusted" }, 403);
  let body: { password?: unknown; serverUrl?: unknown; username?: unknown };
  try { body = await request.json(); } catch { return noStore({ reason_code: "spiritflix_login_invalid" }, 400); }
  if (Object.keys(body).some((key) => !["password", "serverUrl", "username"].includes(key)) || typeof body.username !== "string" || typeof body.password !== "string" || typeof body.serverUrl !== "string") return noStore({ reason_code: "spiritflix_login_invalid" }, 400);
  const created = await createOrdinarySession({ password: body.password, serverUrl: body.serverUrl, username: body.username });
  if (!created.ok) return noStore({ reason_code: created.reason }, 403);
  const response = noStore({ authenticated: true, session: created.session }, 200);
  response.cookies.set(sessionCookie(request, created.id));
  return response;
}

export async function DELETE(request: NextRequest) {
  if (!trustedSpiritFlixMutation(request)) return noStore({ reason_code: "spiritflix_origin_untrusted" }, 403);
  const id = request.cookies.get(SPIRITFLIX_SESSION_COOKIE)?.value;
  const session = resolveOrdinarySession(id);
  if (!session) return noStore({ reason_code: "spiritflix_session_missing" }, 401);
  if (request.headers.get("x-spiritflix-csrf") !== session.csrf) return noStore({ reason_code: "spiritflix_csrf_invalid" }, 403);
  revokeOrdinarySession(id);
  const response = noStore({ revoked: true }, 200);
  response.cookies.set({ ...sessionCookie(request, ""), maxAge: 0 });
  return response;
}
