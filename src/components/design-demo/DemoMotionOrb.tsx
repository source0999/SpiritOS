// ── DemoMotionOrb — Oracle orb visual (CSS-driven, reduced-motion aware) ──────
// > Visual-only. The real Oracle voice loop lives in /oracle and is untouched.
// > All animation is CSS in spirit-demo.effects.css + spirit-demo.animations.css.
// > Decorative — marked aria-hidden; surrounding components carry the labels.
import type { CSSProperties } from "react";

export type DemoMotionOrbProps = {
  /** Diameter constraint via inline style; defaults to CSS clamp on container. */
  size?: string;
  className?: string;
};

export function DemoMotionOrb({ size, className }: DemoMotionOrbProps) {
  const style: CSSProperties | undefined = size ? { width: size } : undefined;

  return (
    <div
      className={`demo-orb${className ? ` ${className}` : ""}`}
      style={style}
      aria-hidden="true"
    >
      <span className="demo-orb__halo" />
      <span className="demo-orb__ring demo-orb__ring--3" />
      <span className="demo-orb__ring demo-orb__ring--2" />
      <span className="demo-orb__ring demo-orb__ring--1" />
      <span className="demo-orb__core" />
    </div>
  );
}

export default DemoMotionOrb;
