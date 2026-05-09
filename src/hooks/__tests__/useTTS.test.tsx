import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { useTTS } from "@/hooks/useTTS";

describe("useTTS (Prompt 9G)", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it("hydrates isEnabled from localStorage after mount (stable first paint)", async () => {
    window.localStorage.setItem("spirit:ttsEnabled", "1");
    const { result } = renderHook(() => useTTS());
    expect(result.current.state.isEnabled).toBe(false);
    await waitFor(() => {
      expect(result.current.state.isEnabled).toBe(true);
    });
  });

  it("hydrates voiceSpeed from localStorage after mount", async () => {
    window.localStorage.setItem("spirit:ttsVoiceSpeed", "1.18");
    const { result } = renderHook(() => useTTS());
    expect(result.current.state.voiceSpeed).toBeCloseTo(1.12, 5);
    await waitFor(() => {
      expect(result.current.state.voiceSpeed).toBeCloseTo(1.18, 5);
    });
  });

  it("setVoiceSpeed persists to localStorage", async () => {
    const { result } = renderHook(() => useTTS());
    await waitFor(() => {
      expect(result.current.state.isEnabled).toBe(false);
    });
    act(() => {
      result.current.setVoiceSpeed(1.08);
    });
    expect(result.current.state.voiceSpeed).toBeCloseTo(1.08, 5);
    expect(window.localStorage.getItem("spirit:ttsVoiceSpeed")).toBe("1.08");
  });
});
