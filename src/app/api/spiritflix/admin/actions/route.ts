import { NextRequest, NextResponse } from "next/server";
import { handleSpiritFlixAdminAction, normalizeSpiritFlixAdminActionRequest } from "@/lib/spiritflix/admin/actions";
import type { SpiritFlixAdminActionRequest } from "@/lib/spiritflix/admin/types";
import { consumeSpiritFlixAdminApproval, finalizeSpiritFlixAdminApproval } from "@/lib/coding/spiritflix-admin-approval-authority";

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

  const approvalId = typeof payload.approval_id === "string" ? payload.approval_id : "";
  if (!approvalId) return NextResponse.json({ reason_code: "spiritflix_admin_approval_missing" }, { status: 400 });
  const action = "admin.action";
  const target = `spiritflix:admin-actions:${payload.action}`;
  const plan = { mode: payload.mode ?? payload.phase ?? "" };
  const consumed = await consumeSpiritFlixAdminApproval(approvalId, action, target, plan);
  if (!consumed.ok) return NextResponse.json({ reason_code: consumed.reason }, { status: 422 });

  try {
    const response = await handleSpiritFlixAdminAction(payload);
    await finalizeSpiritFlixAdminApproval(approvalId, action, target, plan, Number(consumed.value.generation), response.allowed ? "succeeded" : "failed");
    return NextResponse.json(response, {
      status: response.allowed ? 200 : 400,
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    await finalizeSpiritFlixAdminApproval(approvalId, action, target, plan, Number(consumed.value.generation), "failed");
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix admin action failed." },
      { status: 500, headers: { "Cache-Control": "no-store" } },
    );
  }
}
