"use client";

// ── MobileThreadDrawer — left MobileSheet + thread chrome (Prompt 9E-A) ──────────
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
    <MobileSheet open={open} title="Threads" side="left" onClose={onClose}>
      {children}
    </MobileSheet>
  );
});
