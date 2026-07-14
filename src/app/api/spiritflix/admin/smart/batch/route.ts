import { NextRequest, NextResponse } from "next/server";
import { isSpiritFlixAdminPathError } from "@/lib/spiritflix/admin/paths";
import {
  buildSpiritFlixSmartRenamePlan,
  previewSpiritFlixSmartBatch,
  reviewSpiritFlixSmartBatch,
  runSpiritFlixSmartBatch,
  type SpiritFlixSmartBatchReviewMode,
} from "@/lib/spiritflix/admin/smart";
import { consumeSpiritFlixAdminApproval, finalizeSpiritFlixAdminApproval } from "@/lib/coding/spiritflix-admin-approval-authority";

export const runtime = "nodejs";

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
  if (isSpiritFlixAdminPathError(error)) {
    return NextResponse.json({ error: error instanceof Error ? error.message : "Invalid path." }, { status: 400 });
  }
  const message = error instanceof Error ? error.message : "Smart batch analysis failed.";
  const status = /requires a folder|path|outside|traversal|not allowed|selection|unsupported/i.test(message) ? 400 : fallbackStatus;
  return NextResponse.json({ error: message.slice(0, 500) }, { status });
}

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  try {
    const payload = await previewSpiritFlixSmartBatch({
      path: url.searchParams.get("path") ?? undefined,
      recursive: boolParam(url.searchParams.get("recursive")),
      maxItems: numberParam(url.searchParams.get("maxItems")),
    });
    return NextResponse.json(payload, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return jsonError(error);
  }
}

export async function POST(request: NextRequest) {
  let body: {
    path?: string;
    paths?: string[];
    action?: string;
    reviewMode?: string;
    editedFilenameSuggestion?: string;
    recursive?: boolean;
    maxItems?: number;
    force?: boolean;
    approval_id?: unknown;
  };
  try {
    body = (await request.json()) as typeof body;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const approvalId = typeof body.approval_id === "string" ? body.approval_id : "";
  if (!approvalId) return NextResponse.json({ reason_code: "spiritflix_admin_approval_missing" }, { status: 400 });
  const actionLabel = body.action?.trim() || "run";
  if (actionLabel !== "preview" && actionLabel !== "run" && actionLabel !== "review" && actionLabel !== "renamePlan") {
    return NextResponse.json({ error: "Unsupported smart batch action." }, { status: 400 });
  }
  const target = `spiritflix:smart-batch:${body.path ?? (Array.isArray(body.paths) ? body.paths.join(",") : "")}`;
  const plan = { action: actionLabel };
  const consumed = await consumeSpiritFlixAdminApproval(approvalId, "smart.batch", target, plan);
  if (!consumed.ok) return NextResponse.json({ reason_code: consumed.reason }, { status: 422 });

  try {
    const options = {
      path: body.path,
      paths: Array.isArray(body.paths) ? body.paths : undefined,
      recursive: Boolean(body.recursive),
      maxItems: numberParam(body.maxItems),
      force: Boolean(body.force),
    };
    const payload = actionLabel === "preview"
      ? await previewSpiritFlixSmartBatch(options)
      : actionLabel === "renamePlan"
        ? await buildSpiritFlixSmartRenamePlan(options)
        : actionLabel === "review"
          ? await reviewSpiritFlixSmartBatch({
              ...options,
              reviewMode: assertReviewMode(body.reviewMode),
              editedFilenameSuggestion: typeof body.editedFilenameSuggestion === "string" ? body.editedFilenameSuggestion : undefined,
            })
          : await runSpiritFlixSmartBatch(options);
    await finalizeSpiritFlixAdminApproval(approvalId, "smart.batch", target, plan, Number(consumed.value.generation), "succeeded");
    return NextResponse.json(payload, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    await finalizeSpiritFlixAdminApproval(approvalId, "smart.batch", target, plan, Number(consumed.value.generation), "failed");
    return jsonError(error);
  }
}

function assertReviewMode(value: unknown): SpiritFlixSmartBatchReviewMode {
  if (value === "approve_all_tags" || value === "approve_name" || value === "reject_all_tags" || value === "mark_reviewed") {
    return value;
  }
  throw new Error("Unsupported smart batch review mode.");
}
