import { describe, expect, it, vi } from "vitest";

import { copyTextToClipboard } from "@/lib/clipboard";

describe("copyTextToClipboard", () => {
  it("uses clipboard API when available", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const r = await copyTextToClipboard("hello");
    expect(r).toEqual({ ok: true });
    expect(writeText).toHaveBeenCalledWith("hello");
  });

  it("does not throw when clipboard API is missing", async () => {
    const prev = navigator.clipboard;
    Object.defineProperty(navigator, "clipboard", { value: undefined, configurable: true });
    const r = await copyTextToClipboard("hello");
    expect(r.ok).toBe(false);
    Object.defineProperty(navigator, "clipboard", { value: prev, configurable: true });
  });
});
