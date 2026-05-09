import { describe, expect, it } from "vitest";

import { buildTitleFromText } from "@/lib/chat-persistence";

describe("buildTitleFromText", () => {
  it("returns New chat when empty or whitespace", () => {
    expect(buildTitleFromText("")).toBe("New chat");
    expect(buildTitleFromText("   \n")).toBe("New chat");
  });

  it("squashes whitespace to single spaces", () => {
    expect(buildTitleFromText("  hello   world\t")).toBe("hello world");
  });

  it("truncates beyond 42 characters", () => {
    expect(buildTitleFromText("a".repeat(50))).toHaveLength(42);
  });
});
