// ── Dashboard route group —──────────────────────────────────────────────
// URL: / (groups do not pollute the path). Quarantine lives at /quarantine
// because two group-level page.tsx files cannot both claim / — physics wins.

export default function DashboardGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
