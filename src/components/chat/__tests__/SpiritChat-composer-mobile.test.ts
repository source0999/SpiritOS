import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("SpiritChat mobile composer (Prompt 9F)", () => {
  it("keeps iOS-safe font size and capped grow height on the message field", () => {
    const p = resolve(process.cwd(), "src/components/chat/SpiritChat.tsx");
    const src = readFileSync(p, "utf8");
    expect(src).toContain("max-lg:text-base");
    expect(src).toContain("max-lg:max-h-[120px]");
  });
});
