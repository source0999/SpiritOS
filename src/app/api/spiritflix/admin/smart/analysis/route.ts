import fs from "node:fs/promises";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";

import { resolveSpiritFlixAdminPath, isSpiritFlixAdminPathError } from "@/lib/spiritflix/admin/paths";
import {
  assertSmartVideoPathCandidate,
  buildSmartRenamePreviewDraft,
  getSmartAnalysisPath,
  isSpiritFlixSmartVideoExtension,
  metadataSidecarPath,
  projectApprovedSmartMetadata,
  readSmartAnalysis,
  type SpiritFlixSmartAnalysis,
  writeApprovedSmartMetadataSidecar,
} from "@/lib/spiritflix/admin/smart";
import { resolveSpiritFlixSmartMediaRoot } from "@/lib/spiritflix/admin/smart/media-root";
import {
  markSpiritFlixSmartAnalysisReviewed,
  runSpiritFlixSmartReviewPipeline,
  saveSpiritFlixSmartAnalysisReview,
} from "@/lib/spiritflix/admin/smart/review";
import { assertSpiritFlixSmartReviewPayload } from "@/lib/spiritflix/admin/smart/review-metadata";
import { captureSpiritFlixFiles, restoreSpiritFlixFiles } from "@/lib/spiritflix/admin/file-mutation-snapshot";
import { resolveSpiritFlixAdminApprovalBinding } from "@/lib/coding/spiritflix-admin-approval-binding";
import { runApprovedSpiritFlixAdminMutation, SpiritFlixAdminTransactionError } from "@/lib/coding/spiritflix-admin-transaction";

const FORBIDDEN_EXECUTE_ACTIONS = new Set([
  "applyRename",
  "applyMove",
  "executeRename",
  "executeMove",
]);

export const runtime = "nodejs";

type SmartAnalysisMutationBody = {
  action?: string;
  approval_id?: unknown;
  path?: string;
  review?: unknown;
};

async function loadVideoAnalysis(videoPath: string, mediaRoot: string): Promise<{
  analysis: SpiritFlixSmartAnalysis | null;
  sidecarPath: string;
}> {
  const stat = await fs.stat(videoPath);
  if (!stat.isFile()) throw new Error("Smart analysis is only available for video files.");
  const extension = path.extname(videoPath).toLowerCase();
  if (!isSpiritFlixSmartVideoExtension(extension)) throw new Error("Smart analysis is only available for supported video files.");
  const validatedPath = assertSmartVideoPathCandidate(videoPath, { mediaRoot });
  const pathInput = { videoPath: validatedPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs };
  return {
    analysis: await readSmartAnalysis(pathInput, { mediaRoot }),
    sidecarPath: getSmartAnalysisPath(pathInput, { mediaRoot }),
  };
}

function jsonError(error: unknown, fallbackStatus = 500) {
  if (error instanceof SpiritFlixAdminTransactionError) {
    return NextResponse.json({ reason_code: error.reasonCode }, { status: error.status });
  }
  if (isSpiritFlixAdminPathError(error)) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Invalid path." }, { status: 400 });
  }
  const message = error instanceof Error ? error.message : "Smart analysis request failed.";
  const status = /only available|folder|video files|unknown field|known tag|review|overlap|must be|not in suggestedTags|too large|unsupported/i.test(message)
    ? 400
    : fallbackStatus;
  return NextResponse.json({ error: message }, { status });
}

export async function GET(request: NextRequest) {
  const videoPath = new URL(request.url).searchParams.get("path")?.trim() ?? "";
  if (!videoPath) return NextResponse.json({ error: "Missing video path." }, { status: 400 });
  try {
    const { realPath } = await resolveSpiritFlixAdminPath(videoPath);
    const mediaRoot = resolveSpiritFlixSmartMediaRoot(realPath);
    return NextResponse.json(await loadVideoAnalysis(realPath, mediaRoot), { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return jsonError(error);
  }
}

async function performMutation(
  body: SmartAnalysisMutationBody,
  action: string,
  realPath: string,
  mediaRoot: string,
  stat: { mtimeMs: number; size: number },
): Promise<Record<string, unknown>> {
  if (FORBIDDEN_EXECUTE_ACTIONS.has(action)) {
    throw new Error(`${action} is not available in smart tagging. File mutations require Level 2 preview and confirm.`);
  }

  if (action === "exportMetadata" || action === "confirmMetadata") {
    const pathInput = { videoPath: realPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs };
    const loaded = await readSmartAnalysis(pathInput, { mediaRoot });
    if (!loaded) throw new Error("No smart analysis found for this video. Run analyze first.");
    if (!loaded.reviewedMetadata || loaded.reviewedMetadata.reviewStatus === "unreviewed") {
      throw new Error("Analysis must be reviewed before exporting metadata.");
    }
    const result = await writeApprovedSmartMetadataSidecar(loaded, { mediaRoot });
    return { metadataPath: result.path, metadata: projectApprovedSmartMetadata(loaded), confirmed: true };
  }

  if (action === "prepareRenamePreview") {
    const pathInput = { videoPath: realPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs };
    const loaded = await readSmartAnalysis(pathInput, { mediaRoot });
    if (!loaded) throw new Error("No smart analysis found for this video. Run analyze first.");
    if (!loaded.reviewedMetadata || loaded.reviewedMetadata.reviewStatus === "unreviewed") {
      throw new Error("Analysis must be reviewed before preparing rename preview.");
    }
    const filenameSuggestion = projectApprovedSmartMetadata(loaded).filenameSuggestion;
    if (!filenameSuggestion) throw new Error("No filename suggestion available from reviewed metadata.");
    return { renamePreview: buildSmartRenamePreviewDraft({ sourcePath: realPath, filenameSuggestion }) };
  }

  let analysis: SpiritFlixSmartAnalysis;
  if (action === "markReviewed") {
    analysis = await markSpiritFlixSmartAnalysisReviewed(realPath, { mediaRoot });
  } else if (action === "saveReview") {
    analysis = await saveSpiritFlixSmartAnalysisReview(
      realPath,
      assertSpiritFlixSmartReviewPayload(body.review ?? { approvedTagIds: [], rejectedTagIds: [] }),
      { mediaRoot },
    );
  } else if (action === "analyze") {
    analysis = await runSpiritFlixSmartReviewPipeline(realPath, { mediaRoot });
  } else {
    throw new Error("Unsupported smart analysis action.");
  }
  const sidecarPath = getSmartAnalysisPath(
    { videoPath: realPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs },
    { mediaRoot },
  );
  return { analysis, sidecarPath };
}

export async function POST(request: NextRequest) {
  let body: SmartAnalysisMutationBody;
  try {
    body = await request.json() as SmartAnalysisMutationBody;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }
  const approvalId = typeof body.approval_id === "string" ? body.approval_id : "";
  if (!approvalId) return NextResponse.json({ reason_code: "spiritflix_admin_approval_missing" }, { status: 400 });
  const videoPath = body.path?.trim() ?? "";
  if (!videoPath) return NextResponse.json({ error: "Missing video path." }, { status: 400 });
  const action = body.action?.trim() || "analyze";

  try {
    // All path and input validation happens before entering consuming.
    const { realPath } = await resolveSpiritFlixAdminPath(videoPath);
    const mediaRoot = resolveSpiritFlixSmartMediaRoot(realPath);
    const stat = await fs.stat(realPath);
    if (!stat.isFile()) throw new Error("Smart analysis only supports a single video file path.");
    if (!isSpiritFlixSmartVideoExtension(path.extname(realPath).toLowerCase())) {
      throw new Error("Smart analysis only supports supported video files.");
    }
    assertSmartVideoPathCandidate(realPath, { mediaRoot });
    if (body.review !== undefined) assertSpiritFlixSmartReviewPayload(body.review);

    const binding = await resolveSpiritFlixAdminApprovalBinding("smart-analysis", {
      path: videoPath,
      action,
      ...(body.review !== undefined ? { review: body.review } : {}),
    });
    const analysisPath = getSmartAnalysisPath(
      { videoPath: realPath, fileSizeBytes: stat.size, mtimeMs: stat.mtimeMs },
      { mediaRoot },
    );
    const metadataPath = metadataSidecarPath(realPath, mediaRoot);
    const completed = await runApprovedSpiritFlixAdminMutation({
      approvalId,
      binding,
      capture: () => captureSpiritFlixFiles([analysisPath, metadataPath]),
      mutate: () => performMutation(body, action, realPath, mediaRoot, stat),
      rollback: (snapshot) => restoreSpiritFlixFiles(snapshot),
      verify: async (result) => {
        if (action === "prepareRenamePreview") {
          if (!result.renamePreview) throw new Error("spiritflix_admin_rename_preview_verification_failed");
          return { schema: "spiritflix-admin-smart-rename-preview-result/v1", state: result.renamePreview };
        }
        if (action === "exportMetadata" || action === "confirmMetadata") {
          const persisted = JSON.parse(await fs.readFile(metadataPath, "utf8")) as unknown;
          return { schema: "spiritflix-admin-smart-metadata-result/v1", state: { metadataPath, persisted } };
        }
        const persisted = await loadVideoAnalysis(realPath, mediaRoot);
        if (!persisted.analysis) throw new Error("spiritflix_admin_analysis_verification_failed");
        return {
          schema: "spiritflix-admin-smart-analysis-result/v1",
          state: { analysis: persisted.analysis, sidecarPath: persisted.sidecarPath },
        };
      },
    });
    return NextResponse.json({
      ...completed.result,
      authority: {
        participant_invocation_ids: completed.evidence.participant_invocations.map((item) => item.invocation_id),
        result_hash: completed.evidence.result_hash,
      },
    }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return jsonError(error);
  }
}
