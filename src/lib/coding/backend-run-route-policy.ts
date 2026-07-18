import { CodingRunProjectionError } from "@/lib/coding/durable-run-store";

export function backendCodingRunMutationForbidden(operation: string): Response {
  return Response.json(
    {
      error: "next_coding_run_mutation_forbidden",
      operation,
      authority: {
        owner: "source_proxy",
        store: "long_running_tasks_sqlite",
      },
      message: "Create and update the Source Proxy task; this Next route is a read-only projection.",
    },
    { headers: { allow: "GET" }, status: 405 },
  );
}

export function backendCodingRunReadFailure(error: unknown): Response {
  const reasonCode =
    error instanceof CodingRunProjectionError
      ? error.reasonCode
      : "source_proxy_coding_run_projection_unavailable";
  return Response.json(
    {
      error: reasonCode,
      authority: {
        owner: "source_proxy",
        store: "long_running_tasks_sqlite",
      },
      message: "Authoritative Source Proxy task truth is unavailable; no cached status was substituted.",
    },
    { status: 502 },
  );
}
