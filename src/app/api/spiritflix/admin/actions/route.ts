import { NextRequest, NextResponse } from "next/server";
import {
  captureSpiritFlixAdminActionMutation,
  handleSpiritFlixAdminAction,
  normalizeSpiritFlixAdminActionRequest,
  rollbackSpiritFlixAdminActionMutation,
  verifySpiritFlixAdminActionMutation,
} from "@/lib/spiritflix/admin/actions";
import type { SpiritFlixAdminActionRequest } from "@/lib/spiritflix/admin/types";
import { resolveSpiritFlixAdminApprovalBinding } from "@/lib/coding/spiritflix-admin-approval-binding";
import { runApprovedSpiritFlixAdminMutation, SpiritFlixAdminTransactionError } from "@/lib/coding/spiritflix-admin-transaction";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  let payload: SpiritFlixAdminActionRequest & { approval_id?: unknown };

  try {
    payload = normalizeSpiritFlixAdminActionRequest((await request.json()) as SpiritFlixAdminActionRequest & { approval_id?: unknown }) as SpiritFlixAdminActionRequest & { approval_id?: unknown };
  } catch {
    return NextResponse.json({ error: "Invalid SpiritFlix admin action request." }, { status: 400 });
  }

  if (!payload.action || !(payload.mode ?? payload.phase)) {
    return NextResponse.json({ error: "SpiritFlix admin actions require action and mode." }, { status: 400 });
  }

  if ((payload.mode ?? payload.phase) === "preview") {
    const response = await handleSpiritFlixAdminAction(payload);
    return NextResponse.json(response, {
      status: response.allowed ? 200 : 400,
      headers: { "Cache-Control": "no-store" },
    });
  }

  const approvalId = typeof payload.approval_id === "string" ? payload.approval_id : "";
  if (!approvalId) return NextResponse.json({ reason_code: "spiritflix_admin_approval_missing" }, { status: 400 });

  try {
    const previewId = String(payload.confirmToken ?? payload.previewId ?? "");
    if (!previewId) throw new Error("spiritflix_admin_preview_id_required");
    const binding = await resolveSpiritFlixAdminApprovalBinding("admin-action", payload);
    const completed = await runApprovedSpiritFlixAdminMutation({
      approvalId,
      binding,
      capture: () => captureSpiritFlixAdminActionMutation(previewId),
      mutate: () => handleSpiritFlixAdminAction(payload),
      rollback: (snapshot, result) => rollbackSpiritFlixAdminActionMutation(snapshot, result),
      verify: async (result) => ({
        schema: "spiritflix-admin-action-result/v2",
        state: await verifySpiritFlixAdminActionMutation(result),
      }),
    });
    return NextResponse.json({
      ...completed.result,
      authority: {
        participant_invocation_ids: completed.evidence.participant_invocations.map((item) => item.invocation_id),
        result_hash: completed.evidence.result_hash,
      },
    }, {
      status: 200,
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    return NextResponse.json(
      error instanceof SpiritFlixAdminTransactionError
        ? { reason_code: error.reasonCode }
        : { error: error instanceof Error ? error.message : "SpiritFlix admin action failed." },
      { status: error instanceof SpiritFlixAdminTransactionError ? error.status : 500, headers: { "Cache-Control": "no-store" } },
    );
  }
}
