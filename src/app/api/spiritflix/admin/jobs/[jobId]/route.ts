import { NextRequest, NextResponse } from "next/server";
import { appendSpiritFlixJobState, failSpiritFlixJob, getSpiritFlixJobHistory, requeueSpiritFlixJob, reverseSpiritFlixOrganizeReceipt } from "@/lib/spiritflix/admin/jobs";

export const runtime = "nodejs";

interface RouteContext {
  params: Promise<{ jobId: string }>;
}

type JobControlPayload = {
  action?: unknown;
  reasonCode?: unknown;
  reason?: unknown;
};

function noStore(body: unknown, status = 200) {
  return NextResponse.json(body, { status, headers: { "Cache-Control": "no-store" } });
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const { jobId } = await context.params;
  try {
    const history = await getSpiritFlixJobHistory(decodeURIComponent(jobId));
    if (!history.job) return noStore({ error: "SpiritFlix job was not found." }, 404);
    return noStore(history);
  } catch (error) {
    return noStore({ error: error instanceof Error ? error.message : "SpiritFlix job history read failed." }, 400);
  }
}

export async function POST(request: NextRequest, context: RouteContext) {
  const { jobId } = await context.params;
  let payload: JobControlPayload;
  try {
    payload = (await request.json()) as JobControlPayload;
  } catch {
    return noStore({ error: "Invalid SpiritFlix job control request." }, 400);
  }

  try {
    const decodedJobId = decodeURIComponent(jobId);
    if (payload.action === "fail") {
      if (typeof payload.reasonCode !== "string" || typeof payload.reason !== "string") {
        return noStore({ error: "Failing a SpiritFlix job requires reasonCode and reason." }, 400);
      }
      return noStore(await failSpiritFlixJob({ jobId: decodedJobId, reasonCode: payload.reasonCode, reason: payload.reason }));
    }
    if (payload.action === "requeue") {
      return noStore(await requeueSpiritFlixJob({ jobId: decodedJobId }));
    }
    if (payload.action === "reverse_move") {
      const history = await getSpiritFlixJobHistory(decodedJobId);
      const job = history.job;
      const receipt = job?.details?.organizeReceipt;
      if (!job || !receipt || typeof receipt !== "object" || Array.isArray(receipt)) {
        return noStore({ error: "SpiritFlix job has no reversible organize receipt." }, 400);
      }
      const reverseReceipt = await reverseSpiritFlixOrganizeReceipt(receipt as never);
      const event = await appendSpiritFlixJobState({
        videoPath: job.videoPath,
        fileSizeBytes: job.fileSizeBytes,
        mtimeMs: job.mtimeMs,
        jobId: job.jobId,
        fileName: job.fileName,
        state: "needs_review",
        details: {
          source: "spiritflix-job-control",
          action: "reverse_move",
          reverseReceipt,
          mediaMutation: reverseReceipt.reasonCode === "reversed",
        },
      });
      return noStore({ action: "reverse_move", reverseReceipt, job: event });
    }
    return noStore({ error: "Unsupported SpiritFlix job control action." }, 400);
  } catch (error) {
    return noStore({ error: error instanceof Error ? error.message : "SpiritFlix job control failed." }, 400);
  }
}
