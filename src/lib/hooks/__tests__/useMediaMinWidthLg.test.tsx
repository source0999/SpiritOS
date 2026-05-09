import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useMediaMinWidthLg } from "../useMediaMinWidthLg";

function mockMatchMedia(matches: boolean) {
  const mq = {
    matches,
    media: "(min-width: 1024px)",
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  };
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockImplementation(() => mq),
  );
  return mq;
}

describe("useMediaMinWidthLg", () => {
  beforeEach(() => {
    vi.stubGlobal("matchMedia", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("implementation reads matchMedia during first client render to avoid desktop chrome flash", () => {
    const p = resolve(process.cwd(), "src/lib/hooks/useMediaMinWidthLg.ts");
    const src = readFileSync(p, "utf8");
    expect(src).toContain("useState(() =>");
    expect(src).toContain('window.matchMedia("(min-width: 1024px)").matches');
  });

  it("syncs to wide viewport after mount", async () => {
    mockMatchMedia(true);
    const { result } = renderHook(() => useMediaMinWidthLg());
    await waitFor(() => expect(result.current).toBe(true));
  });

  it("syncs to narrow viewport after mount", async () => {
    mockMatchMedia(false);
    const { result } = renderHook(() => useMediaMinWidthLg());
    await waitFor(() => expect(result.current).toBe(false));
  });
});
