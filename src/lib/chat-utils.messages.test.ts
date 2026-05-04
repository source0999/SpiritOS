import { describe, expect, it } from "vitest";

import {
  deleteUIMessageById,
  findPreviousUserMessage,
  updateUIMessageText,
} from "@/lib/chat-utils";
import type { UIMessage } from "ai";

function msg(
  id: string,
  role: "user" | "assistant",
  text: string,
): UIMessage {
  return {
    id,
    role,
    parts: [{ type: "text", text }],
  };
}

describe("chat-utils message helpers", () => {
  it("updateUIMessageText changes text part", () => {
    const rows: UIMessage[] = [msg("u1", "user", "hi")];
    const next = updateUIMessageText(rows, "u1", "yo");
    expect(next[0]!.parts).toEqual([{ type: "text", text: "yo" }]);
  });

  it("deleteUIMessageById removes one id", () => {
    const rows: UIMessage[] = [msg("a", "user", "1"), msg("b", "assistant", "2")];
    expect(deleteUIMessageById(rows, "a").map((m) => m.id)).toEqual(["b"]);
  });

  it("findPreviousUserMessage finds nearest previous user", () => {
    const rows: UIMessage[] = [
      msg("1", "user", "a"),
      msg("2", "assistant", "b"),
      msg("3", "user", "c"),
      msg("4", "assistant", "d"),
    ];
    expect(findPreviousUserMessage(rows, "4")?.id).toBe("3");
  });
});
