// ── Quarantine route group —─────────────────────────────────────────────
// > Design language: _blueprints/design_system.md — higher contrast, rose seam
// Shell only; page lives at /quarantine so / stays the dashboard.

export default function QuarantineGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-dvh border-x-4 border-rose/60 bg-ink shadow-quarantine-inset">
      {children}
    </div>
  );
}
