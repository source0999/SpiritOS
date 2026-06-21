import { NextRequest, NextResponse } from "next/server";
import { isSpiritFlixAdminPathError } from "@/lib/spiritflix/admin/paths";
import { listSpiritFlixAdminDirectory } from "@/lib/spiritflix/admin/fs";
import type { SpiritFlixAdminSortBy, SpiritFlixAdminSortOrder } from "@/lib/spiritflix/admin/types";

export const runtime = "nodejs";

function numberParam(value: string | null): number | undefined {
  if (!value) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export async function GET(request: NextRequest) {
  const url = new URL(request.url);

  try {
    const payload = await listSpiritFlixAdminDirectory({
      path: url.searchParams.get("path") ?? undefined,
      searchTerm: url.searchParams.get("searchTerm") ?? undefined,
      sortBy: (url.searchParams.get("sortBy") as SpiritFlixAdminSortBy | null) ?? "title",
      sortOrder: (url.searchParams.get("sortOrder") as SpiritFlixAdminSortOrder | null) ?? "asc",
      limit: numberParam(url.searchParams.get("limit")),
      startIndex: numberParam(url.searchParams.get("startIndex")),
    });

    return NextResponse.json(payload, {
      headers: {
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    const status = isSpiritFlixAdminPathError(error) ? 400 : 500;
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix admin filesystem listing failed." },
      { status },
    );
  }
}
