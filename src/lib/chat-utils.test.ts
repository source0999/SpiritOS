import { describe, expect, it } from "vitest";
import type { UIMessage } from "ai";

import { dedupeUIMessagesById, textFromParts } from "./chat-utils";

function u(
  id: string,
  text: string,
  role: "user" | "assistant" = "user",
): UIMessage {
  return {
    id,
    role,
    parts: [{ type: "text", text }],
  };
}

describe("dedupeUIMessagesById", () => {
  it("removes duplicate ids while preserving first-seen order (last payload wins)", () => {
    const out = dedupeUIMessagesById([
      u("a", "first-a"),
      u("b", "bee"),
      u("a", "second-a"),
    ]);
    expect(out.map((m) => m.id)).toEqual(["a", "b"]);
    expect(textFromParts(out[0]!)).toBe("second-a");
    expect(textFromParts(out[1]!)).toBe("bee");
  });

  it("is a no-op when ids are already unique", () => {
    const rows = [u("1", "x"), u("2", "y")];
    expect(dedupeUIMessagesById(rows)).toEqual(rows);
  });
});
