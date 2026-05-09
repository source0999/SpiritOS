"use client";

// ── HubStage - default route; eager (no dynamic) to keep first paint light ─────
import { HubStageCards } from "@/components/dashboard/HubStageCards";
import type { StageId } from "@/components/dashboard/stageTypes";

export function HubStage({ setStage }: { setStage: (s: StageId) => void }) {
  return <HubStageCards setStage={setStage} />;
}
