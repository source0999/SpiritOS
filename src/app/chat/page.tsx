// ── /chat — thin route; SpiritChat owns all client state ──────────────────────
import { SpiritChat } from "@/components/chat/SpiritChat";

export default function ChatPage() {
  return (
    <SpiritChat
      variant="standalone"
      title="Neural // Spirit"
      subtitle="/api/spirit · Dark Node surface"
    />
  );
}
