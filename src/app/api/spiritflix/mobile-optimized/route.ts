import fs from "node:fs";
import fsp from "node:fs/promises";
import { NextRequest, NextResponse } from "next/server";
import {
  findMobileOptimizedReceipt,
  isContainedMobileOutput,
} from "@/lib/spiritflix/mobile-optimized";

export const runtime = "nodejs";

function parseRange(range: string | null, size: number): { start: number; end: number } | null {
  if (!range) return { start: 0, end: size - 1 };
  const match = /^bytes=(\d*)-(\d*)$/.exec(range);
  if (!match) return null;
  const start = match[1] ? Number(match[1]) : 0;
  const end = match[2] ? Number(match[2]) : size - 1;
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start || end >= size) {
    return null;
  }
  return { start, end };
}

function jsonUnavailable(status = 404) {
  return NextResponse.json({ available: false }, { status });
}

export async function GET(request: NextRequest) {
  const searchParams = (request.nextUrl ?? new URL(request.url)).searchParams;
  const itemId = searchParams.get("itemId") ?? undefined;
  const sourcePathSha256 = searchParams.get("sourcePathSha256") ?? undefined;
  const sourcePath = searchParams.get("sourcePath") ?? undefined;
  const key = searchParams.get("key") ?? undefined;
  const stream = searchParams.get("stream") === "1";

  if (!itemId && !sourcePathSha256 && !sourcePath && !key) return jsonUnavailable(400);

  const match = await findMobileOptimizedReceipt({ itemId, sourcePathSha256, sourcePath, key });
  if (!match) return jsonUnavailable();

  const outputPath = match.receipt.outputPath;
  if (!isContainedMobileOutput(outputPath)) return jsonUnavailable(403);

  const stat = await fsp.stat(outputPath).catch(() => null);
  if (!stat?.isFile()) return jsonUnavailable();

  if (!stream) {
    return NextResponse.json({
      available: true,
      mode: "mobile optimized",
      key: match.key,
      url: `/api/spiritflix/mobile-optimized?stream=1&key=${encodeURIComponent(match.key)}`,
      receipt: {
        itemId: match.receipt.itemId,
        sourcePathSha256: match.receipt.sourcePathSha256,
        encoder: match.receipt.encoder,
        profile: match.receipt.profile,
        workerHost: match.receipt.workerHost,
        outputSize: match.receipt.outputSize ?? stat.size,
        percentSaved: match.receipt.percentSaved,
        ffprobe: match.receipt.ffprobe,
      },
    });
  }

  const range = parseRange(request.headers.get("Range"), stat.size);
  if (!range) {
    return new NextResponse(null, {
      status: 416,
      headers: { "Content-Range": `bytes */${stat.size}`, "Accept-Ranges": "bytes" },
    });
  }

  const status = request.headers.has("Range") ? 206 : 200;
  const headers = new Headers({
    "Accept-Ranges": "bytes",
    "Content-Type": "video/mp4",
    "Content-Length": String(range.end - range.start + 1),
    "Cache-Control": "private, max-age=60",
  });
  if (status === 206) headers.set("Content-Range", `bytes ${range.start}-${range.end}/${stat.size}`);

  const body = fs.createReadStream(outputPath, { start: range.start, end: range.end });
  return new NextResponse(body as unknown as BodyInit, { status, headers });
}
