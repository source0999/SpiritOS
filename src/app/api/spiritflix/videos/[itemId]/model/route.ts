import { NextRequest, NextResponse } from "next/server";
import {
  getSpiritFlixManualModelForItem,
  setSpiritFlixManualModelForItem,
} from "@/lib/spiritflix/manual-models";
import { consumeSpiritFlixAdminApproval, finalizeSpiritFlixAdminApproval } from "@/lib/coding/spiritflix-admin-approval-authority";

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

  let payload: { modelName?: unknown; filePath?: unknown; knownModelNames?: unknown; approval_id?: unknown };
  try {
    payload = (await request.json()) as { modelName?: unknown; filePath?: unknown; knownModelNames?: unknown; approval_id?: unknown };
  } catch {
    return NextResponse.json({ error: "Invalid SpiritFlix manual model request." }, { status: 400 });
  }

  if (typeof payload.modelName !== "string") {
    return NextResponse.json({ error: "modelName must be a string." }, { status: 400 });
  }

  const approvalId = typeof payload.approval_id === "string" ? payload.approval_id : "";
  if (!approvalId) return NextResponse.json({ reason_code: "spiritflix_admin_approval_missing" }, { status: 400 });
  const action = "metadata.mutation";
  const target = `spiritflix:videos:${decodeURIComponent(itemId)}:model`;
  const plan = { field: "modelName", value: payload.modelName };
  const consumed = await consumeSpiritFlixAdminApproval(approvalId, action, target, plan);
  if (!consumed.ok) return NextResponse.json({ reason_code: consumed.reason }, { status: 422 });

  try {
    const result = await setSpiritFlixManualModelForItem({
      itemId: decodeURIComponent(itemId),
      filePath: typeof payload.filePath === "string" ? payload.filePath : undefined,
      modelName: payload.modelName,
      knownModelNames: Array.isArray(payload.knownModelNames) ? payload.knownModelNames.filter((name): name is string => typeof name === "string") : undefined,
    });
    await finalizeSpiritFlixAdminApproval(approvalId, action, target, plan, Number(consumed.value.generation), "succeeded");
    return NextResponse.json(result, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    await finalizeSpiritFlixAdminApproval(approvalId, action, target, plan, Number(consumed.value.generation), "failed");
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix manual video model update failed." },
      { status: 400 },
    );
  }
}
