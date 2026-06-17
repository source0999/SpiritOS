import fs from "node:fs/promises";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";
import { SPIRITFLIX_MEDIA_ROOT } from "@/lib/spiritflix/admin/constants";
import { getSpiritFlixAdminAllowedRoots, isSpiritFlixAdminPathError, resolveSpiritFlixAdminPath } from "@/lib/spiritflix/admin/paths";
import {
  assertSmartVideoPathCandidate,
  getSmartAnalysisPath,
  isSpiritFlixSmartVideoExtension,
  readSmartAnalysis,
  type SpiritFlixSmartAnalysis,
} from "@/lib/spiritflix/admin/smart";
import { markSpiritFlixSmartAnalysisReviewed, runSpiritFlixSmartReviewPipeline } from "@/lib/spiritflix/admin/smart/review";

export const runtime = "nodejs";

function isSubPath(parent: string, child: string): boolean {
  const relative = path.relative(parent, child);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function resolveSmartMediaRoot(targetPath: string): string {
  const allowedRoots = getSpiritFlixAdminAllowedRoots();
  const match = [...allowedRoots].sort((left, right) => right.length - left.length).find((root) => isSubPath(root, targetPath));
  if (!match) return SPIRITFLIX_MEDIA_ROOT;

  let current = path.resolve(match);
  while (true) {
    if (path.basename(current) === "media") return current;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }

  return match;
}

async function loadVideoAnalysis(videoPath: string, mediaRoot: string): Promise<{
  analysis: SpiritFlixSmartAnalysis | null;
  sidecarPath: string;
}> {
  const stat = await fs.stat(videoPath);
  if (!stat.isFile()) {
    throw new Error("Smart analysis is only available for video files.");
  }

  const extension = path.extname(videoPath).toLowerCase();
  if (!isSpiritFlixSmartVideoExtension(extension)) {
    throw new Error("Smart analysis is only available for supported video files.");
  }

  const validatedPath = assertSmartVideoPathCandidate(videoPath, { mediaRoot });
  const pathInput = {
    videoPath: validatedPath,
    fileSizeBytes: stat.size,
    mtimeMs: stat.mtimeMs,
  };
  const analysis = await readSmartAnalysis(pathInput, { mediaRoot });
  const sidecarPath = getSmartAnalysisPath(pathInput, { mediaRoot });
  return { analysis, sidecarPath };
}

function jsonError(error: unknown, fallbackStatus = 500) {
  if (isSpiritFlixAdminPathError(error)) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Invalid path." }, { status: 400 });
  }
  const message = error instanceof Error ? error.message : "Smart analysis request failed.";
  const status = /only available|folder|video files/i.test(message) ? 400 : fallbackStatus;
  return NextResponse.json({ error: message }, { status });
}

export async function GET(request: NextRequest) {
  const videoPath = new URL(request.url).searchParams.get("path")?.trim() ?? "";
  if (!videoPath) {
    return NextResponse.json({ error: "Missing video path." }, { status: 400 });
  }

  try {
    const { realPath } = await resolveSpiritFlixAdminPath(videoPath);
    const mediaRoot = resolveSmartMediaRoot(realPath);
    const payload = await loadVideoAnalysis(realPath, mediaRoot);
    return NextResponse.json(payload, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return jsonError(error);
  }
}

export async function POST(request: NextRequest) {
  let body: { path?: string; action?: string };
  try {
    body = (await request.json()) as { path?: string; action?: string };
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const videoPath = body.path?.trim() ?? "";
  if (!videoPath) {
    return NextResponse.json({ error: "Missing video path." }, { status: 400 });
  }

  const action = body.action?.trim() || "analyze";

  try {
    const { realPath } = await resolveSpiritFlixAdminPath(videoPath);
    const mediaRoot = resolveSmartMediaRoot(realPath);
    const stat = await fs.stat(realPath);

    if (!stat.isFile()) {
      return NextResponse.json({ error: "Smart analysis only supports a single video file path." }, { status: 400 });
    }

    const extension = path.extname(realPath).toLowerCase();
    if (!isSpiritFlixSmartVideoExtension(extension)) {
      return NextResponse.json({ error: "Smart analysis only supports supported video files." }, { status: 400 });
    }

    assertSmartVideoPathCandidate(realPath, { mediaRoot });

    let analysis: SpiritFlixSmartAnalysis;
    if (action === "markReviewed") {
      analysis = await markSpiritFlixSmartAnalysisReviewed(realPath, { mediaRoot });
    } else if (action === "analyze") {
      analysis = await runSpiritFlixSmartReviewPipeline(realPath, { mediaRoot });
    } else {
      return NextResponse.json({ error: "Unsupported smart analysis action." }, { status: 400 });
    }

    const sidecarPath = getSmartAnalysisPath(
      { videoPath: realPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs },
      { mediaRoot },
    );

    return NextResponse.json({ analysis, sidecarPath }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return jsonError(error);
  }
}
