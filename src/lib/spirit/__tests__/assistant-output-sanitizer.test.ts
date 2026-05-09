/// <reference types="vitest/globals" />

import { sanitizeAssistantVisibleText } from "@/lib/spirit/assistant-output-sanitizer";

describe("sanitizeAssistantVisibleText", () => {
  it("removes redacted_thinking blocks", () => {
    const open = "<" + "redacted_thinking" + ">";
    const close = "<" + "/" + "redacted_thinking" + ">";
    const t = ["Hello", open, 'Respond in "Sassy mode" only', "Keep sentences short", close, "World"].join("\n");
    expect(sanitizeAssistantVisibleText(t)).toBe("Hello\n\nWorld");
  });

  it("unwraps leaked visible chat_message container tags", () => {
    const t = `<chat_message> It could be a lot of things.

A hot engine stalling is never good. </chat_message>`;
    expect(sanitizeAssistantVisibleText(t)).toBe(
      "It could be a lot of things.\n\nA hot engine stalling is never good.",
    );
  });

  it("unwraps assistant_response container tags without removing inner text", () => {
    const t = `<assistant_response tone="peer">Check the actual error first.</assistant_response>`;
    expect(sanitizeAssistantVisibleText(t)).toBe("Check the actual error first.");
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

  it("removes leaked coding-assistant customer-service line", () => {
    const t = `Hey.

I'm here to help with coding questions

So anyway: drink water.`;
    const out = sanitizeAssistantVisibleText(t);
    expect(out).not.toContain("coding questions");
    expect(out).toContain("drink water");
  });

  it("keeps normal text that mentions thinking in prose", () => {
    const t = "I think we should refactor the module.";
    expect(sanitizeAssistantVisibleText(t)).toBe(t);
  });
});
