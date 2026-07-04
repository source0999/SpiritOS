import { NextRequest, NextResponse } from "next/server";
import { listSpiritFlixJobs, readSpiritFlixDeadLetters } from "@/lib/spiritflix/admin/jobs";
import { resolveSpiritFlixAdminPath } from "@/lib/spiritflix/admin/paths";

export const runtime = "nodejs";

function parseBoolean(value: string | null): boolean {
  return value === "1" || value === "true";
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  try {
    const mediaRootParam = searchParams.get("mediaRoot");
    const mediaRoot = mediaRootParam ? (await resolveSpiritFlixAdminPath(mediaRootParam)).realPath : undefined;
    const response = await listSpiritFlixJobs({
      mediaRoot,
      activeOnly: parseBoolean(searchParams.get("activeOnly")),
      videoId: searchParams.get("videoId") ?? undefined,
    });
    const deadLetters = await readSpiritFlixDeadLetters({ mediaRoot });
    return NextResponse.json({ ...response, deadLetters }, {
      headers: {
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix job state read failed." },
      { status: 500 },
    );
  }
}
