// ── SectionLabel — mono uppercase rail labels (panels, cards, dl rows) ────────
// > Extracted from: Diagnostics, Hub cards, Oracle panel — stop paste-widest hell
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export const sectionLabelClasses =
  "font-mono text-[10px] font-semibold uppercase tracking-widest text-chalk/45";

type SectionLabelProps = {
  as?: "p" | "span" | "dt";
  children: ReactNode;
  className?: string;
};

export function SectionLabel({
  as: Tag = "p",
  children,
  className,
}: SectionLabelProps) {
  return (
    <Tag className={cn(sectionLabelClasses, className)}>{children}</Tag>
  );
}
