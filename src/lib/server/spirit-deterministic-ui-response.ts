import "server-only";

import { createUIMessageStream, createUIMessageStreamResponse } from "ai";
import type { UIMessage } from "ai";

import type {
  SpiritAssistantMessageMetadata,
  SpiritToolActivityCard,
} from "@/lib/spirit/spirit-activity-events";
import { sanitizeForHttpByteStringHeader } from "@/lib/server/spirit-search-telemetry";

/** Same UI stream framing as LLM path - useChat / Oracle stay happy */
export function createDeterministicAssistantUIMessageResponse(opts: {
  text: string;
  originalMessages: UIMessage[];
  headers?: HeadersInit;
  /** Compact tool/workspace telemetry for assistant message metadata + optional headers */
  toolActivity?: SpiritToolActivityCard[];
}): Response {
  const body = opts.text;
  const meta: SpiritAssistantMessageMetadata | undefined =
    opts.toolActivity && opts.toolActivity.length > 0
      ? { spiritToolActivity: opts.toolActivity }
      : undefined;

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
      writer.write({
        type: "finish",
        finishReason: "stop",
        messageMetadata: meta,
      });
    },
  });

  const headers = new Headers(opts.headers ?? undefined);
  if (opts.toolActivity && opts.toolActivity.length > 0) {
    headers.set(
      "x-spirit-tool-activity-json",
      sanitizeForHttpByteStringHeader(JSON.stringify(opts.toolActivity)),
    );
  }

  return createUIMessageStreamResponse({
    stream,
    headers,
  });
}
