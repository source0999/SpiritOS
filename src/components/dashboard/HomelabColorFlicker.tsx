"use client";

import { ThemeStrip } from "@/components/dashboard/ThemeStrip";

export function HomelabColorFlicker() {
  return (
    <div className="flex flex-col gap-1.5">
      <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-chalk/36">
        Color Flicker
      </p>
      <ThemeStrip />
    </div>
  );
}
