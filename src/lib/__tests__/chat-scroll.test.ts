import { describe, expect, it } from "vitest";

import { DEFAULT_SCROLL_NEAR_BOTTOM_PX, isNearBottom } from "@/lib/chat-scroll";

function mockScrollEl(opts: {
  scrollHeight: number;
  scrollTop: number;
  clientHeight: number;
}): HTMLElement {
  const el = document.createElement("div");
  Object.defineProperties(el, {
    scrollHeight: { value: opts.scrollHeight, configurable: true },
    scrollTop: { value: opts.scrollTop, configurable: true },
    clientHeight: { value: opts.clientHeight, configurable: true },
  });
  return el;
}

describe("isNearBottom", () => {
  it("is true when gap to bottom is under threshold", () => {
    const el = mockScrollEl({ scrollHeight: 1000, scrollTop: 850, clientHeight: 100 });
    expect(isNearBottom(el, DEFAULT_SCROLL_NEAR_BOTTOM_PX)).toBe(true);
  });

  it("is false when user scrolled far from bottom", () => {
    const el = mockScrollEl({ scrollHeight: 1000, scrollTop: 0, clientHeight: 200 });
    expect(isNearBottom(el, DEFAULT_SCROLL_NEAR_BOTTOM_PX)).toBe(false);
  });

  it("treats missing scroll container as near-bottom (stickiness safe)", () => {
    expect(isNearBottom(null)).toBe(true);
    expect(isNearBottom(undefined)).toBe(true);
  });

  it("respects custom threshold", () => {
    const el = mockScrollEl({ scrollHeight: 500, scrollTop: 350, clientHeight: 100 });
    expect(isNearBottom(el, 60)).toBe(true);
    expect(isNearBottom(el, 40)).toBe(false);
  });
});
