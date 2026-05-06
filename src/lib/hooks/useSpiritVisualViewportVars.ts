"use client";

// ── useSpiritVisualViewportVars - iOS Safari keyboard: layout viewport lies, VV doesn’t ─
// > 100dvh is cosplay on mobile WebKit. Drive shell height from visualViewport + rAF coalesce.
// > Keyboard inset state is effect-only — safe for SSR (starts at 0).
import { type RefObject, useEffect, useRef, useState } from "react";

export type SpiritVisualViewportVarTarget = RefObject<HTMLElement | null>;

export type SpiritVisualViewportMetrics = {
  /** Rounded px; updated from visualViewport inside useEffect only. */
  keyboardInsetPx: number;
};

/**
 * Paints CSS custom properties on `ref.current` for mobile keyboard-safe layouts.
 * - `--spirit-visual-viewport-height` — visible height (px)
 * - `--spirit-keyboard-inset` — max(0, layout height − visible height − vv.offsetTop) (px)
 * - `--spirit-visual-offset-top` — visualViewport.offsetTop (px)
 */
export function useSpiritVisualViewportVars(
  ref: SpiritVisualViewportVarTarget,
  enabled = true,
): SpiritVisualViewportMetrics {
  const [keyboardInsetPx, setKeyboardInsetPx] = useState(0);
  const lastInsetRef = useRef(0);

  useEffect(() => {
    if (!enabled || typeof window === "undefined") return;
    const el = ref.current;
    if (!el) return;

    let raf = 0;

    const apply = () => {
      const innerH = window.innerHeight;
      const vv = window.visualViewport;
      let vh = innerH;
      let offsetTop = 0;
      let keyboardInset = 0;
      if (vv) {
        vh = vv.height;
        offsetTop = vv.offsetTop;
        keyboardInset = Math.max(0, innerH - vh - offsetTop);
      }
      el.style.setProperty("--spirit-visual-viewport-height", `${vh}px`);
      el.style.setProperty("--spirit-keyboard-inset", `${keyboardInset}px`);
      el.style.setProperty("--spirit-visual-offset-top", `${offsetTop}px`);

      const rounded = Math.round(keyboardInset);
      if (rounded !== lastInsetRef.current) {
        lastInsetRef.current = rounded;
        setKeyboardInsetPx(rounded);
      }
    };

    const schedule = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(apply);
    };

    schedule();

    const vv = window.visualViewport;
    vv?.addEventListener("resize", schedule);
    vv?.addEventListener("scroll", schedule);
    window.addEventListener("resize", schedule);
    window.addEventListener("orientationchange", schedule);
    document.addEventListener("focusin", schedule);
    document.addEventListener("focusout", schedule);

    return () => {
      cancelAnimationFrame(raf);
      vv?.removeEventListener("resize", schedule);
      vv?.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
      window.removeEventListener("orientationchange", schedule);
      document.removeEventListener("focusin", schedule);
      document.removeEventListener("focusout", schedule);
    };
  }, [ref, enabled]);

  return { keyboardInsetPx };
}
