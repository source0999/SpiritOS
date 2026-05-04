// ── /oracle — voice-first ephemeral Oracle lane (Prompt 10D-B) ────────────────────
// > runtimeSurface=oracle → /api/spirit + ORACLE_OLLAMA_MODEL when env set.
// > No Dexie threads here — saved Oracle sessions are a future decision.
// > STT / mic: not in this MVP (see _blueprints/oracle_voice_mvp.md).
import { OracleVoiceSurface } from "@/components/oracle/OracleVoiceSurface";

export default function OraclePage() {
  return <OracleVoiceSurface />;
}
