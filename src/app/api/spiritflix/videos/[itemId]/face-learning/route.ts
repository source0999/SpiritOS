import { NextRequest, NextResponse } from "next/server";
import { spiritFlixAdminMutationDenied } from "@/lib/spiritflix/admin-authority";
import { requestSpiritFlixFaceLearning } from "@/lib/spiritflix/face-learning";
import type { FaceOrganizerPerformer } from "@/lib/spiritflix-types";

export const runtime = "nodejs";

export async function POST(_request: NextRequest, _context: RouteContext) {
  return NextResponse.json(spiritFlixAdminMutationDenied(), { status: 410 });
}

interface RouteContext {
  params: Promise<{ itemId: string }>;
}

interface FaceLearningPayload {
  filePath?: unknown;
  modelName?: unknown;
  sidecarPath?: unknown;
  faceGuess?: unknown;
  relatedItems?: unknown;
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

async function legacyPOST(request: NextRequest, context: RouteContext) {
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

  try {
    const record = await requestSpiritFlixFaceLearning({
      itemId: decodeURIComponent(itemId),
      filePath: typeof payload.filePath === "string" ? payload.filePath : undefined,
      modelName: payload.modelName,
      sidecarPath: typeof payload.sidecarPath === "string" ? payload.sidecarPath : undefined,
      faceGuess: isFaceGuess(payload.faceGuess) ? payload.faceGuess : undefined,
      relatedItems: parseRelatedItems(payload.relatedItems),
    });
    return NextResponse.json({ record }, { headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix face learning request failed." },
      { status: 400 },
    );
  }
}
