import { NextRequest, NextResponse } from "next/server";
import { normalizeJellyfinServerUrl } from "@/lib/spiritflix/jellyfin-client";

const allowedHosts = new Set([
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

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const serverUrl = normalizeJellyfinServerUrl(searchParams.get("serverUrl") ?? "");
  const itemId = searchParams.get("itemId") ?? "";
  const token = searchParams.get("token") ?? "";

  if (!isAllowedServer(serverUrl) || !/^[a-fA-F0-9-]+$/.test(itemId) || !token) {
    return NextResponse.json({ error: "Invalid stream request." }, { status: 400 });
  }

  const upstream = new URL(`${serverUrl}/Videos/${itemId}/Stream`);
  upstream.searchParams.set("Static", "true");
  upstream.searchParams.set("api_key", token);
  upstream.searchParams.set("PlaySessionId", `spiritflix-${itemId}`);

  const headers: HeadersInit = {};
  const range = request.headers.get("Range");
  if (range) headers.Range = range;

  const response = await fetch(upstream, { headers });
  if (!response.body) {
    return NextResponse.json({ error: "Stream unavailable." }, { status: response.status });
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
