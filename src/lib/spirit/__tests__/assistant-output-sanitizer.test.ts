import { describe, expect, it } from "vitest";

import { sanitizeAssistantVisibleText } from "@/lib/spirit/assistant-output-sanitizer";

describe("sanitizeAssistantVisibleText", () => {
  it("removes redacted_thinking blocks", () => {
    const open = "<" + "redacted_thinking" + ">";
    const close = "<" + "/" + "redacted_thinking" + ">";
    const t = ["Hello", open, 'Respond in "Sassy mode" only', "Keep sentences short", close, "World"].join("\n");
    expect(sanitizeAssistantVisibleText(t)).toBe("Hello\n\nWorld");
  });

  it("removes leaked Sassy contract lines", () => {
    const t = `Go touch grass.

Respond in "Sassy mode" only
Keep sentences short
No hidden chain-of-thought

Actually: fine.`;
    expect(sanitizeAssistantVisibleText(t)).not.toContain("Sassy mode");
    expect(sanitizeAssistantVisibleText(t)).toContain("touch grass");
    expect(sanitizeAssistantVisibleText(t)).toContain("Actually: fine.");
  });

  it("removes leaked Brutal contract lines", () => {
    const t = `Truth here.

Respond in "Brutal mode" only
Mode contract:

Do the thing.`;
    expect(sanitizeAssistantVisibleText(t)).not.toContain("Brutal mode");
    expect(sanitizeAssistantVisibleText(t)).toContain("Truth here");
  });

  it("keeps normal text that mentions thinking in prose", () => {
    const t = "I think we should refactor the module.";
    expect(sanitizeAssistantVisibleText(t)).toBe(t);
  });
});
