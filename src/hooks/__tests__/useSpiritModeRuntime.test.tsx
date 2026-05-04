import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { useSpiritModeRuntime } from "@/hooks/useSpiritModeRuntime";
import { DEFAULT_MODEL_PROFILE_ID } from "@/lib/spirit/model-profile.types";

describe("useSpiritModeRuntime (Prompt 10D)", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it("defaults to Peer when persistence is off (Oracle-style)", () => {
    const { result } = renderHook(() =>
      useSpiritModeRuntime({
        runtimeSurface: "oracle",
        persistenceEnabled: false,
        threadRuntime: {
          activeModelProfileId: "teacher",
          setActiveModelProfile: async () => {},
        },
      }),
    );
    expect(result.current.activeModelProfileId).toBe(DEFAULT_MODEL_PROFILE_ID);
    expect(result.current.requestBodyModeFields.runtimeSurface).toBe("oracle");
    expect(result.current.requestBodyModeFields.modelProfileId).toBe(
      DEFAULT_MODEL_PROFILE_ID,
    );
  });

  it("updates ephemeral profile when persistence is off", () => {
    const { result } = renderHook(() =>
      useSpiritModeRuntime({
        runtimeSurface: "oracle",
        persistenceEnabled: false,
        threadRuntime: {
          activeModelProfileId: "normal-peer",
          setActiveModelProfile: async () => {},
        },
      }),
    );
    act(() => {
      void result.current.setActiveModelProfile("teacher");
    });
    expect(result.current.activeModelProfileId).toBe("teacher");
    expect(result.current.requestBodyModeFields.modelProfileId).toBe("teacher");
  });
});
