import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

/** Glass panel for dashboard grid — shallow depth, not a padded cell block. */
export function DashboardWidgetCard({
  title,
  subtitle,
  className,
  children,
}: {
  title: string;
  subtitle?: string;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "flex min-h-[10rem] flex-col rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-border)_80%,transparent)] bg-white/[0.03] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] backdrop-blur-md",
        className,
      )}
    >
      <h2 className="font-mono text-[11px] font-semibold uppercase tracking-[0.2em] text-[color:color-mix(in_oklab,var(--spirit-accent-strong)_88%,transparent)]">
        {title}
      </h2>
      {subtitle ? (
        <p className="mt-2 flex-1 font-mono text-xs leading-relaxed text-chalk/52">
          {subtitle}
        </p>
      ) : null}
      {children ? <div className={cn(subtitle ? "mt-6" : "mt-4")}>{children}</div> : null}
    </section>
  );
}
