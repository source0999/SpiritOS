import "server-only";

import { createUIMessageStream, createUIMessageStreamResponse } from "ai";
import type { UIMessage } from "ai";

/** Same UI stream framing as LLM path - useChat / Oracle stay happy */
export function createDeterministicAssistantUIMessageResponse(opts: {
  text: string;
  originalMessages: UIMessage[];
  headers?: HeadersInit;
}): Response {
  const body = opts.text;
  const stream = createUIMessageStream({
    originalMessages: opts.originalMessages,
    execute: ({ writer }) => {
      writer.write({ type: "start" });
      writer.write({ type: "start-step" });
      const textId = "text-1";
      writer.write({ type: "text-start", id: textId });
      writer.write({ type: "text-delta", id: textId, delta: body });
      writer.write({ type: "text-end", id: textId });
      writer.write({ type: "finish-step" });
      writer.write({ type: "finish", finishReason: "stop" });
    },
  });

  return createUIMessageStreamResponse({
    stream,
    headers: opts.headers,
  });
}
