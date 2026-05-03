// ── DiagnosticsPanel — live server-derived rail (RSC + client leaf for polling) ─
// > SpiritDiagnosticsLive owns the only /api/spirit/health poll — never stack SpiritHealthIndicator here.
// > Design language: _blueprints/design_system.md — mono metadata, cyan values
import { SpiritDiagnosticsLive } from "@/components/dashboard/SpiritDiagnosticsLive";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { cn } from "@/lib/cn";

export type DiagnosticsPanelProps = {
  className?: string;
};

export function DiagnosticsPanel({ className }: DiagnosticsPanelProps) {
  return (
    <aside
      className={cn(
        "glass flex min-h-0 w-full shrink-0 flex-col border-[color:var(--spirit-border)] lg:border-l lg:border-t-0 lg:backdrop-blur-xl",
        className,
      )}
      aria-label="System diagnostics (read-only)"
    >
      <div className="border-b border-[color:var(--spirit-border)] px-3 py-2.5 text-center sm:px-4">
        <SectionLabel className="tracking-[0.26em]">Diagnostics</SectionLabel>
        <p className="mt-0.5 truncate font-mono text-[10px] leading-snug text-chalk/38">
          /api/spirit/health · 20s
        </p>
      </div>
      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto p-3 px-4 pb-5 pt-3 sm:p-4 sm:px-5">
        <SpiritDiagnosticsLive />
      </div>
    </aside>
  );
}
