import { isMacWorkerJobType } from "@/lib/mac-worker/contract";
import { runMacWorkerJob } from "@/lib/mac-worker/client";
import { getMacWorkerStatus } from "@/lib/mac-worker/registry";
import type { MacWorkerJobInput } from "@/lib/mac-worker/types";

export const dynamic = "force-dynamic";

export async function GET() {
  return Response.json(
    {
      ok: true,
      status: getMacWorkerStatus(),
    },
    { headers: { "Cache-Control": "no-store" } },
  );
}

export async function POST(request: Request) {
  const body = await request.json().catch(() => ({}));
  const jobType = body?.job_type;
  if (!isMacWorkerJobType(jobType)) {
    return Response.json(
      { ok: false, error: "Unsupported or missing job_type", status: getMacWorkerStatus() },
      { status: 400, headers: { "Cache-Control": "no-store" } },
    );
  }

  const result = await runMacWorkerJob(jobType, (body.input || {}) as MacWorkerJobInput);
  return Response.json(
    {
      ok: result.success,
      result,
      status: getMacWorkerStatus(),
    },
    { status: result.success ? 200 : 502, headers: { "Cache-Control": "no-store" } },
  );
}
