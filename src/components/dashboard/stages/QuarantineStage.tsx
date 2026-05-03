"use client";

// ── QuarantineStage — lazy boundary: heavy visual only when tab is open ───────
import { QuarantineStageVisual } from "@/components/dashboard/QuarantineStageVisual";

export default function QuarantineStage() {
  return (
    <div className="scrollbar-hide relative flex min-h-[55vh] flex-1 flex-col overflow-auto px-4 py-5 sm:p-6 lg:min-h-0">
      <QuarantineStageVisual variant="embedded" />
    </div>
  );
}
