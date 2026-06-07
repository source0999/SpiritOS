import { getActiveCodingRun } from "@/lib/coding/durable-run-store";

export async function GET() {
  const run = await getActiveCodingRun();
  return Response.json({ run });
}
