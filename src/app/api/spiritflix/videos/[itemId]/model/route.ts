import { NextRequest, NextResponse } from "next/server";
import {
  captureSpiritFlixManualModelMutation,
  getSpiritFlixManualModelForItem,
  restoreSpiritFlixManualModelMutation,
  setSpiritFlixManualModelForItem,
} from "@/lib/spiritflix/manual-models";
import { resolveSpiritFlixAdminApprovalBinding } from "@/lib/coding/spiritflix-admin-approval-binding";
import { runApprovedSpiritFlixAdminMutation, SpiritFlixAdminTransactionError } from "@/lib/coding/spiritflix-admin-transaction";

export const runtime = "nodejs";

interface RouteContext {
  params: Promise<{ itemId: string }>;
}

export async function GET(request: NextRequest, context: RouteContext) {
  const { itemId } = await context.params;

  try {
    const lookupFilePath = request.nextUrl.searchParams.get("filePath") ?? undefined;
    const record = await getSpiritFlixManualModelForItem(decodeURIComponent(itemId), { lookupFilePath });
    return NextResponse.json(record, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix manual video model failed." },
      { status: 400 },
    );
  }
}

export async function PUT(request: NextRequest, context: RouteContext) {
  const { itemId } = await context.params;

  let payload: { itemId?: unknown; modelName?: unknown; filePath?: unknown; knownModelNames?: unknown; approval_id?: unknown };
  try {
    payload = (await request.json()) as { itemId?: unknown; modelName?: unknown; filePath?: unknown; knownModelNames?: unknown; approval_id?: unknown };
  } catch {
    return NextResponse.json({ error: "Invalid SpiritFlix manual model request." }, { status: 400 });
  }

  if (typeof payload.modelName !== "string") {
    return NextResponse.json({ error: "modelName must be a string." }, { status: 400 });
  }

  const approvalId = typeof payload.approval_id === "string" ? payload.approval_id : "";
  if (!approvalId) return NextResponse.json({ reason_code: "spiritflix_admin_approval_missing" }, { status: 400 });
  const decodedItemId = decodeURIComponent(itemId);
  if (payload.itemId !== decodedItemId) return NextResponse.json({ reason_code: "spiritflix_admin_item_id_mismatch" }, { status: 400 });
  const filePath = typeof payload.filePath === "string" ? payload.filePath : undefined;
  const knownModelNames = Array.isArray(payload.knownModelNames)
    ? payload.knownModelNames.filter((name): name is string => typeof name === "string")
    : undefined;

  try {
    const binding = await resolveSpiritFlixAdminApprovalBinding("manual-model", {
      itemId: decodedItemId,
      filePath,
      modelName: payload.modelName,
      knownModelNames,
    });
    const completed = await runApprovedSpiritFlixAdminMutation({
      approvalId,
      binding,
      capture: () => captureSpiritFlixManualModelMutation(decodedItemId),
      mutate: () => setSpiritFlixManualModelForItem({
        itemId: decodedItemId,
        filePath,
        modelName: payload.modelName as string,
        knownModelNames,
      }),
      rollback: (snapshot) => restoreSpiritFlixManualModelMutation(snapshot),
      verify: async (result) => {
        const stored = await getSpiritFlixManualModelForItem(decodedItemId, { lookupFilePath: filePath });
        if (stored.modelName !== result.record.modelName) {
          throw new Error("spiritflix_admin_model_verification_failed");
        }
        return {
          schema: "spiritflix-admin-manual-model-result/v1",
          state: { filePath: stored.filePath ?? null, itemId: stored.itemId, modelName: stored.modelName },
        };
      },
    });
    return NextResponse.json({
      ...completed.result,
      authority: {
        participant_invocation_ids: completed.evidence.participant_invocations.map((item) => item.invocation_id),
        result_hash: completed.evidence.result_hash,
      },
    }, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    return NextResponse.json(
      error instanceof SpiritFlixAdminTransactionError
        ? { reason_code: error.reasonCode }
        : { error: error instanceof Error ? error.message : "SpiritFlix manual video model update failed." },
      { status: error instanceof SpiritFlixAdminTransactionError ? error.status : 400 },
    );
  }
}
