import { NextRequest, NextResponse } from "next/server";
import {
  getSpiritFlixManualModelIndex,
  listSpiritFlixManualModelRecords,
} from "@/lib/spiritflix/manual-models";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const includeItems = request.nextUrl.searchParams.get("includeItems") === "1";

  try {
    const index = await getSpiritFlixManualModelIndex();
    return NextResponse.json(
      {
        ...index,
        items: includeItems ? await listSpiritFlixManualModelRecords() : undefined,
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix manual model index failed." },
      { status: 500 },
    );
  }
}
