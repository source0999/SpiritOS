"use client";

// ── Clock — isolated tick so DashboardClient doesn’t repaint every second ───────
// > Extracted Phase 1: same markup/classes as the old header span, zero theme coupling

import { useEffect, useState } from "react";

export function Clock() {
  const [localTime, setLocalTime] = useState("12:00 PM");

  useEffect(() => {
    const tick = () => {
      try {
        setLocalTime(
          new Date().toLocaleTimeString(undefined, {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          }),
        );
      } catch {
        setLocalTime("12:00 PM");
      }
    };

    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, []);

  return (
    <span className="hidden font-mono text-[10px] tabular-nums text-chalk/45 sm:inline">
      {localTime}
    </span>
  );
}
