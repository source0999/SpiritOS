import { NextRequest, NextResponse } from "next/server";
import { appendYtmcloneEvents } from "@/lib/ytmclone/stats-store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null);
  const events = Array.isArray(body) ? body : Array.isArray(body?.events) ? body.events : body ? [body] : [];

  if (events.length === 0) {
    return NextResponse.json({ ok: false, error: "Expected one event or an events array." }, { status: 400 });
  }

  const result = await appendYtmcloneEvents(events);

  return NextResponse.json({
    ok: true,
    accepted: result.accepted,
    duplicateCount: result.duplicateCount,
    rejected: result.rejected,
    storagePath: result.storagePath,
  });
}
