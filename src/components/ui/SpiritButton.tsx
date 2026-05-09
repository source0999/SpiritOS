// ── SpiritButton - cyan accent CTAs (hub Oracle link shares spiritPrimaryCtaClasses)
// > No Radix. Static classes only - Tailwind must see full strings.
import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/cn";

/** Use on `next/link` when you need the same pill as SpiritButton without asChild. */
export const spiritPrimaryCtaClasses =
  "inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-full border border-[color:color-mix(in_oklab,var(--spirit-accent)_40%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_12%,transparent)] px-6 font-mono text-sm font-semibold text-[color:var(--spirit-accent-strong)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40";

export type SpiritButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
};

export function SpiritButton({
  children,
  className,
  type = "button",
  ...props
}: SpiritButtonProps) {
  return (
    <button
      type={type}
      className={cn(spiritPrimaryCtaClasses, className)}
      {...props}
    >
      {children}
    </button>
  );
}
