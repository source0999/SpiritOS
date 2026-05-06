import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const p = resolve(process.cwd(), "src/components/chat/SpiritChat.tsx");

describe("SpiritChat mobile composer (Prompt 9F)", () => {
  it("keeps iOS-safe font size and capped grow height on the message field", () => {
    const src = readFileSync(p, "utf8");
    expect(src).toContain("max-lg:text-base");
    expect(src).toContain("max-lg:max-h-[120px]");
  });

  it("scroll container has overscroll-y-contain on both variant branches", () => {
    const src = readFileSync(p, "utf8");
    const matches = src.match(/overscroll-y-contain/g) ?? [];
    expect(matches.length).toBeGreaterThanOrEqual(2);
  });

  it("composer wrapper does not use sticky positioning", () => {
    const src = readFileSync(p, "utf8");
    expect(src).not.toContain("sticky bottom-0 z-30");
  });

  it("standalone root uses fixed h-dvh height, not min-h-dvh that allows body scroll", () => {
    const src = readFileSync(p, "utf8");
    expect(src).not.toContain("min-h-dvh");
    expect(src).toContain("h-[100dvh]");
  });

  it("textarea declares overflow-y-auto for internal scroll at max height", () => {
    const src = readFileSync(p, "utf8");
    expect(src).toContain("overflow-y-auto");
  });
});
