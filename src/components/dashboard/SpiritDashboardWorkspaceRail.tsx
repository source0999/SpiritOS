import Link from "next/link";
import { MessageCircle, Sparkles } from "lucide-react";

import { cn } from "@/lib/cn";

type Props = { className?: string };

export function SpiritDashboardWorkspaceRail({ className }: Props) {
  const linkClass =
    "flex min-h-[48px] touch-manipulation items-center justify-center gap-2 rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-glass-border)_55%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg-soft)_32%,transparent)] px-4 py-3 font-mono text-[10px] font-semibold uppercase tracking-wider text-chalk/78 transition hover:border-[color:color-mix(in_oklab,var(--spirit-accent)_35%,transparent)] hover:text-chalk active:scale-[0.99] sm:min-h-0 sm:justify-start sm:py-2.5";

  return (
    <aside
      aria-label="Workspace shortcuts"
      className={cn(
        "spirit-dashboard-v2-glass flex flex-col gap-3 p-4 sm:p-5",
        className,
      )}
    >
      <div>
        <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-chalk/45">
          Workspace
        </p>
        <h2 className="mt-0.5 font-mono text-[13px] font-semibold uppercase tracking-tight text-chalk">
          Quick links
        </h2>
        <p className="mt-1 font-mono text-[9px] leading-relaxed text-chalk/38">
          Static shortcuts — same routes as the left rail. No extra telemetry.
        </p>
      </div>
      <div className="flex flex-col gap-2">
        <Link href="/chat" className={linkClass}>
          <MessageCircle className="h-4 w-4 shrink-0 text-chalk/55" aria-hidden />
          Open Chat
        </Link>
        <Link href="/oracle" className={linkClass}>
          <Sparkles className="h-4 w-4 shrink-0 text-chalk/55" aria-hidden />
          Open Oracle
        </Link>
      </div>
    </aside>
  );
}
