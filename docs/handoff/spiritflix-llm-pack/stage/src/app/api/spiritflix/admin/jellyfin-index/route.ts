import { NextResponse } from "next/server";
import { getServerJellyfinCredentials, listServerJellyfinVideoItems, resolveServerJellyfinUserId } from "@/lib/spiritflix/admin/jellyfin-server";

export const runtime = "nodejs";

export async function GET() {
  const credentials = getServerJellyfinCredentials();
  if (!credentials) {
    return NextResponse.json({ items: [], source: "unconfigured" }, { headers: { "Cache-Control": "no-store" } });
  }

  try {
    const userId = await resolveServerJellyfinUserId(credentials);
    const items = await listServerJellyfinVideoItems(credentials, userId);
    return NextResponse.json(
      {
        schema: "spiritflix-admin-jellyfin-index/v1",
        generatedAt: new Date().toISOString(),
        source: "server",
        itemCount: items.length,
        items,
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix admin Jellyfin index failed.", items: [], source: "failed" },
      { status: 500, headers: { "Cache-Control": "no-store" } },
    );
  }
}
