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

  it("workspace variant allows mobile overscroll chaining for iOS PTR (max-lg overscroll-y-auto)", () => {
    const src = readFileSync(p, "utf8");
    expect(src).toContain("max-lg:overscroll-y-auto");
    expect(src).toContain("lg:overscroll-y-contain");
  });

  it("standalone branch keeps overscroll-y-contain on the message scroller", () => {
    const src = readFileSync(p, "utf8");
    expect(src).toContain(
      "overscroll-y-contain pb-[calc(5rem+env(safe-area-inset-bottom,0px))]",
    );
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

  it("composer focus scrolls textarea into view with block nearest (no delayed messagesEnd jump)", () => {
    const src = readFileSync(p, "utf8");
    expect(src).toContain("composerTextareaRef");
    expect(src).toContain('block: "nearest"');
    expect(src).not.toMatch(/setTimeout\([^)]*280/);
  });

  it("workspace composer dock exposes data-testid for empty-thread regression checks", () => {
    const src = readFileSync(p, "utf8");
    expect(src).toContain('data-testid="spirit-composer-dock"');
  });
});
