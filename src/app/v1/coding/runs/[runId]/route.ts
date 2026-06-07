import { getCodingRun, patchCodingRun } from "@/lib/coding/durable-run-store";

export async function GET(_request: Request, context: { params: Promise<{ runId: string }> }) {
  const { runId } = await context.params;
  const run = await getCodingRun(runId);
  if (!run) return Response.json({ error: "coding_run_not_found" }, { status: 404 });
  return Response.json({ run });
}

export async function PATCH(request: Request, context: { params: Promise<{ runId: string }> }) {
  const { runId } = await context.params;
  const body = await request.json().catch(() => ({}));
  const run = await patchCodingRun(runId, body);
  if (!run) return Response.json({ error: "coding_run_not_found" }, { status: 404 });
  return Response.json({ run });
}
