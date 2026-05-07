"use client";

// ── MobileThreadDrawer - left MobileSheet + thread chrome (Prompt 9E-A) ──────────
import { memo, type ReactNode } from "react";

import { MobileSheet } from "@/components/chat/MobileSheet";

export type MobileThreadDrawerProps = {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
};

export const MobileThreadDrawer = memo(function MobileThreadDrawer({
  open,
  onClose,
  children,
}: MobileThreadDrawerProps) {
  return (
    <MobileSheet
      open={open}
      title="Chats"
      side="left"
      onClose={onClose}
      className="border-r border-[color:color-mix(in_oklab,var(--spirit-border)_32%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_99%,#050508)] shadow-[6px_0_36px_-14px_rgba(0,0,0,0.72)]"
    >
      {children}
    </MobileSheet>
  );
});
