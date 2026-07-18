import { NextRequest, NextResponse } from "next/server";
import {
  captureSpiritFlixManualTagsMutation,
  getSpiritFlixManualTagsForItem,
  restoreSpiritFlixManualTagsMutation,
  setSpiritFlixManualTagsForItem,
} from "@/lib/spiritflix/manual-tags";
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
    const record = await getSpiritFlixManualTagsForItem(decodeURIComponent(itemId), { lookupFilePath });
    return NextResponse.json(record, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix manual video tags failed." },
      { status: 400 },
    );
  }
}

export async function PUT(request: NextRequest, context: RouteContext) {
  const { itemId } = await context.params;

  let payload: { itemId?: unknown; manualTags?: unknown; filePath?: unknown; approval_id?: unknown };
  try {
    payload = (await request.json()) as { itemId?: unknown; manualTags?: unknown; filePath?: unknown; approval_id?: unknown };
  } catch {
    return NextResponse.json({ error: "Invalid SpiritFlix manual tag request." }, { status: 400 });
  }

  if (!Array.isArray(payload.manualTags)) {
    return NextResponse.json({ error: "manualTags must be an array." }, { status: 400 });
  }

  const approvalId = typeof payload.approval_id === "string" ? payload.approval_id : "";
  if (!approvalId) return NextResponse.json({ reason_code: "spiritflix_admin_approval_missing" }, { status: 400 });
  const decodedItemId = decodeURIComponent(itemId);
  if (payload.itemId !== decodedItemId) return NextResponse.json({ reason_code: "spiritflix_admin_item_id_mismatch" }, { status: 400 });
  const filePath = typeof payload.filePath === "string" ? payload.filePath : undefined;

  try {
    const binding = await resolveSpiritFlixAdminApprovalBinding("manual-tags", {
      itemId: decodedItemId,
      filePath,
      manualTags: payload.manualTags,
    });
    const completed = await runApprovedSpiritFlixAdminMutation({
      approvalId,
      binding,
      capture: () => captureSpiritFlixManualTagsMutation(decodedItemId),
      mutate: () => setSpiritFlixManualTagsForItem({
        itemId: decodedItemId,
        filePath,
        manualTags: payload.manualTags as string[],
      }),
      rollback: (snapshot) => restoreSpiritFlixManualTagsMutation(snapshot),
      verify: async (result) => {
        const stored = await getSpiritFlixManualTagsForItem(decodedItemId, { lookupFilePath: filePath });
        if (stored.manualTags.join("\u0000") !== result.record.manualTags.join("\u0000")) {
          throw new Error("spiritflix_admin_tags_verification_failed");
        }
        return {
          schema: "spiritflix-admin-manual-tags-result/v1",
          state: { filePath: stored.filePath ?? null, itemId: stored.itemId, manualTags: stored.manualTags },
        };
      },
    });
    return NextResponse.json({
      ...completed.result,
      authority: {
        participant_invocation_ids: completed.evidence.participant_invocations.map((item) => item.invocation_id),
        result_hash: completed.evidence.result_hash,
      },
      propagated: {
        tags: [],
        itemIds: [],
      },
    }, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    return NextResponse.json(
      error instanceof SpiritFlixAdminTransactionError
        ? { reason_code: error.reasonCode }
        : { error: error instanceof Error ? error.message : "SpiritFlix manual video tag update failed." },
      { status: error instanceof SpiritFlixAdminTransactionError ? error.status : 400 },
    );
  }
}
