"use client";

// -- SpiritTrinityChatShell - dashboard v4 chrome around the real SpiritChat runtime --
import { useEffect, useState } from "react";

import { SpiritChat } from "@/components/chat/SpiritChat";
import type { SpiritChatProps } from "@/components/chat/SpiritChat";
import CodingCockpitShell from "@/components/coding/CodingCockpitShell";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";

type TrinityWorkspaceSurface = "chat" | "coding";

function ClientOnlySpiritChat(props: SpiritChatProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const id = window.setTimeout(() => setMounted(true), 0);
    return () => window.clearTimeout(id);
  }, []);

  if (!mounted) return null;

  return <SpiritChat {...props} />;
}

export default function SpiritTrinityChatShell() {
  const [surface, setSurface] = useState<TrinityWorkspaceSurface>("chat");

  return (
    <div className="spirit-trinity-chat fixed inset-0 flex overflow-hidden text-[var(--spirit-text)]">
      <div className="spirit-trinity-atmosphere" aria-hidden>
        <div className="spirit-trinity-atmosphere__base" />
        <div className="spirit-trinity-atmosphere__grid" />
        <div className="spirit-trinity-atmosphere__wash" />
        <div className="spirit-trinity-atmosphere__veil" />
      </div>

      <main className="spirit-trinity-live-chat flex min-h-0 min-w-0 flex-1 flex-col">
        {/* Chat owns presentation only; coding lifecycle stays in the canonical cockpit. */}
        <div
          className="flex shrink-0 flex-wrap gap-2 border-b border-white/[0.08] px-3 py-2"
          role="tablist"
          aria-label="Workspace surface"
        >
          <button
            type="button"
            role="tab"
            aria-selected={surface === "chat"}
            className={`border px-3 py-1.5 text-xs font-semibold tracking-wide transition-colors ${
              surface === "chat"
                ? "border-cyan-400/50 bg-cyan-500/10 text-cyan-200"
                : "border-white/15 bg-white/[0.03] text-[var(--spirit-text)]/70 hover:border-white/25 hover:text-[var(--spirit-text)]"
            }`}
            onClick={() => setSurface("chat")}
          >
            Trinity chat
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={surface === "coding"}
            className={`border px-3 py-1.5 text-xs font-semibold tracking-wide transition-colors ${
              surface === "coding"
                ? "border-cyan-400/50 bg-cyan-500/10 text-cyan-200"
                : "border-white/15 bg-white/[0.03] text-[var(--spirit-text)]/70 hover:border-white/25 hover:text-[var(--spirit-text)]"
            }`}
            onClick={() => setSurface("coding")}
          >
            Source coding agent
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-hidden">
          {surface === "chat" ? (
            <ClientOnlySpiritChat
              persistence
              variant="workspace"
              showThreadSidebar
              chromeVariant="trinity"
              title="Spirit"
              subtitle="Workspace 1.5"
              shellClassName="h-full min-h-0"
            />
          ) : (
            <div className="h-full min-h-0 overflow-auto" data-testid="trinity-canonical-cockpit">
              <CodingCockpitShell embedded />
            </div>
          )}
        </div>
      </main>

      <DashboardDemoV4FloatingNav desktopVariant="full-height" />
    </div>
  );
}
