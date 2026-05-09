import type { ReactNode } from "react";

type BadgeVariant = "live" | "pending" | "mock" | "offline" | "ready";

interface HomelabStatusBadgeProps {
  variant: BadgeVariant;
  children: ReactNode;
}

export function HomelabStatusBadge({
  variant,
  children,
}: HomelabStatusBadgeProps) {
  return (
    <span className={`homelab-badge homelab-badge--${variant}`}>
      {children}
    </span>
  );
}
