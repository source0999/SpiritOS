import { NextRequest, NextResponse } from "next/server";
import { listJellyfinAdminItems } from "@/lib/spiritflix/admin/jellyfin-admin";
import type { SpiritFlixAdminLibraryRequest } from "@/lib/spiritflix/admin/types";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  let payload: SpiritFlixAdminLibraryRequest;

  try {
    payload = (await request.json()) as SpiritFlixAdminLibraryRequest;
  } catch {
    return NextResponse.json({ error: "Invalid SpiritFlix admin library request." }, { status: 400 });
  }

  try {
    const response = await listJellyfinAdminItems(payload);
    return NextResponse.json(response, {
      headers: {
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix admin library listing failed." },
      { status: 400 },
    );
  }
}
