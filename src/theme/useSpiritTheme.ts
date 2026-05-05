"use client";

import { useCallback, useEffect, useState } from "react";
import {
  DEFAULT_THEME_ID,
  THEME_IDS,
  applySpiritPaletteDom,
  getPaletteById,
  normalizeStoredThemeId,
  type ThemeId,
} from "@/theme/spiritPalettes";

// ── ThemeEngine — registry drives data-theme, typography, and --spirit-* paint ─

const STORAGE_KEY = "spirit-os-theme-engine";

export type { ThemeId };

export function safeTheme(raw: unknown): ThemeId | null {
  try {
    if (typeof raw !== "string") return null;
    return normalizeStoredThemeId(raw);
  } catch {
    return null;
  }
}

function resolveThemeState(theme: unknown): ThemeId {
  try {
    if (typeof theme === "string" && THEME_IDS.has(theme)) {
      return theme as ThemeId;
    }
  } catch {
    /* malformed */
  }
  return DEFAULT_THEME_ID;
}

export function useSpiritTheme() {
  const [theme, setThemeState] = useState<ThemeId>(DEFAULT_THEME_ID);

  useEffect(() => {
    try {
      if (typeof window === "undefined") return;
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw != null) {
        queueMicrotask(() => setThemeState(normalizeStoredThemeId(raw)));
      }
    } catch {
      queueMicrotask(() => setThemeState(DEFAULT_THEME_ID));
    }
  }, []);

  useEffect(() => {
    try {
      const resolved = resolveThemeState(theme);
      if (resolved !== theme) {
        queueMicrotask(() => setThemeState(resolved));
        return;
      }

      try {
        if (typeof document !== "undefined") {
          applySpiritPaletteDom(document.documentElement, getPaletteById(resolved));
        }
      } catch {
        /* SSR / no DOM */
      }

      try {
        if (typeof window !== "undefined") {
          window.localStorage.setItem(STORAGE_KEY, resolved);
        }
      } catch {
        /* private mode / quota */
      }
    } catch {
      try {
        queueMicrotask(() => setThemeState(DEFAULT_THEME_ID));
        if (typeof document !== "undefined") {
          applySpiritPaletteDom(document.documentElement, getPaletteById(DEFAULT_THEME_ID));
        }
        if (typeof window !== "undefined") {
          try {
            window.localStorage.removeItem(STORAGE_KEY);
          } catch {
            /* ignore */
          }
        }
      } catch {
        if (typeof document !== "undefined") {
          applySpiritPaletteDom(document.documentElement, getPaletteById(DEFAULT_THEME_ID));
        }
        queueMicrotask(() => setThemeState(DEFAULT_THEME_ID));
      }
    }
  }, [theme]);

  const setTheme = useCallback((next: ThemeId) => {
    try {
      setThemeState(resolveThemeState(next));
    } catch {
      setThemeState(DEFAULT_THEME_ID);
    }
  }, []);

  return { theme, setTheme };
}
