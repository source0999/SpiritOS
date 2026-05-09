import type { CSSProperties } from "react";

interface HomelabProgressBarProps {
  pct: number;
  variant?: "default" | "good" | "warn" | "bad";
  label?: string;
}

export function HomelabProgressBar({
  pct,
  variant = "default",
  label,
}: HomelabProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, pct));
  const fillVariant =
    variant === "default" ? "" : `homelab-progress-fill--${variant}`;

  return (
    <div
      className="homelab-progress"
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
      style={{ "--hl-pct": `${clamped}%` } as CSSProperties}
    >
      <div
        className={`homelab-progress-fill ${fillVariant}`.trim()}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
