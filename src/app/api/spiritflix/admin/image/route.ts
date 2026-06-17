import { NextRequest, NextResponse } from "next/server";
import { getServerJellyfinCredentials, jellyfinImagePath } from "@/lib/spiritflix/admin/jellyfin-server";

export const runtime = "nodejs";

const allowedTypes = new Set(["Primary", "Thumb", "Backdrop"]);

export async function GET(request: NextRequest) {
  const credentials = getServerJellyfinCredentials();
  if (!credentials) {
    return NextResponse.json({ error: "SpiritFlix admin image proxy is not configured." }, { status: 503 });
  }

  const itemId = request.nextUrl.searchParams.get("itemId") ?? "";
  const imageType = request.nextUrl.searchParams.get("type") ?? "Primary";
  const tag = request.nextUrl.searchParams.get("tag") ?? undefined;
  const width = Number(request.nextUrl.searchParams.get("width") ?? "360");

  if (!itemId || !allowedTypes.has(imageType)) {
    return NextResponse.json({ error: "Invalid SpiritFlix admin image request." }, { status: 400 });
  }

  const path = jellyfinImagePath(itemId, imageType as "Primary" | "Thumb" | "Backdrop", tag, Number.isFinite(width) ? width : 360);
  const response = await fetch(`${credentials.serverUrl}${path}`, {
    headers: {
      "X-Emby-Token": credentials.accessToken,
    },
    cache: "no-store",
  });

  if (!response.ok || !response.body) {
    return NextResponse.json({ error: "Image unavailable." }, { status: response.status });
  }

  return new NextResponse(response.body, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "image/jpeg",
      "Cache-Control": "private, max-age=300",
    },
  });
}
