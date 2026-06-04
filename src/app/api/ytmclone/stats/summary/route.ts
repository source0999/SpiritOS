import { NextResponse } from "next/server";
import { buildYtmcloneSummary } from "@/lib/ytmclone/stats-store";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const summary = await buildYtmcloneSummary();
  return NextResponse.json({ ok: true, ...summary });
}
