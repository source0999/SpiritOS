// ── StageFallback — dynamic() loading shell (code-split stage bodies) ─────────
// > Phase 2: same chalk/mono language as the rest of the shell; not a redesign

export function StageFallback({ label = "Loading stage…" }: { label?: string }) {
  return (
    <div className="flex min-h-[50vh] flex-1 items-center justify-center p-6 font-mono text-xs text-chalk/45">
      {label}
    </div>
  );
}
