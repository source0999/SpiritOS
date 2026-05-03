"use client";

import { useCallback, useEffect, useState } from "react";

// ── ThemeEngine — palettes on --spirit-* vars; bad storage/CSS never blanks UI ─

export type ThemeId = "spirit-slate" | "dark-node" | "legacy-violet";

const STORAGE_KEY = "spirit-os-theme-engine";

/** Spirit Cyan lane — canonical fallback when storage/DOM coercion fails */
const SPIRIT_CYAN_THEME: ThemeId = "spirit-slate";

const THEMES = new Set<ThemeId>([
  "spirit-slate",
  "dark-node",
  "legacy-violet",
]);

export function safeTheme(raw: unknown): ThemeId | null {
  try {
    if (typeof raw !== "string") return null;
    if (THEMES.has(raw as ThemeId)) return raw as ThemeId;
    return null;
  } catch {
    return null;
  }
}

function resolveTheme(theme: unknown): ThemeId {
  try {
    if (typeof theme === "string" && THEMES.has(theme as ThemeId)) {
      return theme as ThemeId;
    }
  } catch {
    /* malformed — fall through */
  }
  return SPIRIT_CYAN_THEME;
}

function applyDataTheme(theme: ThemeId): void {
  try {
    if (typeof document === "undefined") return;
    document.documentElement.setAttribute("data-theme", theme);
  } catch {
    /* SSR / stripped DOM — caller may recover via fallback */
  }
}

export function useSpiritTheme() {
  const [theme, setThemeState] = useState<ThemeId>(SPIRIT_CYAN_THEME);

  useEffect(() => {
    try {
      if (typeof window === "undefined") return;
      const raw = window.localStorage.getItem(STORAGE_KEY);
      const t = safeTheme(raw);
      if (t) queueMicrotask(() => setThemeState(t));
    } catch {
      queueMicrotask(() => setThemeState(SPIRIT_CYAN_THEME));
    }
  }, []);

  useEffect(() => {
    try {
      const resolved = resolveTheme(theme);
      if (resolved !== theme) {
        queueMicrotask(() => setThemeState(resolved));
        return;
      }

      applyDataTheme(resolved);

      try {
        if (typeof window !== "undefined") {
          window.localStorage.setItem(STORAGE_KEY, resolved);
        }
      } catch {
        /* storage quotas / private windows */
      }
    } catch {
      try {
        queueMicrotask(() => setThemeState(SPIRIT_CYAN_THEME));
        applyDataTheme(SPIRIT_CYAN_THEME);
        if (typeof window !== "undefined") {
          try {
            window.localStorage.removeItem(STORAGE_KEY);
          } catch {
            /* ignore */
          }
        }
      } catch {
        applyDataTheme(SPIRIT_CYAN_THEME);
        queueMicrotask(() => setThemeState(SPIRIT_CYAN_THEME));
      }
    }
  }, [theme]);

  const setTheme = useCallback((next: ThemeId) => {
    try {
      const resolved = safeTheme(next) ?? SPIRIT_CYAN_THEME;
      setThemeState(resolved);
    } catch {
      setThemeState(SPIRIT_CYAN_THEME);
    }
  }, []);

  return { theme, setTheme };
}
