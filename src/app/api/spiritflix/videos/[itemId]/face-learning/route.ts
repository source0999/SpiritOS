import { NextRequest, NextResponse } from "next/server";
import { requestSpiritFlixFaceLearning } from "@/lib/spiritflix/face-learning";
import type { FaceOrganizerPerformer } from "@/lib/spiritflix-types";
import { consumeSpiritFlixAdminApproval, finalizeSpiritFlixAdminApproval } from "@/lib/coding/spiritflix-admin-approval-authority";

export const runtime = "nodejs";

interface RouteContext {
  params: Promise<{ itemId: string }>;
}

interface FaceLearningPayload {
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
  const action = "face.learning";
  const target = `spiritflix:videos:${decodedItemId}:face-learning`;
  const plan = { modelName: payload.modelName };
  const consumed = await consumeSpiritFlixAdminApproval(approvalId, action, target, plan);
  if (!consumed.ok) return NextResponse.json({ reason_code: consumed.reason }, { status: 422 });

  try {
    const record = await requestSpiritFlixFaceLearning({
      itemId: decodedItemId,
      filePath: typeof payload.filePath === "string" ? payload.filePath : undefined,
      modelName: payload.modelName,
      sidecarPath: typeof payload.sidecarPath === "string" ? payload.sidecarPath : undefined,
      faceGuess: isFaceGuess(payload.faceGuess) ? payload.faceGuess : undefined,
      relatedItems: parseRelatedItems(payload.relatedItems),
    });
    await finalizeSpiritFlixAdminApproval(approvalId, action, target, plan, Number(consumed.value.generation), "succeeded");
    return NextResponse.json({ record }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    await finalizeSpiritFlixAdminApproval(approvalId, action, target, plan, Number(consumed.value.generation), "failed");
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix face learning request failed." },
      { status: 400 },
    );
  }
}
