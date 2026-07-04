import { NextRequest, NextResponse } from "next/server";
import { normalizeJellyfinServerUrl } from "@/lib/spiritflix-jellyfin-client";

const allowedHosts = new Set([
  "spirit.tailb69ea6.ts.net:8096",
  "100.111.32.31:8096",
  "127.0.0.1:8096",
  "localhost:8096",
]);
const JELLYFIN_LOCAL_ORIGIN = "http://127.0.0.1:8096";
const JELLYFIN_PROXY_TIMEOUT_MS = 8000;

interface ProxyBody {
  serverUrl?: string;
  path?: string;
  method?: string;
  body?: unknown;
  authorization?: string;
}

function isAllowedServer(serverUrl: string): boolean {
  try {
    const parsed = new URL(serverUrl);
    return (parsed.protocol === "http:" || parsed.protocol === "https:") && allowedHosts.has(parsed.host);
  } catch {
    return false;
  }
}

function getProxyOrigin(serverUrl: string): string {
  const parsed = new URL(serverUrl);
  if (allowedHosts.has(parsed.host) && parsed.port === "8096") return JELLYFIN_LOCAL_ORIGIN;
  return parsed.origin;
}

export async function POST(request: NextRequest) {
  let payload: ProxyBody;
  try {
    payload = (await request.json()) as ProxyBody;
  } catch {
    return NextResponse.json({ error: "Invalid proxy request." }, { status: 400 });
  }

  const serverUrl = normalizeJellyfinServerUrl(payload.serverUrl ?? "");
  const path = payload.path ?? "";
  const method = (payload.method ?? "GET").toUpperCase();

  if (!isAllowedServer(serverUrl)) {
    return NextResponse.json({ error: "That Jellyfin server is not allowed for SpiritFlix." }, { status: 400 });
  }

  if (!path.startsWith("/") || path.startsWith("//") || path.includes("://")) {
    return NextResponse.json({ error: "Invalid Jellyfin API path." }, { status: 400 });
  }

  if (!["DELETE", "GET", "POST"].includes(method)) {
    return NextResponse.json({ error: "Unsupported Jellyfin API method." }, { status: 405 });
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), JELLYFIN_PROXY_TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(`${getProxyOrigin(serverUrl)}${path}`, {
      method,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(payload.authorization ? { "X-Emby-Authorization": payload.authorization } : {}),
      },
      body: method === "POST" ? JSON.stringify(payload.body ?? {}) : undefined,
    });
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === "AbortError";
    return NextResponse.json(
      { error: timedOut ? "Jellyfin request timed out." : "Jellyfin proxy request failed." },
      { status: timedOut ? 504 : 502 },
    );
  } finally {
    clearTimeout(timeout);
  }

  if (response.status === 204) {
    return new NextResponse(null, {
      status: 204,
      headers: {
        "Content-Type": response.headers.get("Content-Type") ?? "application/json",
      },
    });
  }

  const text = await response.text();
  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
    },
  });
}
