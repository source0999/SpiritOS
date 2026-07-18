import { listRecentCodingRuns } from "@/lib/coding/durable-run-store";
import {
  backendCodingRunMutationForbidden,
  backendCodingRunReadFailure,
} from "@/lib/coding/backend-run-route-policy";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const limit = Number(url.searchParams.get("limit") || 10);
  try {
    const runs = await listRecentCodingRuns(limit);
    return Response.json({
      authority: { owner: "source_proxy", projection: "read_only" },
      count: runs.length,
      runs,
    });
  } catch (error) {
    return backendCodingRunReadFailure(error);
  }
}

export async function POST(_request: Request) {
  void _request;
  return backendCodingRunMutationForbidden("create");
}
