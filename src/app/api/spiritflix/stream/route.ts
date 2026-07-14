import { NextRequest, NextResponse } from "next/server";

import { resolveRequestMediaSession } from "@/lib/spiritflix/server-session";

export async function GET(request: NextRequest) {
  if ([...request.nextUrl.searchParams.keys()].some((key) => key !== "audioStreamIndex" && key !== "itemId")) return NextResponse.json({ reason_code: "spiritflix_client_authority_forbidden" }, { status: 400 });
  const session = resolveRequestMediaSession(request.cookies);
  const itemId = request.nextUrl.searchParams.get("itemId") ?? "";
  const audioStreamIndex = request.nextUrl.searchParams.get("audioStreamIndex");
  if (!session) return NextResponse.json({ reason_code: "spiritflix_session_missing" }, { status: 401 });
  if (!/^[a-fA-F0-9-]+$/.test(itemId) || (audioStreamIndex && !/^\d+$/.test(audioStreamIndex))) return NextResponse.json({ reason_code: "spiritflix_stream_invalid" }, { status: 400 });
  const upstream = new URL(`/Videos/${itemId}/Stream`, session.serverUrl);
  upstream.searchParams.set("Static", "true");
  upstream.searchParams.set("PlaySessionId", `spiritflix-${itemId}`);
  if (audioStreamIndex) upstream.searchParams.set("AudioStreamIndex", audioStreamIndex);
  const headers: HeadersInit = { "X-Emby-Authorization": session.authorization };
  const range = request.headers.get("Range"); if (range) headers.Range = range;
  const response = await fetch(upstream, { headers });
  if (!response.body) return NextResponse.json({ reason_code: "spiritflix_stream_unavailable" }, { status: response.status });
  const passthrough = new Headers(); for (const name of ["Content-Type", "Content-Length", "Content-Range", "Accept-Ranges", "Cache-Control"]) { const value = response.headers.get(name); if (value) passthrough.set(name, value); }
  return new NextResponse(response.body, { headers: passthrough, status: response.status });
}
