import { NextRequest, NextResponse } from "next/server";
import { runSpiritFlixJobWorkerOnce } from "@/lib/spiritflix/admin/jobs";
import type { SpiritFlixJobWorkerFinalState, SpiritFlixJobWorkerPlaceholderState } from "@/lib/spiritflix/admin/jobs";

export const runtime = "nodejs";

interface WorkerPayload {
  jobId?: unknown;
  finalState?: unknown;
  placeholderState?: unknown;
}

function parseFinalState(value: unknown): SpiritFlixJobWorkerFinalState | undefined {
  return value === "ready" || value === "needs_review" || value === "failed" ? value : undefined;
}

function parsePlaceholderState(value: unknown): SpiritFlixJobWorkerPlaceholderState | undefined {
  return value === "matching" || value === "converting" ? value : undefined;
}

export async function POST(request: NextRequest) {
  let payload: WorkerPayload = {};
  try {
    const text = await request.text();
    payload = text.trim() ? (JSON.parse(text) as WorkerPayload) : {};
  } catch {
    return NextResponse.json({ error: "Invalid SpiritFlix worker request." }, { status: 400 });
  }

  try {
    const result = await runSpiritFlixJobWorkerOnce({
      jobId: typeof payload.jobId === "string" ? payload.jobId : undefined,
      finalState: parseFinalState(payload.finalState),
      placeholderState: parsePlaceholderState(payload.placeholderState),
      mode: "no_media_mutation",
      workerId: "admin-worker-api",
    });
    return NextResponse.json(result, { status: result.claimed ? 202 : 200, headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "SpiritFlix worker tick failed." },
      { status: 400, headers: { "Cache-Control": "no-store" } },
    );
  }
}
