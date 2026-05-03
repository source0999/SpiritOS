import {
  convertToModelMessages,
  streamText,
} from "ai";

import { ApiError, errorToResponse } from "@/lib/server/api-errors";
import { getSpiritModelId, ollamaOpenAI } from "@/lib/server/ollama";
import { getSpiritMaxOutputTokens } from "@/lib/server/spirit-diagnostics";
import { readSpiritRequest } from "@/lib/server/spirit-request";

// ── Spirit → Ollama ───────────────────────────────────────────────
// Native Ollama JSON API is LM v1; streamText wants v3. OpenAI-compat `/v1/chat/completions` bridges that gap.

export async function POST(req: Request) {
  try {
    console.log("[spirit-api] POST /api/spirit hit");

    const { messages: uiMessages } = await readSpiritRequest(req);

    let messages;
    try {
      messages = await convertToModelMessages(
        uiMessages.map((m) => {
          const { id, ...rest } = m;
          void id;
          return rest;
        }),
      );
    } catch {
      throw new ApiError(400, "Invalid message format");
    }

    const result = await streamText({
      model: ollamaOpenAI.chat(getSpiritModelId()),
      messages,
      temperature: 0.85,
      maxOutputTokens: getSpiritMaxOutputTokens(),
    });

    return result.toUIMessageStreamResponse();
  } catch (error) {
    return errorToResponse(error);
  }
}
