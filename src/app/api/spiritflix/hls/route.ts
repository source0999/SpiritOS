import { NextRequest, NextResponse } from "next/server";

import { isAllowedSpiritFlixPath, resolveRequestMediaSession } from "@/lib/spiritflix/server-session";

function proxyPath(path: string) { return `/api/spiritflix/hls?${new URLSearchParams({ path }).toString()}`; }
function rewritePlaylist(body: string, basePath: string) {
  const base = new URL(basePath, "http://spiritflix.local");
  return body.split("\n").map((line) => { const trimmed = line.trim(); if (!trimmed || trimmed.startsWith("#")) return line; const resolved = new URL(trimmed, base); return proxyPath(`${resolved.pathname}${resolved.search}`); }).join("\n");
}

export async function GET(request: NextRequest) {
  if ([...request.nextUrl.searchParams.keys()].some((key) => key !== "path")) return NextResponse.json({ reason_code: "spiritflix_client_authority_forbidden" }, { status: 400 });
  const session = resolveRequestMediaSession(request.cookies);
  const path = request.nextUrl.searchParams.get("path") ?? "";
  if (!session) return NextResponse.json({ reason_code: "spiritflix_session_missing" }, { status: 401 });
  if (!isAllowedSpiritFlixPath(path)) return NextResponse.json({ reason_code: "spiritflix_hls_invalid" }, { status: 400 });
  const upstream = new URL(path, session.serverUrl);
  const headers: HeadersInit = { "X-Emby-Authorization": session.authorization };
  const range = request.headers.get("Range"); if (range) headers.Range = range;
  const response = await fetch(upstream, { headers });
  if (!response.body) return NextResponse.json({ reason_code: "spiritflix_hls_unavailable" }, { status: response.status });
  const contentType = response.headers.get("Content-Type") ?? "";
  if (contentType.includes("mpegurl") || upstream.pathname.endsWith(".m3u8")) return new NextResponse(rewritePlaylist(await response.text(), `${upstream.pathname}${upstream.search}`), { headers: { "Cache-Control": "private, max-age=10", "Content-Type": contentType || "application/vnd.apple.mpegurl" }, status: response.status });
  const passthrough = new Headers(); for (const name of ["Content-Type", "Content-Length", "Content-Range", "Accept-Ranges", "Cache-Control"]) { const value = response.headers.get(name); if (value) passthrough.set(name, value); }
  return new NextResponse(response.body, { headers: passthrough, status: response.status });
}
