import { getActiveCodingRun } from "@/lib/coding/durable-run-store";
import { backendCodingRunReadFailure } from "@/lib/coding/backend-run-route-policy";

export async function GET() {
  try {
    const run = await getActiveCodingRun();
    return Response.json({
      authority: { owner: "source_proxy", projection: "read_only" },
      run,
    });
  } catch (error) {
    return backendCodingRunReadFailure(error);
  }
}
