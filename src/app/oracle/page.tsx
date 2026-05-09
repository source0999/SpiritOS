// ── /oracle - voice-first ephemeral Oracle lane (Prompt 10D-B) ────────────────────
// > runtimeSurface=oracle → /api/spirit + ORACLE_OLLAMA_MODEL when env set.
// > No Dexie threads here - saved Oracle sessions are a future decision.
// > STT / mic: not in this MVP (see _blueprints/oracle_voice_mvp.md).
import { OracleVoiceSurface } from "@/components/oracle/OracleVoiceSurface";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import "@/styles/dashboard-demo-v4.css";

export default function OraclePage() {
  return (
    <div className="dashboard-demo-v4-route-shell">
      <div className="dashboard-demo-v4-route-main">
        <OracleVoiceSurface />
      </div>
      <DashboardDemoV4FloatingNav />
    </div>
  );
}
