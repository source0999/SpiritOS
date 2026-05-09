import "server-only";

// ── API errors - JSON bodies only; never leak stacks to browsers ────────────────

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly publicMessage: string,
  ) {
    super(publicMessage);
    this.name = "ApiError";
  }
}

export function errorToResponse(error: unknown): Response {
  if (error instanceof ApiError) {
    return Response.json(
      { ok: false, error: error.publicMessage },
      { status: error.status },
    );
  }

  console.error("[api-error]", error);

  return Response.json(
    { ok: false, error: "Spirit backend failed" },
    { status: 500 },
  );
}
