import fs from "node:fs/promises";
import { NextRequest, NextResponse } from "next/server";

import { isSpiritFlixAdminPathError } from "@/lib/spiritflix/admin/paths";
import {
  buildSpiritFlixSmartRenamePlan,
  getSmartAnalysisPath,
  previewSpiritFlixSmartBatch,
  reviewSpiritFlixSmartBatch,
  runSpiritFlixSmartBatch,
  type SpiritFlixSmartBatchOptions,
  type SpiritFlixSmartBatchPreview,
  type SpiritFlixSmartBatchReviewMode,
  type SpiritFlixSmartRenamePlan,
} from "@/lib/spiritflix/admin/smart";
import { resolveSpiritFlixSmartMediaRoot } from "@/lib/spiritflix/admin/smart/media-root";
import {
  captureSpiritFlixFiles,
  restoreSpiritFlixFiles,
  type SpiritFlixFileMutationSnapshot,
} from "@/lib/spiritflix/admin/file-mutation-snapshot";
import { resolveSpiritFlixAdminApprovalBinding } from "@/lib/coding/spiritflix-admin-approval-binding";
import { runApprovedSpiritFlixAdminMutation, SpiritFlixAdminTransactionError } from "@/lib/coding/spiritflix-admin-transaction";

export const runtime = "nodejs";

type SmartBatchBody = {
  action?: string;
  approval_id?: unknown;
  editedFilenameSuggestion?: string;
  force?: boolean;
  maxItems?: number;
  path?: string;
  paths?: string[];
  recursive?: boolean;
  reviewMode?: string;
};

function numberParam(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string" || !value.trim()) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function boolParam(value: unknown): boolean {
  return value === true || value === "true";
}

function jsonError(error: unknown, fallbackStatus = 500) {
  if (error instanceof SpiritFlixAdminTransactionError) {
    return NextResponse.json({ reason_code: error.reasonCode }, { status: error.status });
  }
  if (isSpiritFlixAdminPathError(error)) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Invalid path." }, { status: 400 });
  }
  const message = error instanceof Error ? error.message : "Smart batch analysis failed.";
  const status = /requires a folder|path|outside|traversal|not allowed|selection|unsupported|must be/i.test(message) ? 400 : fallbackStatus;
  return NextResponse.json({ error: message.slice(0, 500) }, { status });
}

function assertReviewMode(value: unknown): SpiritFlixSmartBatchReviewMode {
  if (value === "approve_all_tags" || value === "approve_name" || value === "reject_all_tags" || value === "mark_reviewed") {
    return value;
  }
  throw new Error("Unsupported smart batch review mode.");
}

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  try {
    return NextResponse.json(await previewSpiritFlixSmartBatch({
      path: url.searchParams.get("path") ?? undefined,
      recursive: boolParam(url.searchParams.get("recursive")),
      maxItems: numberParam(url.searchParams.get("maxItems")),
    }), { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return jsonError(error);
  }
}

async function sidecarsFor(options: SpiritFlixSmartBatchOptions): Promise<string[]> {
  const preview = await previewSpiritFlixSmartBatch(options);
  return Promise.all(preview.items.map(async (item) => {
    const details = await fs.stat(item.path);
    return getSmartAnalysisPath(
      { videoPath: item.path, fileSizeBytes: details.size, mtimeMs: details.mtimeMs },
      { mediaRoot: resolveSpiritFlixSmartMediaRoot(item.path) },
    );
  }));
}

export async function POST(request: NextRequest) {
  let body: SmartBatchBody;
  try {
    body = await request.json() as SmartBatchBody;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }
  const approvalId = typeof body.approval_id === "string" ? body.approval_id : "";
  if (!approvalId) return NextResponse.json({ reason_code: "spiritflix_admin_approval_missing" }, { status: 400 });
  const action = body.action?.trim() || "run";
  if (action !== "preview" && action !== "run" && action !== "review" && action !== "renamePlan") {
    return NextResponse.json({ error: "Unsupported smart batch action." }, { status: 400 });
  }
  if (body.paths !== undefined && (!Array.isArray(body.paths) || body.paths.some((item) => typeof item !== "string" || !item.trim()))) {
    return NextResponse.json({ error: "Smart batch paths must be non-empty strings." }, { status: 400 });
  }
  const options: SpiritFlixSmartBatchOptions = {
    path: body.path,
    paths: body.paths,
    recursive: Boolean(body.recursive),
    maxItems: numberParam(body.maxItems),
    force: Boolean(body.force),
  };
  let reviewMode: SpiritFlixSmartBatchReviewMode | undefined;
  try {
    if (action === "review") reviewMode = assertReviewMode(body.reviewMode);
    // Resolving the exact candidate list is a pre-consumption validation step.
    const sidecarPaths = await sidecarsFor(options);
    const binding = await resolveSpiritFlixAdminApprovalBinding("smart-batch", {
      ...(body.path !== undefined ? { path: body.path } : {}),
      ...(body.paths !== undefined ? { paths: body.paths } : {}),
      action,
      ...(reviewMode ? { reviewMode } : {}),
      ...(body.editedFilenameSuggestion !== undefined ? { editedFilenameSuggestion: body.editedFilenameSuggestion } : {}),
      ...(body.recursive !== undefined ? { recursive: body.recursive } : {}),
      ...(body.maxItems !== undefined ? { maxItems: body.maxItems } : {}),
      ...(body.force !== undefined ? { force: body.force } : {}),
    });
    const completed = await runApprovedSpiritFlixAdminMutation<
      SpiritFlixFileMutationSnapshot,
      SpiritFlixSmartBatchPreview | SpiritFlixSmartRenamePlan
    >({
      approvalId,
      binding,
      capture: () => captureSpiritFlixFiles(sidecarPaths),
      mutate: () => action === "preview"
        ? previewSpiritFlixSmartBatch(options)
        : action === "renamePlan"
          ? buildSpiritFlixSmartRenamePlan(options)
          : action === "review"
            ? reviewSpiritFlixSmartBatch({
                ...options,
                reviewMode: reviewMode!,
                editedFilenameSuggestion: body.editedFilenameSuggestion,
              })
            : runSpiritFlixSmartBatch(options),
      rollback: (snapshot) => restoreSpiritFlixFiles(snapshot),
      verify: async (result) => {
        if (!result || typeof result !== "object" || !("schema" in result)) {
          throw new Error("spiritflix_admin_batch_verification_failed");
        }
        const fresh = action === "renamePlan" ? result : await previewSpiritFlixSmartBatch(options);
        return {
          schema: "spiritflix-admin-smart-batch-result/v1",
          state: {
            action,
            fresh,
            selectedPaths: body.paths ?? [],
            sourcePath: body.path ?? null,
          },
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
