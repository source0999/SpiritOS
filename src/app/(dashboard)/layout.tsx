// ── Dashboard route group —──────────────────────────────────────────────
// URL: / (groups do not pollute the path).

export default function DashboardGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
