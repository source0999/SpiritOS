import { NextRequest, NextResponse } from "next/server";
import {
  getSpiritFlixManualTagsForItem,
  setSpiritFlixManualTagsForItem,
} from "@/lib/spiritflix/manual-tags";
import { consumeSpiritFlixAdminApproval, finalizeSpiritFlixAdminApproval } from "@/lib/coding/spiritflix-admin-approval-authority";

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

  let payload: { manualTags?: unknown; filePath?: unknown; approval_id?: unknown };
  try {
    payload = (await request.json()) as { manualTags?: unknown; filePath?: unknown; approval_id?: unknown };
  } catch {
    return NextResponse.json({ error: "Invalid SpiritFlix manual tag request." }, { status: 400 });
  }

  if (!Array.isArray(payload.manualTags)) {
    return NextResponse.json({ error: "manualTags must be an array." }, { status: 400 });
  }

  const approvalId = typeof payload.approval_id === "string" ? payload.approval_id : "";
  if (!approvalId) return NextResponse.json({ reason_code: "spiritflix_admin_approval_missing" }, { status: 400 });
  const decodedItemId = decodeURIComponent(itemId);
  const action = "metadata.mutation";
  const target = `spiritflix:videos:${decodedItemId}:tags`;
  const plan = { field: "manualTags", count: payload.manualTags.length };
  const consumed = await consumeSpiritFlixAdminApproval(approvalId, action, target, plan);
  if (!consumed.ok) return NextResponse.json({ reason_code: consumed.reason }, { status: 422 });

  try {
    const result = await setSpiritFlixManualTagsForItem({
      itemId: decodedItemId,
      filePath: typeof payload.filePath === "string" ? payload.filePath : undefined,
      manualTags: payload.manualTags,
    });
    await finalizeSpiritFlixAdminApproval(approvalId, action, target, plan, Number(consumed.value.generation), "succeeded");
    return NextResponse.json({
      ...result,
      propagated: {
        tags: [],
        itemIds: [],
      },
    }, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    await finalizeSpiritFlixAdminApproval(approvalId, action, target, plan, Number(consumed.value.generation), "failed");
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix manual video tag update failed." },
      { status: 400 },
    );
  }
}
