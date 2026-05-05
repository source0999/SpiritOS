import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import { useSpiritTheme } from "../useSpiritTheme";
import {
  DEFAULT_THEME_ID,
  SPIRIT_DOM_CSS_KEYS,
  normalizeStoredThemeId,
} from "../spiritPalettes";

const STORAGE_KEY = "spirit-os-theme-engine";

describe("useSpiritTheme", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    document.documentElement.removeAttribute("data-spirit-typography");
    for (const key of SPIRIT_DOM_CSS_KEYS) {
      document.documentElement.style.removeProperty(key);
    }
  });

  it("defaults to frozen-water", () => {
    const { result } = renderHook(() => useSpiritTheme());
    expect(result.current.theme).toBe(DEFAULT_THEME_ID);
  });

  it("migrates spirit-slate to frozen-water", async () => {
    localStorage.setItem(STORAGE_KEY, "spirit-slate");
    const { result } = renderHook(() => useSpiritTheme());
    await waitFor(() => expect(result.current.theme).toBe("frozen-water"));
    expect(normalizeStoredThemeId("spirit-slate")).toBe("frozen-water");
  });

  it("migrates dark-node to alice-seagrass", async () => {
    localStorage.setItem(STORAGE_KEY, "dark-node");
    const { result } = renderHook(() => useSpiritTheme());
    await waitFor(() => expect(result.current.theme).toBe("alice-seagrass"));
  });

  it("migrates legacy-violet to violet-twilight", async () => {
    localStorage.setItem(STORAGE_KEY, "legacy-violet");
    const { result } = renderHook(() => useSpiritTheme());
    await waitFor(() => expect(result.current.theme).toBe("violet-twilight"));
  });

  it("falls back to frozen-water for garbage storage", async () => {
    localStorage.setItem(STORAGE_KEY, "totally-not-a-theme");
    const { result } = renderHook(() => useSpiritTheme());
    await waitFor(() => expect(result.current.theme).toBe(DEFAULT_THEME_ID));
  });

  it("writes CSS vars and data attributes onto documentElement", async () => {
    renderHook(() => useSpiritTheme());
    await waitFor(() =>
      expect(document.documentElement.getAttribute("data-theme")).toBe(DEFAULT_THEME_ID),
    );
    expect(document.documentElement.style.getPropertyValue("--spirit-accent")).not.toBe("");
  });
});
