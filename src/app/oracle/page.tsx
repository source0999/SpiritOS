// ── /oracle — same chat core; ORACLE_OLLAMA_MODEL lane when env says so (Prompt 9C) ─
import { SpiritChat } from "@/components/chat/SpiritChat";

export default function OraclePage() {
  return (
    <SpiritChat
      variant="standalone"
      runtimeSurface="oracle"
      persistence={false}
      title="Oracle // Workspace"
      subtitle="ORACLE_OLLAMA_MODEL lane · same /api/spirit · TTS still /api/tts"
    />
  );
}
