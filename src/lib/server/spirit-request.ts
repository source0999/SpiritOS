import "server-only";

import type { UIMessage } from "ai";

import { ApiError } from "@/lib/server/api-errors";

export type SpiritRequestBody = {
  messages: UIMessage[];
};

/** Pragmatic UIMessage-ish validation before convertToModelMessages. */
function assertMessagesShape(raw: unknown[]): void {
  for (let i = 0; i < raw.length; i++) {
    const m = raw[i];
    if (!m || typeof m !== "object") {
      throw new ApiError(400, "Each message must be an object");
    }
    const msg = m as Record<string, unknown>;
    if (typeof msg.role !== "string" || msg.role.length === 0) {
      throw new ApiError(400, "Each message must have a non-empty string role");
    }
    if (!Array.isArray(msg.parts)) {
      throw new ApiError(400, "Each message must include a parts array");
    }
  }
}

export async function readSpiritRequest(req: Request): Promise<SpiritRequestBody> {
  let body: unknown;

  try {
    body = await req.json();
  } catch {
    throw new ApiError(400, "Invalid JSON body");
  }

  if (!body || typeof body !== "object") {
    throw new ApiError(400, "Request body must be an object");
  }

  const maybeMessages = (body as { messages?: unknown }).messages;

  if (!Array.isArray(maybeMessages)) {
    throw new ApiError(400, "Request body must include messages[]");
  }

  if (maybeMessages.length === 0) {
    throw new ApiError(400, "messages[] cannot be empty");
  }

  assertMessagesShape(maybeMessages);

  return { messages: maybeMessages as UIMessage[] };
}
