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

async function proxyImage(payload: {
    serverUrl?: string;
    path?: string;
    authorization?: string;
    token?: string;
  }) {
  const serverUrl = normalizeJellyfinServerUrl(payload.serverUrl ?? "");
  const path = payload.path ?? "";

  if (!isAllowedServer(serverUrl) || !path.startsWith("/") || path.startsWith("//") || path.includes("://")) {
    return NextResponse.json({ error: "Invalid image request." }, { status: 400 });
  }

  const response = await fetch(`${serverUrl}${path}`, {
    headers: {
      ...(payload.authorization ? { "X-Emby-Authorization": payload.authorization } : {}),
      ...(payload.token ? { "X-Emby-Token": payload.token } : {}),
    },
  });

  if (!response.ok || !response.body) {
    return NextResponse.json({ error: "Image unavailable." }, { status: response.status });
  }

  return new NextResponse(response.body, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "image/jpeg",
      "Cache-Control": "private, max-age=900, stale-while-revalidate=3600",
    },
  });
}

export async function GET(request: NextRequest) {
  return proxyImage({
    serverUrl: request.nextUrl.searchParams.get("serverUrl") ?? undefined,
    path: request.nextUrl.searchParams.get("path") ?? undefined,
    token: request.nextUrl.searchParams.get("token") ?? undefined,
  });
}

export async function POST(request: NextRequest) {
  const payload = (await request.json()) as {
    serverUrl?: string;
    path?: string;
    authorization?: string;
  };
  return proxyImage(payload);
}
