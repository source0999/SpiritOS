import { NextRequest, NextResponse } from "next/server";
import { createE2ESession, e2eCookieName } from "@/lib/spiritflix/e2e-session";
export const runtime = "nodejs";
export async function POST(_request: NextRequest) {
  const session = await createE2ESession();
  if (!session.ok) return NextResponse.json({ ready: false, reason: session.reason }, { status: 403, headers: { "Cache-Control": "no-store" } });
  const response = NextResponse.json({ ready: true, session: { serverUrl: session.serverUrl, userId: session.userId, username: session.username, accessToken: "e2e-broker" } }, { headers: { "Cache-Control": "no-store" } });
  response.cookies.set(e2eCookieName(), session.id, { httpOnly: true, sameSite: "strict", secure: true, maxAge: session.maxAgeSeconds, path: "/api/spiritflix" });
  return response;
}
