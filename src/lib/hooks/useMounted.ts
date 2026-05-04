"use client";

import { useEffect, useState } from "react";

/** True only after mount — use to avoid hydration / localStorage text mismatches. */
export function useMounted(): boolean {
  const [m, setM] = useState(false);
  useEffect(() => {
    queueMicrotask(() => setM(true));
  }, []);
  return m;
}
