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
 * - `--spirit-visual-viewport-height` — `visualViewport.height` when keyboard is open; when the
 *   keyboard lane is idle, **pinned to `window.innerHeight`** (same as vv on stable loads, but
 *   we stop listening to VV resize/scroll so iOS PTR rubber-band cannot spam `apply()`).
 * - `--spirit-keyboard-inset` — max(0, layout height − visible height − vv.offsetTop)
 * - `--spirit-visual-offset-top` — raw offset **clamped to 0** when keyboard lane is idle
 *
 * **PTR / rubber-band:** (1) `visualViewport` `resize`/`scroll` listeners stay detached while the
 * keyboard lane is idle. (2) Inset must stay ≥ 14px for **50ms** before we treat the lane as
 * active (ignores one-frame PTR spikes). (3) Identical CSS triple + lane state skips redundant
 * `setProperty` when `window.resize` fires in a tight loop.
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

    const vv = window.visualViewport ?? null;
    let raf = 0;
    let vvListenersAttached = false;
    /** Sustained inset before we treat the keyboard lane as active (avoids PTR spikes). */
    let keyboardLaneActive = false;
    let armKbTimer: number | null = null;
    let lastStyleTriple = "";

    const clearKbArmTimer = () => {
      if (armKbTimer != null) {
        window.clearTimeout(armKbTimer);
        armKbTimer = null;
      }
    };

    const schedule = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(apply);
    };

    const onWinResize = () => schedule();
    const onOrientation = () => schedule();
    const onFocusIn = () => schedule();
    const onFocusOut = () => schedule();
    const onVvResize = () => schedule();
    const onVvScroll = () => schedule();

    const setVvListeners = (laneIdle: boolean) => {
      if (!vv) return;
      if (laneIdle && vvListenersAttached) {
        vv.removeEventListener("resize", onVvResize);
        vv.removeEventListener("scroll", onVvScroll);
        vvListenersAttached = false;
      } else if (!laneIdle && !vvListenersAttached) {
        vv.addEventListener("resize", onVvResize);
        vv.addEventListener("scroll", onVvScroll);
        vvListenersAttached = true;
      }
    };

    function apply() {
      const node = ref.current;
      if (!node) return;
      const innerH = window.innerHeight;
      let vh = innerH;
      let offsetTop = 0;
      let keyboardInset = 0;
      let rawOffsetTop = 0;
      if (vv) {
        vh = vv.height;
        rawOffsetTop = vv.offsetTop;
        keyboardInset = Math.max(0, innerH - vh - rawOffsetTop);
        offsetTop = keyboardInset < 14 ? 0 : rawOffsetTop;
      }

      // ── Keyboard lane hysteresis: PTR can briefly inflate inset without a real keyboard.
      // Require inset ≥ 14 for 50ms before attaching VV / switching to vv.height paint path.
      if (keyboardInset < 14) {
        clearKbArmTimer();
        if (keyboardLaneActive) {
          keyboardLaneActive = false;
        }
      } else if (!keyboardLaneActive && armKbTimer == null) {
        armKbTimer = window.setTimeout(() => {
          armKbTimer = null;
          if (!vv) return;
          const ih = window.innerHeight;
          const insNow = Math.max(0, ih - vv.height - vv.offsetTop);
          if (insNow >= 14) {
            keyboardLaneActive = true;
            schedule();
          }
        }, 50);
      }

      const keyboardLaneIdle = !keyboardLaneActive;
      const paintVh = keyboardLaneIdle ? innerH : vh;

      const styleTriple = `${paintVh}|${keyboardInset}|${offsetTop}|${keyboardLaneActive ? 1 : 0}`;
      if (styleTriple === lastStyleTriple) {
        return;
      }
      lastStyleTriple = styleTriple;

      node.style.setProperty("--spirit-visual-viewport-height", `${paintVh}px`);
      node.style.setProperty("--spirit-keyboard-inset", `${keyboardInset}px`);
      node.style.setProperty("--spirit-visual-offset-top", `${offsetTop}px`);

      setVvListeners(keyboardLaneIdle);

      const rounded = Math.round(keyboardInset);
      if (rounded !== lastInsetRef.current) {
        lastInsetRef.current = rounded;
        setKeyboardInsetPx(rounded);
      }
    }

    window.addEventListener("resize", onWinResize);
    window.addEventListener("orientationchange", onOrientation);
    document.addEventListener("focusin", onFocusIn);
    document.addEventListener("focusout", onFocusOut);

    schedule();

    return () => {
      clearKbArmTimer();
      cancelAnimationFrame(raf);
      if (vv && vvListenersAttached) {
        vv.removeEventListener("resize", onVvResize);
        vv.removeEventListener("scroll", onVvScroll);
        vvListenersAttached = false;
      }
      window.removeEventListener("resize", onWinResize);
      window.removeEventListener("orientationchange", onOrientation);
      document.removeEventListener("focusin", onFocusIn);
      document.removeEventListener("focusout", onFocusOut);
    };
  }, [ref, enabled]);

  return { keyboardInsetPx };
}
