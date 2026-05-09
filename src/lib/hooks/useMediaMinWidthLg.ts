"use client";

import { useEffect, useState } from "react";

/**
 * Tailwind `lg` breakpoint (1024px). The first client render reads matchMedia so
 * desktop does not flash the mobile chat chrome on reload.
 */
export function useMediaMinWidthLg(): boolean {
  const [isLg, setIsLg] = useState(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return false;
    }
    return window.matchMedia("(min-width: 1024px)").matches;
  });

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
