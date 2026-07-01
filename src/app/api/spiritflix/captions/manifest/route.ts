import { NextRequest, NextResponse } from "next/server";
import { getSpiritFlixCaptionManifestResponse } from "@/lib/spiritflix/captions";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const searchParams = (request.nextUrl ?? new URL(request.url)).searchParams;
  const manifest = await getSpiritFlixCaptionManifestResponse({
    key: searchParams.get("key"),
    mediaPath: searchParams.get("mediaPath"),
    sourcePath: searchParams.get("sourcePath"),
  });

  return NextResponse.json(manifest, {
    headers: {
      "Cache-Control": "private, max-age=30",
    },
  });
}
