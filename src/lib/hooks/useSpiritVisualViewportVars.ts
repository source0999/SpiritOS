"use client";

// ── useSpiritVisualViewportVars - iOS Safari keyboard: layout viewport lies, VV doesn’t ─
// > 100dvh is cosplay on mobile WebKit. Drive shell height from visualViewport + rAF coalesce.
import { type RefObject, useEffect } from "react";

export type SpiritVisualViewportVarTarget = RefObject<HTMLElement | null>;

/**
 * Paints CSS custom properties on `ref.current` for mobile keyboard-safe layouts.
 * - `--spirit-visual-viewport-height` — visible height (px)
 * - `--spirit-keyboard-inset` — max(0, layout height − visible height − vv.offsetTop) (px)
 * - `--spirit-visual-offset-top` — visualViewport.offsetTop (px)
 */
export function useSpiritVisualViewportVars(
  ref: SpiritVisualViewportVarTarget,
  enabled = true,
): void {
  useEffect(() => {
    if (!enabled || typeof window === "undefined") return;
    const el = ref.current;
    if (!el) return;

    let raf = 0;

    const apply = () => {
      const innerH = window.innerHeight;
      const vv = window.visualViewport;
      if (!vv) {
        el.style.setProperty("--spirit-visual-viewport-height", `${innerH}px`);
        el.style.setProperty("--spirit-keyboard-inset", "0px");
        el.style.setProperty("--spirit-visual-offset-top", "0px");
        return;
      }
      const vh = vv.height;
      const offsetTop = vv.offsetTop;
      const keyboardInset = Math.max(0, innerH - vh - offsetTop);
      el.style.setProperty("--spirit-visual-viewport-height", `${vh}px`);
      el.style.setProperty("--spirit-keyboard-inset", `${keyboardInset}px`);
      el.style.setProperty("--spirit-visual-offset-top", `${offsetTop}px`);
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
}
