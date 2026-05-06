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

  it("implementation keeps useState(false) for SSR / first paint (grep contract)", () => {
    const p = resolve(process.cwd(), "src/lib/hooks/useMediaMinWidthLg.ts");
    expect(readFileSync(p, "utf8")).toContain("useState(false)");
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
