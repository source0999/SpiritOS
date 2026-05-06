// ── chat-thread-format - sidebar timestamp labels (shared by folder + list rows) ─

export function formatThreadUpdatedLabel(updatedAt: number): string {
  const diffMs = Math.max(0, Date.now() - updatedAt);
  if (diffMs < 60_000) return "now";
  if (diffMs < 3_600_000) return `${Math.floor(diffMs / 60_000)}m ago`;
  if (diffMs < 86_400_000) return `${Math.floor(diffMs / 3_600_000)}h ago`;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(updatedAt);
}
