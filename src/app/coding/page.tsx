// `/coding` UI lives in CodingAgentInterface (Phase 7 clarity + proxy harness).
import CodingAgentInterface from "@/components/coding/CodingAgentInterface";

export default function CodingPage() {
  return (
    <main className="min-h-dvh bg-slate-950">
      <CodingAgentInterface layoutMode="task" />
    </main>
  );
}
