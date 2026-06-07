import { upsertCodingRunRow } from "@/lib/coding/durable-run-store";

export async function POST(
  request: Request,
  context: { params: Promise<{ runId: string; promptId: string }> },
) {
  const { runId, promptId } = await context.params;
  const body = await request.json().catch(() => ({}));
  const run = await upsertCodingRunRow(runId, promptId, body);
  if (!run) return Response.json({ error: "coding_run_not_found" }, { status: 404 });
  return Response.json({ run });
}
