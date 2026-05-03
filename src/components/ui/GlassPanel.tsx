// ── GlassPanel — default glass/card seam (static Tailwind, zero cleverness) ────
// > Extracted from: Hub + Oracle repeated glass/border/bg triplets
// > Design language: _blueprints/design_system.md — spirit-border, chalk void
import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

/** Full literal string so Tailwind JIT + motion wrappers can reuse without duplicating. */
export const glassPanelSurfaceClasses =
  "glass rounded-2xl border border-[color:var(--spirit-border)] bg-white/[0.02]";

type GlassPanelProps = {
  as?: "div" | "section" | "aside" | "article";
  children: ReactNode;
  className?: string;
} & HTMLAttributes<HTMLElement>;

export function GlassPanel({
  as: Tag = "div",
  children,
  className,
  ...props
}: GlassPanelProps) {
  return (
    <Tag className={cn(glassPanelSurfaceClasses, className)} {...props}>
      {children}
    </Tag>
  );
}
