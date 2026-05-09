// ── Dashboard route group — `/` only (chat/oracle live outside this layout) ────
// No visual shell here. The dashboard owns its real surfaces; no fake slab wrapper.

export default function DashboardGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
