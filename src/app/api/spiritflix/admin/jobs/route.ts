import { NextRequest, NextResponse } from "next/server";
import { listSpiritFlixJobs, readSpiritFlixDeadLetters } from "@/lib/spiritflix/admin/jobs";

export const runtime = "nodejs";

function parseBoolean(value: string | null): boolean {
  return value === "1" || value === "true";
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  try {
    const response = await listSpiritFlixJobs({
      activeOnly: parseBoolean(searchParams.get("activeOnly")),
      videoId: searchParams.get("videoId") ?? undefined,
    });
    const deadLetters = await readSpiritFlixDeadLetters();
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
