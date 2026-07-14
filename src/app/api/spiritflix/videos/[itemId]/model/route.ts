import { NextRequest, NextResponse } from "next/server";
import { spiritFlixAdminMutationDenied } from "@/lib/spiritflix/admin-authority";
import {
  getSpiritFlixManualModelForItem,
  setSpiritFlixManualModelForItem,
} from "@/lib/spiritflix/manual-models";

export const runtime = "nodejs";

export async function PUT(_request: NextRequest, _context: RouteContext) {
  return NextResponse.json(spiritFlixAdminMutationDenied(), { status: 410 });
}

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

async function legacyPUT(request: NextRequest, context: RouteContext) {
  const { itemId } = await context.params;

  let payload: { modelName?: unknown; filePath?: unknown; knownModelNames?: unknown };
  try {
    payload = (await request.json()) as { modelName?: unknown; filePath?: unknown; knownModelNames?: unknown };
  } catch {
    return NextResponse.json({ error: "Invalid SpiritFlix manual model request." }, { status: 400 });
  }

  if (typeof payload.modelName !== "string") {
    return NextResponse.json({ error: "modelName must be a string." }, { status: 400 });
  }

  try {
    const result = await setSpiritFlixManualModelForItem({
      itemId: decodeURIComponent(itemId),
      filePath: typeof payload.filePath === "string" ? payload.filePath : undefined,
      modelName: payload.modelName,
      knownModelNames: Array.isArray(payload.knownModelNames) ? payload.knownModelNames.filter((name): name is string => typeof name === "string") : undefined,
    });
    return NextResponse.json(result, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix manual video model update failed." },
      { status: 400 },
    );
  }
}
