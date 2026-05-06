"use client";

// ── OracleOrbSprite - abstract energy orb (no CDN, no <img>) ────────────────────
// > Extracted from the coded demo; SVG ids scoped with useId() so two mounts don’t
// > fight over defs. No crosshair reticle, no tail - just orb + rings + wings.

import { useId, useMemo } from "react";

import type { OracleVisualState } from "@/lib/oracle/oracle-visual-state";

export type OracleOrbSpriteProps = {
  /** Drives motion intensity classes on the wrapper. */
  visualState?: OracleVisualState;
  /** Homelab card vs /oracle chamber sizing. */
  variant?: "widget" | "chamber";
  className?: string;
};

export function OracleOrbSprite({
  visualState = "idle",
  variant = "chamber",
  className = "",
}: OracleOrbSpriteProps) {
  const uid = useId().replace(/:/g, "");
  const gid = `o${uid}`;

  const motes = useMemo(() => {
    const n = variant === "widget" ? 14 : 24;
    return Array.from({ length: n }, (_, i) => ({
      id: i,
      cx: 160 + Math.sin(i * 1.31) * (variant === "widget" ? 86 : 112),
      cy: 154 + Math.cos(i * 1.77) * (variant === "widget" ? 64 : 92),
      r: 1.1 + (i % 4) * 0.65,
      delay: `${(i % 10) * 0.16}s`,
    }));
  }, [variant]);

  return (
    <div
      data-testid="oracle-orb-sprite"
      className={`oracle-orb-wrap oracle-orb-wrap--${variant} oracle-orb--${visualState} ${className}`.trim()}
      aria-label="Oracle sprite"
      role="img"
    >
      <svg className="oracle-orb-svg" viewBox="0 0 320 320" aria-hidden>
        <defs>
          <radialGradient id={`${gid}-core`} cx="42%" cy="35%" r="65%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="18%" stopColor="color-mix(in oklab, var(--spirit-accent-strong) 85%, white)" />
            <stop offset="46%" stopColor="var(--spirit-accent)" />
            <stop offset="82%" stopColor="color-mix(in oklab, var(--spirit-accent) 40%, transparent)" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
          <linearGradient
            id={`${gid}-wl`}
            x1="154"
            x2="28"
            y1="182"
            y2="78"
            gradientUnits="userSpaceOnUse"
          >
            <stop offset="0%" stopColor="color-mix(in oklab, var(--spirit-accent-strong) 55%, transparent)" />
            <stop offset="50%" stopColor="color-mix(in oklab, var(--spirit-accent) 28%, transparent)" />
            <stop offset="100%" stopColor="transparent" />
          </linearGradient>
          <linearGradient
            id={`${gid}-wr`}
            x1="166"
            x2="292"
            y1="182"
            y2="78"
            gradientUnits="userSpaceOnUse"
          >
            <stop offset="0%" stopColor="color-mix(in oklab, var(--spirit-accent-strong) 55%, transparent)" />
            <stop offset="50%" stopColor="color-mix(in oklab, var(--spirit-accent) 28%, transparent)" />
            <stop offset="100%" stopColor="transparent" />
          </linearGradient>
          <filter id={`${gid}-glow`} x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feColorMatrix
              in="blur"
              type="matrix"
              values="0 0 0 0 0.35  0 0 0 0 0.65  0 0 0 0 0.95  0 0 0 0.65 0"
              result="glow"
            />
            <feMerge>
              <feMergeNode in="glow" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <ellipse className="oracle-orb-orbit oracle-orb-orbit-a" cx="160" cy="158" rx="118" ry="52" />
        <ellipse className="oracle-orb-orbit oracle-orb-orbit-b" cx="160" cy="158" rx="88" ry="118" />
        <ellipse className="oracle-orb-orbit oracle-orb-orbit-c" cx="160" cy="158" rx="128" ry="78" />

        {motes.map((m) => (
          <circle
            key={m.id}
            className="oracle-orb-mote"
            cx={m.cx}
            cy={m.cy}
            r={m.r}
            style={{ animationDelay: m.delay }}
          />
        ))}

        <g className="oracle-orb-wing-l" filter={`url(#${gid}-glow)`}>
          <path
            className="oracle-orb-energy"
            fill={`url(#${gid}-wl)`}
            d="M154 182 C128 171 92 150 50 114 C32 98 20 80 14 66 C58 72 104 94 135 126 C150 144 154 162 154 182 Z"
          />
          <path className="oracle-orb-vein" d="M148 176 C124 148 92 113 34 70" />
          <path className="oracle-orb-vein oracle-orb-vein--thin" d="M138 161 C113 138 87 114 62 90" />
        </g>

        <g className="oracle-orb-wing-r" filter={`url(#${gid}-glow)`}>
          <path
            className="oracle-orb-energy"
            fill={`url(#${gid}-wr)`}
            d="M166 182 C192 171 228 150 270 114 C288 98 300 80 306 66 C262 72 216 94 185 126 C170 144 166 162 166 182 Z"
          />
          <path className="oracle-orb-vein" d="M172 176 C196 148 228 113 286 70" />
          <path className="oracle-orb-vein oracle-orb-vein--thin" d="M182 161 C207 138 233 114 258 90" />
        </g>

        <g className="oracle-orb-group" filter={`url(#${gid}-glow)`}>
          <circle className="oracle-orb-outer" cx="160" cy="158" r="40" fill={`url(#${gid}-core)`} />
          <circle className="oracle-orb-hot" cx="160" cy="158" r="7" />
        </g>
      </svg>
    </div>
  );
}
