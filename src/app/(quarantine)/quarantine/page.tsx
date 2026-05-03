// ── /quarantine — voice visualizer (RSC + one client visual leaf) ─────────────
// > Design language: _blueprints/design_system.md — rose seam lives in layout
import Link from "next/link";

import { QuarantineStageVisual } from "@/components/dashboard/QuarantineStageVisual";

export default function QuarantinePage() {
  return (
    <div className="min-h-[100dvh] bg-[color:var(--spirit-bg)] px-4 pb-[env(safe-area-inset-bottom)] pt-6 sm:px-8">
      <Link
        href="/"
        className="mb-6 inline-flex min-h-[44px] items-center font-mono text-xs text-[color:var(--spirit-accent-strong)] underline underline-offset-4 hover:brightness-110"
      >
        ← Dashboard
      </Link>
      <QuarantineStageVisual variant="page" />
    </div>
  );
}
