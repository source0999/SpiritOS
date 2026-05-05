"use client";

// ── OracleVoiceVisualizer — state-driven bars (+ optional mic level) ─────────────
// > Decorative lane: parent supplies `OracleVisualState` from live session logic.

import type { CSSProperties } from "react";
import { useMemo } from "react";

import type { OracleVisualState } from "@/lib/oracle/oracle-visual-state";

export type OracleVoiceVisualizerProps = {
  state: OracleVisualState;
  compact?: boolean;
  /** 0–1 live mic RMS when parent exposes it (e.g. Oracle page while recording). */
  audioLevel?: number;
  className?: string;
};

export function OracleVoiceVisualizer({
  state,
  compact = false,
  audioLevel,
  className = "",
}: OracleVoiceVisualizerProps) {
  const bars = useMemo(() => {
    const n = compact ? 18 : 26;
    return Array.from({ length: n }, (_, i) => ({
      id: i,
      h: 8 + ((i * 9) % (compact ? 18 : 30)),
      delay: `${(i % 9) * 0.052}s`,
    }));
  }, [compact]);

  const level = typeof audioLevel === "number" ? Math.min(1, Math.max(0, audioLevel)) : null;
  const levelBoost =
    state === "listening" || state === "processing" || state === "speaking";

  return (
    <div
      data-testid="oracle-voice-visualizer"
      className={`oracle-viz oracle-viz--${state} ${compact ? "oracle-viz--compact" : ""} ${className}`.trim()}
      aria-label="Oracle voice activity"
      role="img"
    >
      {bars.map((b) => {
        let h = b.h;
        if (level != null && levelBoost) {
          const wobble = 0.55 + level * 0.95 + ((b.id % 5) * 0.04 - 0.08);
          h = Math.max(5, Math.round(b.h * wobble));
        }
        return (
          <span
            key={b.id}
            className="oracle-viz__bar"
            style={
              {
                height: `${h}px`,
                animationDelay: b.delay,
              } as CSSProperties
            }
          />
        );
      })}
    </div>
  );
}
