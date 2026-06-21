import { NextRequest, NextResponse } from "next/server";
import { findSpiritFlixManualTaggedItems } from "@/lib/spiritflix/manual-tags";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const tag = request.nextUrl.searchParams.get("tag");
  if (!tag) {
    return NextResponse.json({ error: "Tag filter is required." }, { status: 400 });
  }

  try {
    const items = await findSpiritFlixManualTaggedItems(tag);
    return NextResponse.json(
      {
        schema: "spiritflix-manual-library-filter/v1",
        tag: tag.trim().replace(/\s+/g, " ").toLowerCase(),
        itemIds: items.map((item) => item.itemId),
        items,
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix manual library filter failed." },
      { status: 400 },
    );
  }
}
