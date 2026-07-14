import fs from "node:fs/promises";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";
import { spiritFlixAdminMutationDenied } from "@/lib/spiritflix/admin-authority";
import { SPIRITFLIX_MEDIA_ROOT } from "@/lib/spiritflix/admin/constants";
import { getSpiritFlixAdminAllowedRoots, isSpiritFlixAdminPathError, resolveSpiritFlixAdminPath } from "@/lib/spiritflix/admin/paths";
import {
  assertSmartVideoPathCandidate,
  buildSmartRenamePreviewDraft,
  getSmartAnalysisPath,
  isSpiritFlixSmartVideoExtension,
  projectApprovedSmartMetadata,
  readSmartAnalysis,
  type SpiritFlixSmartAnalysis,
  writeApprovedSmartMetadataSidecar,
} from "@/lib/spiritflix/admin/smart";
import { markSpiritFlixSmartAnalysisReviewed, runSpiritFlixSmartReviewPipeline, saveSpiritFlixSmartAnalysisReview } from "@/lib/spiritflix/admin/smart/review";
import { assertSpiritFlixSmartReviewPayload } from "@/lib/spiritflix/admin/smart/review-metadata";

const FORBIDDEN_EXECUTE_ACTIONS = new Set([
  "applyRename",
  "applyMove",
  "executeRename",
  "executeMove",
]);

export const runtime = "nodejs";

export async function POST(_request: NextRequest) {
  return NextResponse.json(spiritFlixAdminMutationDenied(), { status: 410 });
}

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
  const status = /only available|folder|video files|unknown field|known tag|review|overlap|must be|not in suggestedTags|too large/i.test(message)
    ? 400
    : fallbackStatus;
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

async function legacyPOST(request: NextRequest) {
  let body: { path?: string; action?: string; review?: unknown };
  try {
    body = (await request.json()) as { path?: string; action?: string; review?: unknown };
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

    // S6: reject all execute actions outright
    if (FORBIDDEN_EXECUTE_ACTIONS.has(action)) {
      return NextResponse.json(
        { error: `${action} is not available in smart tagging. File mutations require Level 2 preview → confirm.` },
        { status: 400 },
      );
    }

    let analysis: SpiritFlixSmartAnalysis;
    if (action === "markReviewed") {
      analysis = await markSpiritFlixSmartAnalysisReviewed(realPath, { mediaRoot });
    } else if (action === "saveReview") {
      const review = assertSpiritFlixSmartReviewPayload(
        body.review ?? { approvedTagIds: [], rejectedTagIds: [] },
      );
      analysis = await saveSpiritFlixSmartAnalysisReview(realPath, review, { mediaRoot });
    } else if (action === "analyze") {
      analysis = await runSpiritFlixSmartReviewPipeline(realPath, { mediaRoot });
    } else if (action === "exportMetadata" || action === "confirmMetadata") {
      // S9: confirm approved metadata to admin metadata sidecar only
      const pathInput = { videoPath: realPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs };
      const loaded = await readSmartAnalysis(pathInput, { mediaRoot });
      if (!loaded) {
        return NextResponse.json({ error: "No smart analysis found for this video. Run analyze first." }, { status: 400 });
      }
      if (!loaded.reviewedMetadata || loaded.reviewedMetadata.reviewStatus === "unreviewed") {
        return NextResponse.json({ error: "Analysis must be reviewed before exporting metadata." }, { status: 400 });
      }
      const result = await writeApprovedSmartMetadataSidecar(loaded, { mediaRoot });
      const projection = projectApprovedSmartMetadata(loaded);
      return NextResponse.json({
        metadataPath: result.path,
        metadata: projection,
        confirmed: true,
      }, { headers: { "Cache-Control": "no-store" } });
    } else if (action === "prepareRenamePreview") {
      // S6: build rename preview draft — no execute, no Level 2 call
      const pathInput = { videoPath: realPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs };
      const loaded = await readSmartAnalysis(pathInput, { mediaRoot });
      if (!loaded) {
        return NextResponse.json({ error: "No smart analysis found for this video. Run analyze first." }, { status: 400 });
      }
      if (!loaded.reviewedMetadata || loaded.reviewedMetadata.reviewStatus === "unreviewed") {
        return NextResponse.json({ error: "Analysis must be reviewed before preparing rename preview." }, { status: 400 });
      }
      const projection = projectApprovedSmartMetadata(loaded);
      const filenameSuggestion = projection.filenameSuggestion;
      if (!filenameSuggestion) {
        return NextResponse.json({ error: "No filename suggestion available from reviewed metadata." }, { status: 400 });
      }
      const draft = buildSmartRenamePreviewDraft({
        sourcePath: realPath,
        filenameSuggestion,
      });
      return NextResponse.json({
        renamePreview: draft,
      }, { headers: { "Cache-Control": "no-store" } });
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
