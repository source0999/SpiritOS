"use client";

import { useSyncExternalStore } from "react";

/** `true` when viewport is at least Tailwind `lg` (1024px). SSR / no matchMedia → assume desktop. */
export function useMediaMinWidthLg(): boolean {
  return useSyncExternalStore(
    (onStoreChange) => {
      if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
        return () => {};
      }
      const mq = window.matchMedia("(min-width: 1024px)");
      mq.addEventListener("change", onStoreChange);
      return () => mq.removeEventListener("change", onStoreChange);
    },
    () => {
      if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
        return true;
      }
      return window.matchMedia("(min-width: 1024px)").matches;
    },
    () => true,
  );
}
