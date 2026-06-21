import fs from "node:fs/promises";
import { NextRequest, NextResponse } from "next/server";
import { isSpiritFlixAdminPathError } from "@/lib/spiritflix/admin/paths";
import { getOrGenerateAdminVideoThumbnail } from "@/lib/spiritflix/admin/thumbnail";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const videoPath = new URL(request.url).searchParams.get("path")?.trim() ?? "";
  if (!videoPath) {
    return NextResponse.json({ error: "Missing video path." }, { status: 400 });
  }

  try {
    const result = await getOrGenerateAdminVideoThumbnail(videoPath);
    if (!result) {
      return NextResponse.json({ error: "Thumbnail unavailable." }, { status: 404 });
    }

    const image = await fs.readFile(result.cachePath);
    return new NextResponse(image, {
      status: 200,
      headers: {
        "Content-Type": "image/jpeg",
        "Cache-Control": "private, max-age=86400",
        "X-SpiritFlix-Thumbnail-Key": result.cacheKey,
      },
    });
  } catch (error) {
    if (isSpiritFlixAdminPathError(error)) {
      return NextResponse.json({ error: error instanceof Error ? error.message : "Invalid path." }, { status: 400 });
    }
    return NextResponse.json({ error: "Thumbnail generation failed." }, { status: 500 });
  }
}
