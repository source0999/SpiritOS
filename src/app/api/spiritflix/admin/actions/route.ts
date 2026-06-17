import { NextRequest, NextResponse } from "next/server";
import { handleSpiritFlixAdminAction, normalizeSpiritFlixAdminActionRequest } from "@/lib/spiritflix/admin/actions";
import type { SpiritFlixAdminActionRequest } from "@/lib/spiritflix/admin/types";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  let payload: SpiritFlixAdminActionRequest;

  try {
    payload = normalizeSpiritFlixAdminActionRequest((await request.json()) as SpiritFlixAdminActionRequest);
  } catch {
    return NextResponse.json({ error: "Invalid SpiritFlix admin action request." }, { status: 400 });
  }

  if (!payload.action || !(payload.mode ?? payload.phase)) {
    return NextResponse.json({ error: "SpiritFlix admin actions require action and mode." }, { status: 400 });
  }

  try {
    const response = await handleSpiritFlixAdminAction(payload);
    return NextResponse.json(response, {
      status: response.allowed ? 200 : 400,
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix admin action failed." },
      { status: 500, headers: { "Cache-Control": "no-store" } },
    );
  }
}
