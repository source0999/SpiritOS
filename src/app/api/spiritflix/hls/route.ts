import { NextRequest, NextResponse } from "next/server";
import { normalizeJellyfinServerUrl } from "@/lib/spiritflix-jellyfin-client";

const allowedHosts = new Set([
  "10.0.0.186:8096",
  "spirit.tailb69ea6.ts.net:8096",
  "100.111.32.31:8096",
  "127.0.0.1:8096",
  "localhost:8096",
]);

function isAllowedServer(serverUrl: string): boolean {
  try {
    const parsed = new URL(serverUrl);
    return (parsed.protocol === "http:" || parsed.protocol === "https:") && allowedHosts.has(parsed.host);
  } catch {
    return false;
  }
}

function isAllowedPath(path: string): boolean {
  return path.startsWith("/") && !path.startsWith("//") && !path.includes("://");
}

function proxyPath(serverUrl: string, token: string, path: string): string {
  const params = new URLSearchParams({
    serverUrl,
    token,
    path,
  });
  return `/api/spiritflix/hls?${params.toString()}`;
}

function rewritePlaylist(body: string, serverUrl: string, token: string, basePath: string): string {
  const base = new URL(basePath, "http://spiritflix.local");
  return body
    .split("\n")
    .map((line) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) return line;
      const resolved = new URL(trimmed, base);
      return proxyPath(serverUrl, token, `${resolved.pathname}${resolved.search}`);
    })
    .join("\n");
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const serverUrl = normalizeJellyfinServerUrl(searchParams.get("serverUrl") ?? "");
  const token = searchParams.get("token") ?? "";
  const path = searchParams.get("path") ?? "";

  if (!isAllowedServer(serverUrl) || !token || !isAllowedPath(path)) {
    return NextResponse.json({ error: "Invalid HLS request." }, { status: 400 });
  }

  const upstream = new URL(path, serverUrl);
  if (!upstream.searchParams.has("api_key")) upstream.searchParams.set("api_key", token);

  const headers: HeadersInit = {};
  const range = request.headers.get("Range");
  if (range) headers.Range = range;

  const response = await fetch(upstream, { headers });
  if (!response.body) {
    return NextResponse.json({ error: "HLS stream unavailable." }, { status: response.status });
  }

  const contentType = response.headers.get("Content-Type") ?? "";
  if (contentType.includes("mpegurl") || upstream.pathname.endsWith(".m3u8")) {
    const rewritten = rewritePlaylist(await response.text(), serverUrl, token, `${upstream.pathname}${upstream.search}`);
    return new NextResponse(rewritten, {
      status: response.status,
      headers: {
        "Content-Type": contentType || "application/vnd.apple.mpegurl",
        "Cache-Control": "private, max-age=10",
      },
    });
  }

  const passthrough = new Headers();
  [
    "Content-Type",
    "Content-Length",
    "Content-Range",
    "Accept-Ranges",
    "Cache-Control",
  ].forEach((header) => {
    const value = response.headers.get(header);
    if (value) passthrough.set(header, value);
  });

  return new NextResponse(response.body, {
    status: response.status,
    headers: passthrough,
  });
}
