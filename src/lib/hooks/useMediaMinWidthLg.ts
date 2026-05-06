"use client";

import { useEffect, useState } from "react";

/**
 * Tailwind `lg` breakpoint (1024px). **Hydration-safe:** server + first client paint use `false`
 * (narrow / mobile layout); real viewport is applied in `useEffect` only.
 * > The old useSyncExternalStore(..., () => true) lied on SSR — every phone hydrated as desktop.
 */
export function useMediaMinWidthLg(): boolean {
  const [isLg, setIsLg] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }
    const mq = window.matchMedia("(min-width: 1024px)");
    const apply = () => setIsLg(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  return isLg;
}
