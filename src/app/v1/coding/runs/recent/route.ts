import { listRecentCodingRuns } from "@/lib/coding/durable-run-store";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const limit = Number(url.searchParams.get("limit") || 10);
  const runs = await listRecentCodingRuns(limit);
  return Response.json({ count: runs.length, runs });
}
