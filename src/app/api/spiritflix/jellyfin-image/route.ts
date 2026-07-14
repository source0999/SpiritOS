import { NextRequest, NextResponse } from "next/server";

import { bindSpiritFlixSessionPath, isAllowedSpiritFlixPath, resolveRequestMediaSession } from "@/lib/spiritflix/server-session";

async function proxyImage(request: NextRequest, path: string) {
  const session = resolveRequestMediaSession(request.cookies);
  if (!session) return NextResponse.json({ reason_code: "spiritflix_session_missing" }, { status: 401 });
  if (!isAllowedSpiritFlixPath(path)) return NextResponse.json({ reason_code: "spiritflix_image_invalid" }, { status: 400 });
  const response = await fetch(`${session.serverUrl}${bindSpiritFlixSessionPath(path, session)}`, { headers: { "X-Emby-Authorization": session.authorization } });
  if (!response.ok || !response.body) return NextResponse.json({ reason_code: "spiritflix_image_unavailable" }, { status: response.status });
  return new NextResponse(response.body, { headers: { "Cache-Control": "private, max-age=900, stale-while-revalidate=3600", "Content-Type": response.headers.get("Content-Type") ?? "image/jpeg" }, status: response.status });
}

export async function GET(request: NextRequest) {
  if ([...request.nextUrl.searchParams.keys()].some((key) => key !== "path")) return NextResponse.json({ reason_code: "spiritflix_client_authority_forbidden" }, { status: 400 });
  return proxyImage(request, request.nextUrl.searchParams.get("path") ?? "");
}

export async function POST(request: NextRequest) {
  let payload: { path?: unknown };
  try { payload = await request.json(); } catch { return NextResponse.json({ reason_code: "spiritflix_image_invalid" }, { status: 400 }); }
  if (Object.keys(payload).some((key) => key !== "path") || typeof payload.path !== "string") return NextResponse.json({ reason_code: "spiritflix_client_authority_forbidden" }, { status: 400 });
  return proxyImage(request, payload.path);
}
