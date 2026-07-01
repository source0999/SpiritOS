import fs from "node:fs";
import { NextRequest, NextResponse } from "next/server";
import { resolveCaptionFilePath } from "@/lib/spiritflix/captions";

export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const searchParams = (request.nextUrl ?? new URL(request.url)).searchParams;
  const key = searchParams.get("key") ?? "";
  const track = searchParams.get("track") ?? "";
  const captionPath = await resolveCaptionFilePath(key, track);
  if (!captionPath) {
    return NextResponse.json({ error: "Caption file not found." }, { status: 404 });
  }

  const body = fs.createReadStream(captionPath);
  return new NextResponse(body as unknown as BodyInit, {
    status: 200,
    headers: {
      "Content-Type": "text/vtt; charset=utf-8",
      "Cache-Control": "private, max-age=300",
    },
  });
}
