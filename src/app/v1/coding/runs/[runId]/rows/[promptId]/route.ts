import { backendCodingRunMutationForbidden } from "@/lib/coding/backend-run-route-policy";

export async function POST(
  _request: Request,
  _context: { params: Promise<{ runId: string; promptId: string }> },
) {
  void _request;
  void _context;
  return backendCodingRunMutationForbidden("row_upsert");
}
