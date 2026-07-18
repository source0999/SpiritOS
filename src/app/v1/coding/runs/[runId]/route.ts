import { getCodingRun } from "@/lib/coding/durable-run-store";
import {
  backendCodingRunMutationForbidden,
  backendCodingRunReadFailure,
} from "@/lib/coding/backend-run-route-policy";

export async function GET(_request: Request, context: { params: Promise<{ runId: string }> }) {
  const { runId } = await context.params;
  try {
    const run = await getCodingRun(runId);
    if (!run) return Response.json({ error: "coding_run_not_found" }, { status: 404 });
    return Response.json({
      authority: { owner: "source_proxy", projection: "read_only" },
      run,
    });
  } catch (error) {
    return backendCodingRunReadFailure(error);
  }
}

export async function PATCH(_request: Request, _context: { params: Promise<{ runId: string }> }) {
  void _request;
  void _context;
  return backendCodingRunMutationForbidden("patch");
}
