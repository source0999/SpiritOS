import { NextRequest, NextResponse } from "next/server";
import {
  captureSpiritFlixFaceLearningMutation,
  getSpiritFlixFaceLearningRequest,
  requestSpiritFlixFaceLearning,
  restoreSpiritFlixFaceLearningMutation,
} from "@/lib/spiritflix/face-learning";
import type { FaceOrganizerPerformer } from "@/lib/spiritflix-types";
import { resolveSpiritFlixAdminApprovalBinding } from "@/lib/coding/spiritflix-admin-approval-binding";
import { runApprovedSpiritFlixAdminMutation, SpiritFlixAdminTransactionError } from "@/lib/coding/spiritflix-admin-transaction";

export const runtime = "nodejs";

interface RouteContext {
  params: Promise<{ itemId: string }>;
}

interface FaceLearningPayload {
  itemId?: unknown;
  filePath?: unknown;
  modelName?: unknown;
  sidecarPath?: unknown;
  faceGuess?: unknown;
  relatedItems?: unknown;
  approval_id?: unknown;
}

function isFaceGuess(value: unknown): value is FaceOrganizerPerformer {
  return Boolean(value && typeof value === "object" && "name" in value && typeof (value as { name?: unknown }).name === "string");
}

function parseRelatedItems(value: unknown): Array<{ itemId: string; filePath?: string }> {
  if (!Array.isArray(value)) return [];
  const relatedItems: Array<{ itemId: string; filePath?: string }> = [];
  value.forEach((item) => {
    if (!item || typeof item !== "object") return;
    const candidate = item as { itemId?: unknown; filePath?: unknown };
    if (typeof candidate.itemId !== "string") return;
    relatedItems.push({
      itemId: candidate.itemId,
      filePath: typeof candidate.filePath === "string" ? candidate.filePath : undefined,
    });
  });
  return relatedItems;
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { itemId } = await context.params;

  let payload: FaceLearningPayload;
  try {
    payload = (await request.json()) as FaceLearningPayload;
  } catch {
    return NextResponse.json({ error: "Invalid SpiritFlix face learning request." }, { status: 400 });
  }

  if (typeof payload.modelName !== "string") {
    return NextResponse.json({ error: "modelName must be a string." }, { status: 400 });
  }

  const approvalId = typeof payload.approval_id === "string" ? payload.approval_id : "";
  if (!approvalId) return NextResponse.json({ reason_code: "spiritflix_admin_approval_missing" }, { status: 400 });
  const decodedItemId = decodeURIComponent(itemId);
  if (payload.itemId !== decodedItemId) return NextResponse.json({ reason_code: "spiritflix_admin_item_id_mismatch" }, { status: 400 });
  const filePath = typeof payload.filePath === "string" ? payload.filePath : undefined;
  const sidecarPath = typeof payload.sidecarPath === "string" ? payload.sidecarPath : undefined;
  const faceGuess = isFaceGuess(payload.faceGuess) ? payload.faceGuess : undefined;
  const relatedItems = parseRelatedItems(payload.relatedItems);

  try {
    const binding = await resolveSpiritFlixAdminApprovalBinding("face-learning", {
      itemId: decodedItemId,
      filePath,
      modelName: payload.modelName,
      sidecarPath,
      faceGuess,
      relatedItems,
    });
    const completed = await runApprovedSpiritFlixAdminMutation({
      approvalId,
      binding,
      capture: () => captureSpiritFlixFaceLearningMutation(decodedItemId, sidecarPath),
      mutate: () => requestSpiritFlixFaceLearning({
        itemId: decodedItemId,
        filePath,
        modelName: payload.modelName as string,
        sidecarPath,
        faceGuess,
        relatedItems,
      }),
      rollback: (snapshot) => restoreSpiritFlixFaceLearningMutation(snapshot),
      verify: async (record) => {
        const stored = await getSpiritFlixFaceLearningRequest(decodedItemId);
        if (!stored || stored.modelName !== record.modelName || stored.itemId !== decodedItemId) {
          throw new Error("spiritflix_admin_face_learning_verification_failed");
        }
        return {
          schema: "spiritflix-admin-face-learning-result/v1",
          state: {
            actions: stored.actions,
            filePath: stored.filePath ?? null,
            itemId: stored.itemId,
            modelName: stored.modelName,
            relatedItems: stored.relatedItems,
            sidecarPath: stored.sidecarPath ?? null,
            status: stored.status,
          },
        };
      },
    });
    return NextResponse.json({
      record: completed.result,
      authority: {
        participant_invocation_ids: completed.evidence.participant_invocations.map((item) => item.invocation_id),
        result_hash: completed.evidence.result_hash,
      },
    }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return NextResponse.json(
      error instanceof SpiritFlixAdminTransactionError
        ? { reason_code: error.reasonCode }
        : { error: error instanceof Error ? error.message : "SpiritFlix face learning request failed." },
      { status: error instanceof SpiritFlixAdminTransactionError ? error.status : 400 },
    );
  }
}
