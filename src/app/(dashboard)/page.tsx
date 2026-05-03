// ── Dashboard route (/) — RSC shell, client orchestrator is a child ───────────
// > Segment errors → `error.tsx` (same void paint as `loading.tsx`). Don’t white-screen users.
// > Blueprint: _blueprints/design_system.md | Rules: global.mdc — leaves stay client
import DashboardClient from "@/components/dashboard/DashboardClient";
import { DiagnosticsPanel } from "@/components/dashboard/DiagnosticsPanel";

export default function DashboardPage() {
  return (
    <DashboardClient
      rightRail={
        <DiagnosticsPanel className="max-h-[40dvh] border-t lg:max-h-none lg:w-[min(100%,20rem)] lg:max-w-xs lg:flex-shrink-0 lg:border-l lg:border-t-0 xl:max-w-sm" />
      }
    />
  );
}
